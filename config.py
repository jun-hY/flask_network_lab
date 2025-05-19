LABS = [
    {'name': 'MITM Attack', 'url': '/lab/mitm'},
    {'name': 'ARP Spoofing', 'url': '/lab/arp'},
    {'name': 'DNS Spoofing', 'url': '/lab/dns'},
    {'name': 'ICMP Redirect', 'url': '/lab/icmp'},
    {'name': 'MAC Flooding', 'url': '/lab/mac'},
    {'name': 'DHCP Starvation', 'url': '/lab/dhcp'},
]

LAB_CONFIG = {
    "arp": {
        "roles": {
            "attacker": {
                "name": "Attacker",
                "description": "공격자 역할"
            },
            "hostA": {
                "name": "Host A",
                "description": "타겟 호스트 A"
            },
            "hostB": {
                "name": "Host B",
                "description": "타겟 호스트 B"
            }
        }
    }
}

import os
from pathlib import Path

# 기본 경로 설정
BASE_DIR = Path(__file__).parent
DOCKER_COMPOSE_DIR = BASE_DIR / "Docker"

# Docker 관련 설정
DOCKER_CONFIG = {
    "compose_dir": "Docker",
    "container_names": {
        "attacker": "seed-attacker",
        "hostA": "hostA-10.9.0.5",
        "hostB": "hostB-10.9.0.6"
    },
    "networks": ["net-10.9.0.0"],
    "subnet": "10.9.0.0/24"
}

# 랩 환경별 설정
LAB_CONFIG = {
    "arp": {
        "name": "ARP Spoofing Lab",
        "description": "ARP 스푸핑 공격 실습 환경. attacker 에서 python3 /volumes/arp_spoof.py 를 실행해보세요! hostA에선 arp -n을 실행해보세요!",
        "roles": ["attacker", "hostA", "hostB"],
        "docker_compose": "docker-compose-arp.yml",
        "volumes": {
            "arp_spoof": "/volumes/arp_spoof.py"
        }
    },
    # 추가 랩 환경을 여기에 정의할 수 있습니다.
}

# 로그 설정
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "app.log"
}

# Flask 앱 설정
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
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
