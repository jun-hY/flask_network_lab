from flask import Blueprint, render_template, request, redirect, url_for
from flask_socketio import emit
from threading import Thread
import os
import time
from python_on_whales import DockerClient, docker as global_docker
from python_on_whales.exceptions import NoSuchContainer

lab_bp = Blueprint('lab', __name__)
running_threads = {}

# Docker Compose 파일이 저장된 디렉토리 (flask_network_lab/Docker)
DOCKER_COMPOSE_DIR = os.path.join(os.getcwd(), 'Docker')

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
    local_docker = DockerClient(compose_files=[compose_file])

    local_docker.compose.up(detach=True)

    time.sleep(2)  # 컨테이너가 완전히 올라올 때까지 대기

    roles = ['attacker', 'hostA', 'hostB']
    for role in roles:
        time.sleep(.3)
        container_name = get_container_name(role, lab_name)
        thread = Thread(target=stream_container_logs, args=(role, container_name, lab_name), daemon=True)
        thread.start()
        running_threads[role] = thread

    return redirect(url_for('lab.lab_page', lab_name=lab_name))

@lab_bp.route("/lab/<lab_name>/stop", methods=["POST"])
def stop_lab(lab_name):
    compose_file = os.path.join(DOCKER_COMPOSE_DIR, f"docker-compose-{lab_name}.yml")
    local_docker = DockerClient(compose_files=[compose_file])

    local_docker.compose.down()
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
    from app import socketio
    try:
        container = global_docker.container.inspect(container_name)
        print(f'[name: {container_name}]')
        if container.state.status != "running":
            socketio.emit('shell_output', {"role": role, "output": f"[{container_name}] is not running.\n"}, to=lab_name)
            return

        for line in global_docker.container.logs(container_name, follow=True, stream=True):
            print(f"[{role}:{container_name}] {line} [to={lab_name}]")  # 디버깅용
            socketio.emit('shell_output', {"role": role, "output": line})

    except NoSuchContainer:
        print(f'[{container_name} not found]')
        socketio.emit('shell_output', {"role": role, "output": f"[{container_name}] not found.\n"}, to=lab_name)
    except Exception as e:
        print(f'[{e}]')
        socketio.emit('shell_output', {"role": role, "output": f"Error: {e}\n"}, to=lab_name)
