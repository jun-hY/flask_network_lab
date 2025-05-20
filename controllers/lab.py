import os
import json
import select
import socket
import struct
import fcntl
import termios
import tty
import pty
import subprocess
from datetime import datetime
from flask import Blueprint, current_app, render_template, request, redirect, url_for, jsonify
from flask_socketio import emit, join_room, leave_room
from python_on_whales import DockerClient
from python_on_whales.exceptions import NoSuchContainer, DockerException
import threading
import time
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 블루프린트 생성
lab_bp = Blueprint('lab', __name__, template_folder='../../templates')

# 전역 변수 선언
global active_sessions, active_ptys, running_threads, global_docker

# 실행 중인 세션 및 스레드 추적
active_sessions = {}  # 활성 세션 정보
active_ptys = {}  # 활성 PTY 세션
running_threads = {}  # 실행 중인 로그 스트리밍 스레드: {role: thread}

# 전역 Docker 클라이언트
global_docker = DockerClient()

class DockerPTY:
    """Docker 컨테이너와 상호작용하는 PTY 핸들러 (python-on-whales 버전)"""
    
    def __init__(self, container_id, socketio, room, role):
        self.container_id = container_id
        self.socketio = socketio
        self.room = room
        self.role = role
        self.running = False
        self.process = None
        self.reader_thread = None
        self.docker = DockerClient(compose_files=[])
        self.pty_fd = None
        self.master_fd = None
    
    def start(self):
        """PTY 세션 시작"""
        try:
            # PTY 마스터/슬레이브 페어 생성
            import pty
            master_fd, slave_fd = pty.openpty()
            
            # 터미널 속성 설정
            import termios
            import tty
            
            # 원시 모드로 설정
            tty.setraw(master_fd)
            tty.setraw(slave_fd)
            
            # 터미널 크기 설정 (기본값: 80x24)
            self._set_pty_size(master_fd, 24, 80)
            
            # Docker exec를 사용하여 PTY 세션 시작
            self.process = self.docker.container.execute(
                self.container_id,
                ["/bin/bash", "--login", "-i"],
                env={"TERM": "xterm-256color"},
                tty=True,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                detach=True
            )
            
            # 슬레이브는 이제 사용하지 않으므로 닫기
            os.close(slave_fd)
            
            # 마스터 FD 저장
            self.master_fd = master_fd
            self.pty_fd = master_fd
            
            # 논블로킹 모드 설정
            import fcntl
            flags = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
            fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            
            self.running = True
            self._start_reader()
            
            # 초기 프롬프트 표시를 위해 빈 명령어 전송
            self.write("\r")
            
        except Exception as e:
            logger.error(f"PTY 시작 중 오류: {str(e)}", exc_info=True)
            self.emit_output(f"\r\nError starting shell: {str(e)}\r\n")
            self.stop()
    
    def _start_reader(self):
        """출력 읽기 스레드 시작"""
        def reader():
            while self.running and self.pty_fd is not None:
                try:
                    r, _, _ = select.select([self.pty_fd], [], [], 0.1)
                    if self.pty_fd in r:
                        try:
                            data = os.read(self.pty_fd, 1024)
                            if data:
                                self.emit_output(data.decode('utf-8', 'replace'))
                        except (OSError, IOError) as e:
                            if e.errno != 11:  # EAGAIN: 리소스 일시적으로 사용 불가
                                logger.error(f"읽기 오류: {str(e)}")
                                time.sleep(0.1)
                except Exception as e:
                    logger.error(f"읽기 스레드 오류: {str(e)}")
                    time.sleep(0.1)
        
        self.reader_thread = threading.Thread(target=reader, daemon=True)
        self.reader_thread.start()
    
    def emit_output(self, data):
        """출력 전송"""
        self.socketio.emit('pty_output', {
            'output': data,
            'role': self.role
        }, room=self.room)
    
    def write(self, data):
        """PTY에 데이터 쓰기"""
        if not self.running or self.pty_fd is None:
            return
            
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            os.write(self.pty_fd, data)
        except Exception as e:
            logger.error(f"쓰기 오류: {str(e)}")
            self.stop()
    
    def resize(self, rows, cols):
        """터미널 크기 조정"""
        if not self.running or self.pty_fd is None:
            return
            
        try:
            # 터미널 크기 설정
            winsize = struct.pack('HHHH', rows, cols, 0, 0)
            fcntl.ioctl(self.pty_fd, termios.TIOCSWINSZ, winsize)
            
            # Docker 컨테이너의 pty 크기 조정
            if hasattr(self, 'process') and self.process:
                self.docker.container.execute(
                    self.container_id,
                    ["stty", "rows", str(rows), "cols", str(cols)]
                )
                
        except Exception as e:
            logger.error(f"터미널 크기 조정 오류: {str(e)}")
    
    def _set_pty_size(self, fd, rows, cols):
        """PTY 크기 설정"""
        import fcntl
        import struct
        import termios
        
        # 터미널 크기 설정
        winsize = struct.pack('HHHH', rows, cols, 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
        
        # Docker 컨테이너의 pty 크기 조정
        if hasattr(self, 'process') and self.process:
            try:
                self.docker.container.execute(
                    self.container_id,
                    ["stty", "rows", str(rows), "cols", str(cols)],
                    tty=True
                )
            except Exception as e:
                logger.error(f"터미널 크기 조정 중 오류: {e}")
    
    def resize(self, rows, cols):
        """터미널 크기 조정"""
        if not self.running or not hasattr(self, 'master_fd') or self.master_fd is None:
            return
        
        try:
            self._set_pty_size(self.master_fd, rows, cols)
        except Exception as e:
            logger.error(f"터미널 크기 조정 오류: {e}")
    
    def stop(self):
        """PTY 세션 정리"""
        if not self.running and not hasattr(self, 'pty_fd') and not hasattr(self, 'master_fd'):
            return
            
        self.running = False
        
        # 파일 디스크립터 정리
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
        
        # 리더 스레드 정리
        if hasattr(self, 'reader_thread') and self.reader_thread and self.reader_thread.is_alive():
            try:
                self.reader_thread.join(timeout=0.5)
                if self.reader_thread.is_alive():
                    logger.warning("리더 스레드가 제시간에 종료되지 않았습니다.")
            except Exception as e:
                logger.error(f"리더 스레드 종료 대기 중 오류: {e}")
        
        # Docker 컨테이너 정리
        if hasattr(self, 'process') and self.process:
            try:
                self.process.kill()
                self.process.remove(force=True)
            except Exception as e:
                logger.error(f"Docker 컨테이너 정리 중 오류: {e}")
            self.process = None
        
        logger.debug("PTY 세션이 정상적으로 정리되었습니다.")

def get_lab_config(lab_name):
    """랩 환경 설정을 가져옵니다."""
    return current_app.config['LAB_CONFIG'].get(lab_name, {})

def get_container_name(role, lab_name):
    """컨테이너 이름을 생성합니다."""
    docker_config = current_app.config['DOCKER_CONFIG']
    return docker_config.get('container_names', {}).get(role, f"{role}-{lab_name}")

def emit_socketio(event, data, room=None, **kwargs):
    """SocketIO 이벤트를 안전하게 발생시킵니다."""
    socketio = current_app.extensions.get('socketio')
    if socketio:
        socketio.emit(event, data, room=room or request.sid, **kwargs)

def handle_pty_input(sid, data):
    """PTY 입력 처리"""
    session = active_sessions.get(sid)
    if not session:
        return
    
    lab_name = data.get('lab_name')
    role = data.get('role')
    
    if not all([lab_name, role]):
        logger.error("Missing lab_name or role in pty_input")
        return
    
    pty_session = active_ptys.get(session['pty_id'])
    if not pty_session:
        return
    
    if 'input' in data:
        pty_session.write(data['input'])
    
    if 'resize' in data:
        rows = data['resize'].get('rows', 24)
        cols = data['resize'].get('cols', 80)
        pty_session.resize(rows, cols)

@lab_bp.route("/lab/<lab_name>")
def lab(lab_name):
    """랩 환경을 표시합니다."""
    lab_config = get_lab_config(lab_name)
    if not lab_config:
        return "Lab not found", 404
    
    lab_data = {
        "name": lab_name,
        "roles": lab_config.get("roles", []),
        "containers": {role: {} for role in lab_config.get("roles", [])},
        "description": lab_config.get("description", "")
    }
    
    return render_template(
        "lab.html",
        lab=lab_data,
        lab_name=lab_name,
        lab_config=lab_config,
        roles=lab_config.get('roles', []),
        description=lab_config.get('description', '')
    )

@lab_bp.route("/lab/<lab_name>/start", methods=["POST"])
def start_lab(lab_name):
    """랩 환경을 시작합니다."""
    # Docker Compose 파일 경로 구성
    compose_path = os.path.join(
        current_app.root_path,  # 애플리케이션 루트 디렉토리
        'Docker',  # Docker 디렉토리
        f"docker-compose-{lab_name}.yml"
    )
    
    # 경로가 존재하는지 확인
    if not os.path.exists(compose_path):
        logger.error(f"Docker Compose 파일을 찾을 수 없습니다: {compose_path}")
        return jsonify({"error": "Docker Compose 파일을 찾을 수 없습니다."}), 404
    
    # Docker Compose로 컨테이너 시작
    try:
        lab_docker = DockerClient(compose_files=[compose_path])
        lab_docker.compose.up(detach=True, build=False)
        logger.info(f"{lab_name} 랩 환경을 시작했습니다.")
    except Exception as e:
        logger.error(f"Docker Compose 실행 중 오류 발생: {str(e)}")
        return jsonify({"error": f"Docker Compose 실행 중 오류 발생: {str(e)}"}), 500
    
    # 각 역할에 대한 로그 스트리밍 시작
    roles = get_lab_config(lab_name).get('roles', [])
    
    for role in roles:
        container_name = get_container_name(role, lab_name)
        
        def start_log_stream(role, container_name, lab_name, app):
            with app.app_context():
                try:
                    try:
                        # 초기 로그 가져오기 (마지막 50줄)
                        try:
                            # python-on-whales를 사용하여 로그 가져오기
                            container = lab_docker.container.inspect(container_name)
                            logs = lab_docker.container.logs(container_name, tail=50, follow=False)
                            
                            if logs:
                                log_str = logs.decode('utf-8', errors='replace') if isinstance(logs, bytes) else str(logs)
                                emit_socketio(
                                    'container_log',
                                    {'role': role, 'message': log_str},
                                    room=f"{lab_name}_{role}"
                                )
                        except Exception as e:
                            logger.error(f"컨테이너 {container_name}의 초기 로그를 가져오는 중 오류 발생: {e}")
                        
                        # 새로운 로그 스트리밍
                        try:
                            # python-on-whales를 사용하여 로그 스트리밍
                            # subprocess를 사용하여 로그 스트리밍 (python-on-whales의 제한사항으로 인해)
                            process = subprocess.Popen(
                                ['docker', 'logs', '--tail', '0', '-f', container_name],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True,
                                encoding='utf-8',
                                errors='replace',
                                bufsize=1,
                                universal_newlines=True
                            )
                            
                            # 프로세스가 종료될 때까지 로그를 계속 읽음
                            while True:
                                output = process.stdout.readline()
                                if output == '' and process.poll() is not None:
                                    break
                                if output:
                                    emit_socketio(
                                        'container_log',
                                        {'role': role, 'message': output},
                                        room=f"{lab_name}_{role}"
                                    )
                            
                            process.wait()
                            
                        except Exception as e:
                            logger.error(f"컨테이너 {container_name}의 로그 스트림 처리 중 오류: {e}")
                            try:
                                if process:
                                    process.terminate()
                            except:
                                pass
                            
                    except Exception as e:
                        logger.error(f"Error accessing container {container_name}: {e}")
                        
                except Exception as e:
                    logger.error(f"Error setting up log streaming for {container_name}: {e}")
        
        thread = threading.Thread(
            target=start_log_stream,
            args=(role, container_name, lab_name, current_app._get_current_object()),
            daemon=True
        )
        thread.start()
        running_threads[role] = thread
    
    return redirect(url_for('lab.lab', lab_name=lab_name))

@lab_bp.route("/lab/<lab_name>/stop", methods=["POST"])
def stop_lab(lab_name):
    """랩 환경을 중지합니다."""
    # Docker Compose 파일 경로 구성
    compose_path = os.path.join(
        current_app.root_path,  # 애플리케이션 루트 디렉토리
        'Docker',  # Docker 디렉토리
        f"docker-compose-{lab_name}.yml"
    )
    
    # 경로가 존재하는지 확인
    if not os.path.exists(compose_path):
        logger.error(f"Docker Compose 파일을 찾을 수 없습니다: {compose_path}")
        return jsonify({"error": "Docker Compose 파일을 찾을 수 없습니다."}), 404
    
    lab_docker = None
    try:
        try:
            # Docker Compose로 컨테이너 중지
            lab_docker = DockerClient(compose_files=[compose_path])
            
            # docker-compose down 실행
            lab_docker.compose.down(
                timeout=30,
            )
            logger.info(f"{lab_name} 랩 환경을 중지했습니다.")
            
        except Exception as e:
            logger.warning(f"Docker Compose 중지 중 경고: {e}")
            
            # 강제로 남은 컨테이너 정리 시도
            if lab_docker is not None:
                try:
                    # python-on-whales 방식으로 컨테이너 필터링
                    containers = lab_docker.ps(filters={"label": f"com.docker.compose.project={lab_name}"})
                    for container in containers:
                        try:
                            if container.state.running:
                                container.stop(timeout=5)
                            container.remove(force=True)
                            logger.debug(f"컨테이너 {container.id} 제거 완료")
                        except Exception as ce:
                            logger.warning(f"컨테이너 {container.id} 제거 실패: {ce}", exc_info=True)
                except Exception as e:
                    logger.error(f"컨테이너 정리 중 오류: {e}", exc_info=True)
        
        # 실행 중인 스레드 정리
        for role, thread in list(running_threads.items()):
            if thread.is_alive():
                thread.join(timeout=1)
                logger.debug(f"{role} 로그 스트리밍 스레드 종료")
        running_threads.clear()
        
        # 네트워크 정리 (lab_docker이 초기화된 경우에만 시도)
        if lab_docker is not None:
            try:
                # python-on-whales 방식으로 네트워크 필터링
                networks = lab_docker.network.list(filters={"label": f"com.docker.compose.project={lab_name}"})
                for network in networks:
                    try:
                        network.remove()
                        logger.debug(f"네트워크 {network.id} 제거 완료")
                    except Exception as ne:
                        logger.error(f"네트워크 {network.id} 정리 중 오류: {ne}", exc_info=True)
            except Exception as ne:
                logger.error(f"네트워크 정리 중 오류: {ne}", exc_info=True)
        
        # 세션 정리
        for sid, session in list(active_sessions.items()):
            if session.get('lab_name') == lab_name:
                cleanup_session(sid)
        
        # 성공 시 랩 페이지로 리다이렉트
        return redirect(url_for('lab.lab', lab_name=lab_name))
        
    except Exception as e:
        logger.error(f"랩 환경 중지 중 오류 발생: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"랩 환경 중지 중 오류가 발생했습니다: {str(e)}"
        }), 500
    finally:
        # Docker 클라이언트 정리 (python-on-whales는 close() 메서드가 없으므로 참조만 제거)
        if lab_docker is not None:
            try:
                logger.debug("Docker 클라이언트 참조 제거")
                del lab_docker
            except Exception as e:
                logger.warning(f"Docker 클라이언트 정리 중 오류: {e}", exc_info=True)

