class LabError(Exception):
    """랩 관련 기본 예외 클래스"""
    pass

class DockerError(LabError):
    """Docker 관련 예외"""
    pass

class PTYError(LabError):
    """PTY 관련 예외"""
    pass

class ConfigError(LabError):
    """설정 관련 예외"""
    pass

class ContainerError(DockerError):
    """컨테이너 관련 예외"""
    pass

class NetworkError(DockerError):
    """네트워크 관련 예외"""
    pass 