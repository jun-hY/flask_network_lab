"""
Flask Network Lab 기본 설정 파일
"""

import os
import secrets
from pathlib import Path

# 기본 경로 설정
BASE_DIR = Path(__file__).parent
DOCKER_COMPOSE_DIR = BASE_DIR / "Docker"

# Flask 설정
SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# 랩 환경 설정
LAB_CONFIG = {
    'basic_network': {
        'roles': ['router1', 'router2', 'host1', 'host2'],
        'description': '기본 네트워크 구성 실습'
    },
    'ospf_network': {
        'roles': ['router1', 'router2', 'router3', 'host1', 'host2'],
        'description': 'OSPF 라우팅 프로토콜 실습'
    }
}

# Docker 설정
DOCKER_CONFIG = {
    'container_names': {
        'router1': 'router1',
        'router2': 'router2',
        'router3': 'router3',
        'host1': 'host1',
        'host2': 'host2'
    },
    'image': 'network_lab:latest',
    'network_name': 'network_lab_net'
}

# 로그 설정
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "app.log"
}

# Flask 앱 설정
class Config:
    SECRET_KEY = SECRET_KEY
    DOCKER_COMPOSE_DIR = str(DOCKER_COMPOSE_DIR)
    
    @staticmethod
    def init_app(app):
        pass

# 개발 환경 설정
class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "DEBUG"

# 프로덕션 환경 설정
class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = "WARNING"

# 환경별 설정 매핑
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
