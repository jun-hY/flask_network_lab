import os
import select
import struct
import threading
import time
import logging
import subprocess
from app.exceptions.custom_exceptions import PTYError

logger = logging.getLogger(__name__)

class PTYService:
    def __init__(self, container_id, socketio, room, role):
        self.container_id = container_id
        self.socketio = socketio
        self.room = room
        self.role = role
        self.running = False
        self.process = None
        self.reader_thread = None
        self.pty_fd = None
        self.master_fd = None
    
    def start(self):
        """PTY 세션을 시작합니다."""
        try:
            if os.name == 'nt':
                self._start_windows_pty()
            else:
                self._start_unix_pty()
            
            self.running = True
            self._start_reader()
            self.write("\r")
            
        except Exception as e:
            logger.error(f"PTY 시작 중 오류: {str(e)}", exc_info=True)
            self.emit_output(f"\r\nError starting shell: {str(e)}\r\n")
            self.stop()
            raise PTYError(f"PTY 시작 실패: {str(e)}")
    
    def _start_windows_pty(self):
        """Windows에서 PTY 세션을 시작합니다."""
        self.process = subprocess.Popen(
            ['docker', 'exec', '-it', self.container_id, '/bin/bash', '--login', '-i'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        self.master_fd = self.process.stdout.fileno()
        self.pty_fd = self.process.stdin.fileno()
    
    def _start_unix_pty(self):
        """Unix/Linux에서 PTY 세션을 시작합니다."""
        import pty
        import tty
        
        master_fd, slave_fd = pty.openpty()
        
        tty.setraw(master_fd)
        tty.setraw(slave_fd)
        
        self._set_pty_size(master_fd, 24, 80)
        
        self.process = subprocess.Popen(
            ['docker', 'exec', '-it', self.container_id, '/bin/bash', '--login', '-i'],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            start_new_session=True
        )
        
        os.close(slave_fd)
        self.master_fd = master_fd
        self.pty_fd = master_fd
    
    def _set_pty_size(self, fd, rows, cols):
        """PTY 크기를 설정합니다."""
        if os.name != 'nt':
            winsize = struct.pack('HHHH', rows, cols, 0, 0)
            import fcntl
            import termios
            fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
    
    def _start_reader(self):
        """출력 읽기 스레드를 시작합니다."""
        def reader():
            while self.running and self.pty_fd is not None:
                try:
                    if os.name == 'nt':
                        self._read_windows()
                    else:
                        self._read_unix()
                except Exception as e:
                    logger.error(f"읽기 스레드 오류: {str(e)}")
                    time.sleep(0.1)
        
        self.reader_thread = threading.Thread(target=reader, daemon=True)
        self.reader_thread.start()
    
    def _read_windows(self):
        """Windows에서 출력을 읽습니다."""
        try:
            data = os.read(self.master_fd, 1024)
            if data:
                self.emit_output(data.decode('utf-8', 'replace'))
        except (OSError, IOError) as e:
            if e.errno != 11:  # EAGAIN
                logger.error(f"읽기 오류: {str(e)}")
            time.sleep(0.1)
    
    def _read_unix(self):
        """Unix/Linux에서 출력을 읽습니다."""
        r, _, _ = select.select([self.pty_fd], [], [], 0.1)
        if self.pty_fd in r:
            try:
                data = os.read(self.pty_fd, 1024)
                if data:
                    self.emit_output(data.decode('utf-8', 'replace'))
            except (OSError, IOError) as e:
                if e.errno != 11:  # EAGAIN
                    logger.error(f"읽기 오류: {str(e)}")
                time.sleep(0.1)
    
    def emit_output(self, data):
        """출력을 전송합니다."""
        self.socketio.emit('pty_output', {
            'output': data,
            'role': self.role
        }, room=self.room)
    
    def write(self, data):
        """PTY에 데이터를 씁니다."""
        if not self.running or self.pty_fd is None:
            return
            
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            os.write(self.pty_fd, data)
        except Exception as e:
            logger.error(f"쓰기 오류: {str(e)}")
            self.stop()
            raise PTYError(f"PTY 쓰기 실패: {str(e)}")
    
    def resize(self, rows, cols):
        """터미널 크기를 조정합니다."""
        if not self.running or self.pty_fd is None:
            return
            
        try:
            if os.name != 'nt':
                self._set_pty_size(self.pty_fd, rows, cols)
                subprocess.run(['docker', 'exec', self.container_id, 'stty', 'rows', str(rows), 'cols', str(cols)])
        except Exception as e:
            logger.error(f"터미널 크기 조정 오류: {str(e)}")
            raise PTYError(f"터미널 크기 조정 실패: {str(e)}")
    
    def stop(self):
        """PTY 세션을 정리합니다."""
        if not self.running and not hasattr(self, 'pty_fd') and not hasattr(self, 'master_fd'):
            return
            
        self.running = False
        
        if hasattr(self, 'process') and self.process:
            try:
                if os.name == 'nt':
                    self.process.terminate()
                else:
                    os.kill(self.process.pid, 9)
            except Exception as e:
                logger.error(f"프로세스 종료 오류: {str(e)}")
        
        if hasattr(self, 'master_fd') and self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except (OSError, AttributeError) as e:
                logger.debug(f"마스터 파일 디스크립터 닫기 오류: {e}")
            self.master_fd = None
        
        if hasattr(self, 'pty_fd') and self.pty_fd is not None:
            try:
                os.close(self.pty_fd)
            except (OSError, AttributeError) as e:
                logger.debug(f"PTY 파일 디스크립터 닫기 오류: {e}")
            self.pty_fd = None
        
        if hasattr(self, 'reader_thread') and self.reader_thread and self.reader_thread.is_alive():
            try:
                self.reader_thread.join(timeout=0.5)
                if self.reader_thread.is_alive():
                    logger.warning("리더 스레드가 제시간에 종료되지 않았습니다.")
            except Exception as e:
                logger.error(f"리더 스레드 종료 대기 중 오류: {e}") 