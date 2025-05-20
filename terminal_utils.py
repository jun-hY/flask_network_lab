import os
import pty
import select
import fcntl
import tty
import termios
import subprocess
import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

class TerminalProcess:
    """터미널 프로세스를 관리하는 클래스"""
    
    def __init__(self, command: str, env: Optional[Dict[str, str]] = None):
        self.command = command
        self.env = env or {}
        self.pid: Optional[int] = None
        self.fd: Optional[int] = None
        self.running: bool = False
        
    def start(self) -> bool:
        """터미널 프로세스 시작"""
        try:
            # 환경 변수 설정
            env = os.environ.copy()
            env.update(self.env)
            
            # PTY 생성
            self.pid, self.fd = pty.fork()
            
            if self.pid == 0:  # 자식 프로세스
                # 터미널 설정
                tty.setraw(0)
                
                # 명령어 실행
                os.execvpe(self.command[0], self.command, env)
            else:  # 부모 프로세스
                # 논블로킹 모드 설정
                flags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
                fcntl.fcntl(self.fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
                
                self.running = True
                return True
                
        except Exception as e:
            logger.error(f"터미널 프로세스 시작 실패: {str(e)}")
            self.stop()
            return False
    
    def read(self, size: int = 1024) -> str:
        """터미널 출력 읽기"""
        if not self.running or not self.fd:
            return ""
            
        try:
            r, _, _ = select.select([self.fd], [], [], 0.1)
            if self.fd in r:
                data = os.read(self.fd, size)
                return data.decode('utf-8', 'replace')
        except (OSError, IOError) as e:
            if e.errno != 5:  # EIO (IOError: [Errno 5] Input/output error)
                logger.error(f"터미널 읽기 오류: {str(e)}")
        except Exception as e:
            logger.error(f"터미널 읽기 오류: {str(e)}")
            
        return ""
    
    def write(self, data: str) -> None:
        """터미널에 입력 쓰기"""
        if not self.running or not self.fd:
            return
            
        try:
            os.write(self.fd, data.encode('utf-8'))
        except Exception as e:
            logger.error(f"터미널 쓰기 오류: {str(e)}")
            self.stop()
    
    def resize(self, rows: int, cols: int) -> None:
        """터미널 크기 조정"""
        if not self.running or not self.fd:
            return
            
        try:
            # 터미널 크기 설정
            size = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, size)
        except Exception as e:
            logger.error(f"터미널 크기 조정 오류: {str(e)}")
    
    def stop(self) -> None:
        """터미널 프로세스 정지"""
        if not self.running:
            return
            
        self.running = False
        
        try:
            if self.pid and self.pid != 0:
                try:
                    os.kill(self.pid, 15)  # SIGTERM
                except ProcessLookupError:
                    pass
                
            if self.fd:
                os.close(self.fd)
                
        except Exception as e:
            logger.error(f"터미널 정리 중 오류: {str(e)}")
        finally:
            self.pid = None
            self.fd = None