def create_pty_session(sid, container_name, role, lab_name):
    """새로운 PTY 세션 생성"""
    try:
        # 기존 세션 정리
        if sid in active_sessions:
            cleanup_session(sid)
        
        # Docker 클라이언트 생성 (전역 변수 사용)
        docker_client = DockerClient(compose_files=[])
        
        # 컨테이너 존재 여부 확인
        try:
            # 컨테이너 이름이 정규화되지 않을 수 있으므로, 존재하는 컨테이너 목록에서 찾기
            containers = docker_client.ps(all=True)
            container = None
            
            # 정확한 이름 또는 ID로 컨테이너 찾기
            for c in containers:
                if container_name in c.id or container_name in c.name:
                    container = c
                    break
            
            if not container:
                logger.error(f"컨테이너를 찾을 수 없습니다: {container_name}")
                return False, f"컨테이너를 찾을 수 없습니다: {container_name}"
                
            # 컨테이너가 실행 중이 아니라면 시작
            if not container.state.running:
                logger.warning(f"컨테이너 {container_name}이(가) 실행 중이지 않습니다. 시작 중...")
                container.start()
                
        except Exception as e:
            logger.error(f"컨테이너 {container_name} 확인/시작 중 오류: {e}", exc_info=True)
            return False, f"컨테이너를 찾을 수 없거나 시작할 수 없습니다: {container_name}"
        
        # PTY 세션 생성 및 시작
        pty_session = DockerPTY(container_name, current_app.extensions['socketio'], sid, role)
        try:
            pty_session.start()
            
            # 세션 정보 저장
            pty_id = f"{sid}_{int(time.time())}"
            active_sessions[sid] = {
                'pty_id': pty_id,
                'container_name': container_name,
                'role': role,
                'lab_name': lab_name,
                'created_at': datetime.now().isoformat(),
                'docker_client': docker_client  # Docker 클라이언트 참조 유지
            }
            active_ptys[pty_id] = pty_session
            
            logger.info(f"PTY 세션 생성 성공: 컨테이너={container_name}, 세션ID={pty_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"PTY 세션 시작 중 오류: {e}", exc_info=True)
            try:
                pty_session.stop()
            except:
                pass
            return False, f"PTY 세션을 시작할 수 없습니다: {str(e)}"
        
    except Exception as e:
        logger.error(f"PTY 세션 생성 실패: {str(e)}", exc_info=True)
        try:
            docker_client.close()
        except:
            pass
        return False, f"PTY 세션을 생성할 수 없습니다: {str(e)}"

def cleanup_session(sid):
    """세션 정리"""
    if sid in active_sessions:
        session = active_sessions[sid]
        pty_id = session.get('pty_id')
        docker_client = session.get('docker_client')
        
        # PTY 세션 정리
        if pty_id and pty_id in active_ptys:
            try:
                active_ptys[pty_id].stop()
                logger.debug(f"PTY 세션 종료: {pty_id}")
            except Exception as e:
                logger.error(f"PTY 세션 정리 중 오류: {e}", exc_info=True)
            finally:
                if pty_id in active_ptys:
                    del active_ptys[pty_id]
        
        # Docker 클라이언트 정리 (python-on-whales는 close() 메서드가 없으므로 pass)
        # 참조만 제거하고 가비지 컬렉터가 처리하도록 함
        if docker_client:
            logger.debug("Docker 클라이언트 참조 제거")
            del docker_client
        
        # 세션 정보 제거
        del active_sessions[sid]
        logger.info(f"세션 정리 완료: {sid}")

def handle_command(data):
    """커맨드 실행을 처리합니다 (레거시 호환용)."""
    lab_name = data.get('lab_name')
    role = data.get('role')
    command = data.get('command')
    
    if not all([lab_name, role, command]):
        emit_socketio('shell_output', {'error': '필수 파라미터 누락'})
        return
    
    try:
        container_name = get_container_name(role, lab_name)
        
        # PTY 세션이 없으면 생성
        sid = request.sid
        if sid not in active_sessions:
            success, error = create_pty_session(sid, container_name, role, lab_name)
            if not success:
                raise Exception(f"PTY 세션 생성 실패: {error}")
        
        # 세션 및 스레드 초기화 (테스트용)
        active_sessions.clear()
        active_ptys.clear()
        running_threads.clear()
            
        # 명령어 실행
        pty_session = active_ptys.get(active_sessions[sid]['pty_id'])
        if pty_session:
            pty_session.write(command + '\n')
            
    except Exception as e:
        emit_socketio('shell_output', {
            "role": role,
            "output": f"오류 발생: {str(e)}\n",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }, room=lab_name)

# SocketIO 이벤트 핸들러 등록
def register_socketio_handlers(socketio):
    @socketio.on('connect')
    def handle_connect():
        logger.info(f"Client connected: {request.sid}")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f"Client disconnected: {request.sid}")
        cleanup_session(request.sid)
    
    @socketio.on('command')
    def handle_command_event(data):
        handle_command(data)
    
    @socketio.on('pty_input')
    def handle_pty_input_event(data):
        handle_pty_input(request.sid, data)
    
    @socketio.on('start_pty')
    def handle_start_pty(data):
        lab_name = data.get('lab_name')
        role = data.get('role')
        
        if not all([lab_name, role]):
            return {'status': 'error', 'message': 'Missing required parameters'}
        
        try:
            container_name = get_container_name(role, lab_name)
            success, error = create_pty_session(request.sid, container_name, role, lab_name)
            
            if success:
                return {'status': 'success'}
            else:
                return {'status': 'error', 'message': error}
                
        except Exception as e:
            logger.error(f"PTY 시작 실패: {str(e)}")
            return {'status': 'error', 'message': str(e)}
