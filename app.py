"""
Flask Network Lab 메인 실행 파일
"""

import os
from flask import Flask
from flask_socketio import SocketIO
from app.config.settings import Settings
from app.utils.logging import setup_logging
from app.services.docker_service import DockerService
from app.services.session_service import SessionService
from app.exceptions.custom_exceptions import ConfigError

def create_app():
    """Flask 애플리케이션을 생성합니다."""
    app = Flask(__name__)
    
    # 설정 로드
    settings = Settings()
    app.config.from_object(settings)
    
    # 로깅 설정
    logger = setup_logging(app)
    
    # 서비스 초기화
    docker_service = DockerService()
    session_service = SessionService()
    
    # 서비스를 앱 컨텍스트에 저장
    app.docker_service = docker_service
    app.session_service = session_service
    
    # SocketIO 초기화
    socketio = SocketIO(app, cors_allowed_origins="*")
    app.socketio = socketio
    
    # 블루프린트 등록
    from app.controllers.lab import lab_bp
    app.register_blueprint(lab_bp)
    
    # SocketIO 이벤트 핸들러 등록
    from app.controllers.lab import register_socketio_handlers
    register_socketio_handlers(socketio)
    
    return app, socketio

def main():
    """애플리케이션을 실행합니다."""
    app, socketio = create_app()
    
    try:
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=app.config.get('DEBUG', False),
            use_reloader=False
        )
    except Exception as e:
        app.logger.error(f"애플리케이션 실행 중 오류 발생: {str(e)}")
        raise

if __name__ == '__main__':
    main()
