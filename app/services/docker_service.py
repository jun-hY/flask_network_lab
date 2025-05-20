"""
Docker 서비스 모듈
"""

import os
import logging
from python_on_whales import DockerClient
from app.exceptions.custom_exceptions import DockerError, ContainerError, NetworkError

logger = logging.getLogger(__name__)

class DockerService:
    def __init__(self):
        """Docker 서비스를 초기화합니다."""
        try:
            self.client = DockerClient()
            # Docker 연결 테스트
            self.client.version()
            logger.info("Docker 서비스 연결 성공")
        except Exception as e:
            logger.error(f"Docker 서비스 연결 실패: {str(e)}")
            raise DockerError("Docker 서비스에 연결할 수 없습니다. Docker Desktop이 실행 중인지 확인해주세요.")
    
    def start_lab(self, lab_name, lab_config):
        """랩 환경을 시작합니다."""
        try:
            containers = {}
            roles = lab_config.get('roles', [])
            
            for role in roles:
                container_name = self._get_container_name(role, lab_name)
                try:
                    # 컨테이너가 이미 실행 중인지 확인
                    container = self.client.container.inspect(container_name)
                    if container.state.running:
                        logger.info(f"컨테이너가 이미 실행 중입니다: {container_name}")
                        containers[role] = container.id
                        continue
                except:
                    pass
                
                # 새 컨테이너 시작
                container = self.client.container.run(
                    image="handsonsecurity/seed-ubuntu:large",
                    name=container_name,
                    detach=True,
                    tty=True,
                    interactive=True
                )
                containers[role] = container.id
                logger.info(f"컨테이너 시작됨: {container_name}")
            
            return containers
            
        except Exception as e:
            logger.error(f"랩 시작 실패: {str(e)}")
            # 실패 시 생성된 컨테이너 정리
            self.stop_lab(lab_name)
            raise DockerError(f"랩 시작 실패: {str(e)}")
    
    def stop_lab(self, lab_name):
        """랩 환경을 중지합니다."""
        try:
            # 관련된 모든 컨테이너 찾기
            containers = self.client.container.list(all=True, filters={"name": f"*-{lab_name}"})
            
            for container in containers:
                try:
                    container.stop()
                    container.remove()
                    logger.info(f"컨테이너 중지 및 제거됨: {container.name}")
                except Exception as e:
                    logger.warning(f"컨테이너 중지 실패: {container.name} - {str(e)}")
            
        except Exception as e:
            logger.error(f"랩 중지 실패: {str(e)}")
            raise DockerError(f"랩 중지 실패: {str(e)}")
    
    def _get_container_name(self, role, lab_name):
        """컨테이너 이름을 생성합니다."""
        return f"{role}-{lab_name}"
    
    def cleanup(self):
        """모든 컨테이너와 네트워크를 정리합니다."""
        try:
            # 모든 컨테이너 중지 및 제거
            containers = self.client.container.list(all=True)
            for container in containers:
                try:
                    container.stop()
                    container.remove()
                except Exception as e:
                    logger.warning(f"컨테이너 정리 실패: {container.name} - {str(e)}")
            
            # 사용하지 않는 네트워크 제거
            networks = self.client.network.list()
            for network in networks:
                if not network.containers:
                    try:
                        network.remove()
                    except Exception as e:
                        logger.warning(f"네트워크 정리 실패: {network.name} - {str(e)}")
            
            logger.info("Docker 환경 정리 완료")
            
        except Exception as e:
            logger.error(f"Docker 환경 정리 실패: {str(e)}")
            raise DockerError(f"Docker 환경 정리 실패: {str(e)}")
    
    def get_container_logs(self, container_name, tail=50):
        """컨테이너의 로그를 가져옵니다."""
        try:
            container = self.client.container.inspect(container_name)
            logs = self.client.container.logs(container_name, tail=tail, follow=False)
            return logs.decode('utf-8', errors='replace') if isinstance(logs, bytes) else str(logs)
        except Exception as e:
            logger.error(f"컨테이너 {container_name}의 로그를 가져오는 중 오류 발생: {e}")
            raise ContainerError(f"컨테이너 로그 조회 실패: {e}")
    
    def execute_command(self, container_name, command):
        """컨테이너에서 명령을 실행합니다."""
        try:
            result = self.client.container.execute(container_name, command)
            return result
        except Exception as e:
            logger.error(f"컨테이너 {container_name}에서 명령 실행 중 오류 발생: {e}")
            raise ContainerError(f"명령 실행 실패: {e}") 