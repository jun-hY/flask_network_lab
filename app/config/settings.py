import os
import json
import logging
from pathlib import Path
from app.exceptions.custom_exceptions import ConfigError

logger = logging.getLogger(__name__)

class Settings:
    def __init__(self):
        self.config = {}
        self.lab_config = {}
        self.docker_config = {}
        self._load_config()
    
    def _load_config(self):
        """설정을 로드합니다."""
        try:
            # 기본 설정 파일 로드
            config_path = Path(__file__).parent.parent.parent / 'config.py'
            if config_path.exists():
                # config.py를 모듈로 임포트
                import importlib.util
                spec = importlib.util.spec_from_file_location("config", config_path)
                config_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config_module)
                
                # 설정 값을 딕셔너리로 변환
                for key in dir(config_module):
                    if not key.startswith('__'):
                        self.config[key] = getattr(config_module, key)
            
            # 랩 설정 로드
            self.lab_config = self.config.get('LAB_CONFIG', {})
            
            # Docker 설정 로드
            self.docker_config = self.config.get('DOCKER_CONFIG', {})
            
            # 환경 변수에서 설정 오버라이드
            self._override_from_env()
            
            # 설정 검증
            self._validate_config()
            
        except Exception as e:
            logger.error(f"설정 로드 중 오류 발생: {str(e)}")
            raise ConfigError(f"설정 로드 실패: {str(e)}")
    
    def _override_from_env(self):
        """환경 변수에서 설정을 오버라이드합니다."""
        # 랩 설정 오버라이드
        lab_config_env = os.getenv('LAB_CONFIG')
        if lab_config_env:
            try:
                self.lab_config.update(json.loads(lab_config_env))
            except json.JSONDecodeError as e:
                logger.warning(f"LAB_CONFIG 환경 변수 파싱 실패: {e}")
        
        # Docker 설정 오버라이드
        docker_config_env = os.getenv('DOCKER_CONFIG')
        if docker_config_env:
            try:
                self.docker_config.update(json.loads(docker_config_env))
            except json.JSONDecodeError as e:
                logger.warning(f"DOCKER_CONFIG 환경 변수 파싱 실패: {e}")
    
    def _validate_config(self):
        """설정을 검증합니다."""
        # 필수 설정 확인
        required_settings = ['SECRET_KEY', 'DEBUG']
        for setting in required_settings:
            if setting not in self.config:
                raise ConfigError(f"필수 설정이 누락되었습니다: {setting}")
        
        # 랩 설정 검증
        for lab_name, lab_config in self.lab_config.items():
            if not isinstance(lab_config, dict):
                raise ConfigError(f"잘못된 랩 설정 형식: {lab_name}")
            
            if 'roles' not in lab_config:
                raise ConfigError(f"랩 설정에 roles가 누락되었습니다: {lab_name}")
            
            if not isinstance(lab_config['roles'], list):
                raise ConfigError(f"랩 설정의 roles가 리스트가 아닙니다: {lab_name}")
        
        # Docker 설정 검증
        if 'container_names' not in self.docker_config:
            raise ConfigError("Docker 설정에 container_names가 누락되었습니다")
    
    def get_lab_config(self, lab_name):
        """랩 환경 설정을 가져옵니다."""
        return self.lab_config.get(lab_name, {})
    
    def get_container_name(self, role, lab_name):
        """컨테이너 이름을 생성합니다."""
        return self.docker_config.get('container_names', {}).get(role, f"{role}-{lab_name}")
    
    def get(self, key, default=None):
        """설정 값을 가져옵니다."""
        return self.config.get(key, default)
    
    def __getitem__(self, key):
        """설정 값을 가져옵니다."""
        return self.config[key]
    
    def __contains__(self, key):
        """설정 키가 존재하는지 확인합니다."""
        return key in self.config 