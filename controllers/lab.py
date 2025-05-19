import os
from datetime import datetime
from flask import Blueprint, current_app, render_template, request, redirect, url_for
from flask_socketio import emit
from python_on_whales import DockerClient
from python_on_whales.exceptions import NoSuchContainer
import threading
import time

# 블루프린트 생성
lab_bp = Blueprint('lab', __name__, template_folder='../../templates')

# 실행 중인 스레드 추적
running_threads = {}

# 전역 Docker 클라이언트
global_docker = DockerClient()

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

def stream_container_logs(role, container_name, lab_name, app):
    """컨테이너 로그를 스트리밍합니다."""
    with app.app_context():
        while True:
            try:
                # 컨테이너 상태 확인
                try:
                    container = global_docker.container.inspect(container_name)
                    if container.state.status != "running":
                        emit_socketio('shell_output', 
                                    {"role": role, "output": f"[{container_name}] is not running.\n"}, 
                                    room=lab_name)
                        time.sleep(1)
                        continue

                    # 로그 스트림 시작
                    # logs = container.logs(stream=True)
                    logs = ''
                    emit_socketio('shell_output', 
                                {"role": role, "output": logs}, 
                                room=lab_name)
                    
                except Exception as e:
                    if "No such container" in str(e):
                        emit_socketio('shell_output',
                                    {"role": role, "output": f"[{container_name}] not found. Waiting...\n"},
                                    room=lab_name)
                    else:
                        current_app.logger.error(f"Container error: {str(e)}")
                        emit_socketio('shell_output',
                                    {"role": role, "output": f"컨테이너 오류: {str(e)}\n"},
                                    room=lab_name)
                    time.sleep(5)
                
            except Exception as e:
                current_app.logger.error(f"Unexpected error in log streaming: {str(e)}")
                time.sleep(5)  # 오류 발생 시 잠시 대기 후 재시도

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
    compose_path = os.path.join(
        current_app.config['DOCKER_COMPOSE_DIR'],
        f"docker-compose-{lab_name}.yml"
    )
    
    # Docker Compose로 컨테이너 시작
    lab_docker = DockerClient(compose_files=[compose_path])
    lab_docker.compose.up(detach=True)
    
    # 각 역할에 대한 로그 스트리밍 시작
    roles = get_lab_config(lab_name).get('roles', [])
    for role in roles:
        container_name = get_container_name(role, lab_name)
        thread = threading.Thread(
            target=stream_container_logs,
            args=(role, container_name, lab_name, current_app._get_current_object()),
            daemon=True
        )
        thread.start()
        running_threads[role] = thread
    
    return redirect(url_for('lab.lab', lab_name=lab_name))

@lab_bp.route("/lab/<lab_name>/stop", methods=["POST"])
def stop_lab(lab_name):
    """랩 환경을 중지합니다."""
    compose_path = os.path.join(
        current_app.config['DOCKER_COMPOSE_DIR'],
        f"docker-compose-{lab_name}.yml"
    )
    
    # Docker Compose로 컨테이너 중지
    lab_docker = DockerClient(compose_files=[compose_path])
    lab_docker.compose.down()
    
    # 실행 중인 스레드 정리
    for thread in running_threads.values():
        if thread.is_alive():
            thread.join(timeout=1)
    running_threads.clear()
    
    return redirect(url_for('lab.lab', lab_name=lab_name))

def handle_command(data):
    """커맨드 실행을 처리합니다."""
    lab_name = data.get('lab_name')
    role = data.get('role')
    command = data.get('command')
    
    if not all([lab_name, role, command]):
        emit_socketio('shell_output', {'error': '필수 파라미터 누락'})
        return
    
    try:
        container_name = get_container_name(role, lab_name)
        compose_path = os.path.join(
            current_app.config['DOCKER_COMPOSE_DIR'],
            f"docker-compose-{lab_name}.yml"
        )
        
        docker = DockerClient(compose_files=[compose_path])
        exec_result = docker.container.execute(container_name, ["sh", "-c", command])

        emit_socketio('shell_output', {
            "role": role,
            "output": f"$ {command}\n{exec_result}\n",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }, room=lab_name)
        
    except NoSuchContainer:
        emit_socketio('shell_output', {
            "role": role,
            "output": f"{container_name} 컨테이너를 찾을 수 없습니다\n",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }, room=lab_name)
    except Exception as e:
        emit_socketio('shell_output', {
            "role": role,
            "output": f"오류 발생: {str(e)}\n",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }, room=lab_name)

# SocketIO 이벤트 핸들러 등록
def register_socketio_handlers(socketio):
    @socketio.on('command')
    def handle_command_event(data):
        handle_command(data)
