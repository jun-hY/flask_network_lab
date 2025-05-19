from flask import Flask, render_template
from flask_socketio import SocketIO
from config import config, DOCKER_COMPOSE_DIR, LAB_CONFIG, DOCKER_CONFIG

def create_app(config_name='default'):
    """Flask 애플리케이션 팩토리 함수"""
    app = Flask(__name__)
    
    # 설정 로드
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 커스텀 설정
    app.config.update({
        'DOCKER_COMPOSE_DIR': DOCKER_COMPOSE_DIR,
        'LAB_CONFIG': LAB_CONFIG,
        'DOCKER_CONFIG': DOCKER_CONFIG
    })
    
    # 블루프린트 등록
    from controllers.main import main_bp
    from controllers.lab import lab_bp, register_socketio_handlers
    
    app.register_blueprint(main_bp)
    app.register_blueprint(lab_bp)
    
    # 에러 핸들러
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    # SocketIO 초기화
    socketio = SocketIO(app, cors_allowed_origins="*")
    app.extensions['socketio'] = socketio
    
    # SocketIO 이벤트 핸들러 등록
    register_socketio_handlers(socketio)
    
    return app, socketio

# 애플리케이션 인스턴스 생성
app, socketio = create_app()

# SocketIO 이벤트 핸들러 등록은 여기서
from controllers.lab import handle_command
socketio.on_event('command', handle_command)

@socketio.on('join_lab')
def handle_join_lab(data):
    room = data.get('lab_name')
    from flask_socketio import join_room
    join_room(room)
    print(f"Client joined room: {room}")

if __name__ == '__main__':
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
