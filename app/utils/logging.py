import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

def setup_logging(app):
    """로깅 시스템을 설정합니다."""
    # 로그 디렉토리 생성
    log_dir = Path(app.root_path) / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # 로그 파일 경로
    log_file = log_dir / f'app_{datetime.now().strftime("%Y%m%d")}.log'
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # 파일 핸들러 설정
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Flask 로거 설정
    flask_logger = logging.getLogger('flask.app')
    flask_logger.setLevel(logging.INFO)
    flask_logger.addHandler(file_handler)
    flask_logger.addHandler(console_handler)
    
    # Werkzeug 로거 설정
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.addHandler(file_handler)
    werkzeug_logger.addHandler(console_handler)
    
    # SocketIO 로거 설정
    socketio_logger = logging.getLogger('socketio')
    socketio_logger.setLevel(logging.INFO)
    socketio_logger.addHandler(file_handler)
    socketio_logger.addHandler(console_handler)
    
    # EngineIO 로거 설정
    engineio_logger = logging.getLogger('engineio')
    engineio_logger.setLevel(logging.INFO)
    engineio_logger.addHandler(file_handler)
    engineio_logger.addHandler(console_handler)
    
    # Docker 로거 설정
    docker_logger = logging.getLogger('docker')
    docker_logger.setLevel(logging.INFO)
    docker_logger.addHandler(file_handler)
    docker_logger.addHandler(console_handler)
    
    # 앱 로거 설정
    app_logger = logging.getLogger('app')
    app_logger.setLevel(logging.INFO)
    app_logger.addHandler(file_handler)
    app_logger.addHandler(console_handler)
    
    # 개발 모드에서는 더 자세한 로깅
    if app.debug:
        root_logger.setLevel(logging.DEBUG)
        flask_logger.setLevel(logging.DEBUG)
        werkzeug_logger.setLevel(logging.DEBUG)
        socketio_logger.setLevel(logging.DEBUG)
        engineio_logger.setLevel(logging.DEBUG)
        docker_logger.setLevel(logging.DEBUG)
        app_logger.setLevel(logging.DEBUG)
    
    return app_logger 