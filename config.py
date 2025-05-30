"""
Flask Network Lab 기본 설정 파일
"""

import os
from pathlib import Path

# 기본 경로 설정
BASE_DIR = Path(__file__).parent
DOCKER_COMPOSE_DIR = BASE_DIR / "Docker"

# Flask 설정
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# 랩 환경 설정
LAB_CONFIG = {
    'arp_poisoning': {
        'description': """ARP Cache Poisoning 실습 환경 
<p>1. 공격 타겟의 호스트에서 ping 10.9.0.99 를 실행해 arp 테이블에 10.9.0.99에 대한 정보를 등록합니다.</p>
<p>2. 공격 타겟에서 ifconfig 명령어를 실행해 공격 타겟의 MAC 주소를 확인합니다.</p>
<p>3. 공격자에서 python3 volumes/arp_cache_poisoning.py를 실행하고 공격 타겟의 MAC 주소를 입력합니다.</p>
<p>4. 공격 타겟의 호스트에서 arp -n 명령어로 arp 테이블이 수정되었는지 확인합니다.</p>
        """,
        'roles': ['HostA', 'HostB', 'HostM'],
    },
    'sniffing_spoofing': {
        'description': """ARP Spoofing을 이용한 패킷 스니핑 실습 환경

        """,
        'roles': ['attacker', 'hostA', 'hostB'],
    }
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
