from flask import Blueprint, render_template, request, redirect, url_for, current_app
from python_on_whales import DockerClient
from python_on_whales.exceptions import NoSuchContainer
import os
import threading
import queue

lab_bp = Blueprint('lab', __name__)
running_threads = {}

# 전역 Docker client
global_docker = DockerClient()

# 전역 app 참조
app = None

DOCKER_COMPOSE_DIR = os.path.join(os.getcwd(), 'Docker')

@lab_bp.record_once
def on_load(state):
    global app
    app = state.app

@lab_bp.route("/lab/<lab_name>")
def lab_page(lab_name):
    lab = {
        "name": lab_name,
        "containers": {
            "attacker": {},
            "hostA": {},
            "hostB": {}
        }
    }
    return render_template("lab.html", lab=lab)

@lab_bp.route("/lab/<lab_name>/start", methods=["POST"])
def start_lab(lab_name):
    compose_file = os.path.join(DOCKER_COMPOSE_DIR, f"docker-compose-{lab_name}.yml")
    lab_docker = DockerClient(compose_files=[compose_file])
    lab_docker.compose.up(detach=True)

    roles = ['attacker', 'hostA', 'hostB']
    for role in roles:
        container_name = get_container_name(role, lab_name)
        thread = threading.Thread(
            target=stream_container_logs,
            args=(role, container_name, lab_name),
            daemon=True
        )
        thread.start()
        running_threads[role] = thread

    return redirect(url_for('lab.lab_page', lab_name=lab_name))

@lab_bp.route("/lab/<lab_name>/stop", methods=["POST"])
def stop_lab(lab_name):
    compose_file = os.path.join(DOCKER_COMPOSE_DIR, f"docker-compose-{lab_name}.yml")
    lab_docker = DockerClient(compose_files=[compose_file])
    lab_docker.compose.down()
    
    # 실행 중인 스레드 정리
    for thread in running_threads.values():
        if thread.is_alive():
            thread.join(timeout=1)
    running_threads.clear()
    
    return redirect(url_for('lab.lab_page', lab_name=lab_name))

def get_container_name(role, lab_name):
    if role == "attacker":
        return "seed-attacker"
    elif role == "hostA":
        return "hostA-10.9.0.5"
    elif role == "hostB":
        return "hostB-10.9.0.6"
    else:
        return f"{lab_name}_{role}_1"

def stream_container_logs(role, container_name, lab_name):
    try:
        # Flask 애플리케이션 컨텍스트 설정
        with app.app_context():
            # 컨테이너 상태 확인
            container = global_docker.container.inspect(container_name)
            if container.state.status != "running":
                app.extensions['socketio'].emit(
                    'shell_output', 
                    {"role": role, "output": f"[{container_name}] is not running.\n"},
                    to=lab_name
                )
                return

            # 로그 스트리밍
            for line in global_docker.container.logs(
                container_name, 
                follow=True, 
                stream=True,
                timestamps=True
            ):
                try:
                    # 타임스탬프 처리
                    timestamp, message = line[1].decode('utf-8').split(' ', 1)
                    # YYYY-MM-DD HH:MM:SS 형식으로 변환
                    formatted_time = timestamp.split('.')[0].replace('T', ' ')
                    # clear 명령어 감지
                    if '\x1b[H\x1b[2J\x1b[3J' in message:
                        # 소켓.IO를 통해 클라이언트로 clear 명령 전송
                        app.extensions['socketio'].emit(
                            'shell_output',
                            {"role": role, "output": message.replace('\x1b[H\x1b[2J\x1b[3J', ''), "timestamp": formatted_time, "clear": True},
                            to=lab_name
                        )
                    else:
                        # 소켓.IO를 통해 클라이언트로 전송
                        app.extensions['socketio'].emit(
                            'shell_output',
                            {"role": role, "output": message, "timestamp": formatted_time},
                            to=lab_name
                        )
                except Exception as e:
                    app.extensions['socketio'].emit(
                        'error',
                        {"role": role, "error": f"Error processing log line: {str(e)}"},
                        to=lab_name
                    )

    except NoSuchContainer:
        app.extensions['socketio'].emit(
            'shell_output',
            {"role": role, "output": f"[{container_name}] not found.\n"},
            to=lab_name
        )
    except Exception as e:
        app.extensions['socketio'].emit(
            'error',
            {"role": role, "error": f"Unexpected error: {str(e)}"},
            to=lab_name
        )
