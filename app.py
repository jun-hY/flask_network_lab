from flask import Flask, render_template, jsonify
from config import DOCKER_COMPOSE_DIR, LAB_CONFIG
from python_on_whales import DockerClient
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# 메인 페이지 라우트
@app.route('/')
def index():
    labs = []
    for lab_name, config in LAB_CONFIG.items():
        lab_info = {
            'name': lab_name,
            'description': config['description'],
            'roles': config['roles'],
        }
        
        labs.append(lab_info)
    return render_template('index.html', labs=labs)

@app.route('/up/<lab_name>', methods=['POST'])
def up(lab_name):
    if lab_name not in LAB_CONFIG:
        return jsonify({'error': '실습 항목을 찾을 수 없습니다.'}), 404
    
    config = LAB_CONFIG[lab_name]
    
    compose_file = DOCKER_COMPOSE_DIR / f"docker-compose-{lab_name}.yml"
    if not compose_file.exists():
        return jsonify({'error': 'docker-compose 파일을 찾을 수 없습니다.'}), 404
    
    docker = DockerClient(compose_files=[compose_file])
    docker.compose.up(
        detach=True
    )
    start_time = time.time()
    
    while (start_time + 60 > time.time()):
        cnt = 0
        for role in config['roles']:
            if 'spawned: \'shellinabox\'' in docker.compose.logs(role):
                cnt += 1
        if cnt == len(config['roles']):
            break
        time.sleep(.2)

    return jsonify({'message': '랩 환경이 시작되었습니다.', 'description': config['description']})

@app.route('/down/<lab_name>', methods=['DELETE'])
def down(lab_name):
    if lab_name not in LAB_CONFIG:
        return jsonify({'error': '실습 항목을 찾을 수 없습니다.'}), 404
    
    compose_file = DOCKER_COMPOSE_DIR / f"docker-compose-{lab_name}.yml"
    if not compose_file.exists():
        return jsonify({'error': 'docker-compose 파일을 찾을 수 없습니다.'}), 404
    
    docker = DockerClient(compose_files=[compose_file])
    docker.compose.down()
    
    return jsonify({'message': '랩 환경이 종료되었습니다.'})

if __name__ == '__main__':
    print('서버 시작: http://localhost:5000')
    app.run(debug=True)
