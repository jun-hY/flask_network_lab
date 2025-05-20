"""
Flask Network Lab 애플리케이션 패키지
"""

import os
from flask import Flask, render_template, redirect, url_for
from flask_socketio import SocketIO
from app.config.settings import Settings
from app.utils.logging import setup_logging
from app.services.docker_service import DockerService
from app.services.session_service import SessionService
from app.exceptions.custom_exceptions import DockerError

def create_app():
    """Flask 애플리케이션을 생성합니다."""
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # 설정 로드
    settings = Settings()
    app.config.from_object(settings)
    
    # 로깅 설정
    logger = setup_logging(app)
    
    # 서비스 초기화
    try:
        docker_service = DockerService()
        app.docker_service = docker_service
        app.docker_available = True
    except DockerError as e:
        logger.warning(f"Docker 서비스 초기화 실패: {str(e)}")
        app.docker_service = None
        app.docker_available = False
    
    session_service = SessionService()
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
    
    # 기본 라우트
    @app.route('/')
    def index():
        """기본 페이지를 표시합니다."""
        return redirect(url_for('lab.index'))
    
    # Docker 상태 확인 페이지
    @app.route('/docker-status')
    def docker_status():
        return render_template('docker_status.html', 
                             docker_available=app.docker_available)
    
    return app, socketio 