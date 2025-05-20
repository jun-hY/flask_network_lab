import time
import logging
from datetime import datetime
from app.services.pty_service import PTYService
from app.exceptions.custom_exceptions import LabError

logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self):
        self.active_sessions = {}  # 활성 세션 정보
        self.active_ptys = {}  # 활성 PTY 세션
        self.running_threads = {}  # 실행 중인 로그 스트리밍 스레드
    
    def create_session(self, sid, container_name, role, lab_name, socketio):
        """새로운 세션을 생성합니다."""
        try:
            # 기존 세션 정리
            if sid in self.active_sessions:
                self.cleanup_session(sid)
            
            # PTY 세션 생성 및 시작
            pty_session = PTYService(container_name, socketio, sid, role)
            pty_session.start()
            
            # 세션 정보 저장
            pty_id = f"{sid}_{int(time.time())}"
            self.active_sessions[sid] = {
                'pty_id': pty_id,
                'container_name': container_name,
                'role': role,
                'lab_name': lab_name,
                'created_at': datetime.now().isoformat()
            }
            self.active_ptys[pty_id] = pty_session
            
            logger.info(f"세션 생성 성공: 컨테이너={container_name}, 세션ID={pty_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"세션 생성 실패: {str(e)}", exc_info=True)
            return False, f"세션을 생성할 수 없습니다: {str(e)}"
    
    def cleanup_session(self, sid):
        """세션을 정리합니다."""
        if sid in self.active_sessions:
            session = self.active_sessions[sid]
            pty_id = session.get('pty_id')
            
            # PTY 세션 정리
            if pty_id and pty_id in self.active_ptys:
                try:
                    self.active_ptys[pty_id].stop()
                    logger.debug(f"PTY 세션 종료: {pty_id}")
                except Exception as e:
                    logger.error(f"PTY 세션 정리 중 오류: {e}", exc_info=True)
                finally:
                    if pty_id in self.active_ptys:
                        del self.active_ptys[pty_id]
            
            # 세션 정보 제거
            del self.active_sessions[sid]
            logger.info(f"세션 정리 완료: {sid}")
    
    def cleanup_lab_sessions(self, lab_name):
        """특정 랩의 모든 세션을 정리합니다."""
        for sid, session in list(self.active_sessions.items()):
            if session.get('lab_name') == lab_name:
                self.cleanup_session(sid)
    
    def get_session(self, sid):
        """세션 정보를 가져옵니다."""
        return self.active_sessions.get(sid)
    
    def get_pty_session(self, sid):
        """PTY 세션을 가져옵니다."""
        session = self.get_session(sid)
        if session:
            return self.active_ptys.get(session.get('pty_id'))
        return None
    
    def handle_pty_input(self, sid, data):
        """PTY 입력을 처리합니다."""
        session = self.get_session(sid)
        if not session:
            return
        
        lab_name = data.get('lab_name')
        role = data.get('role')
        
        if not all([lab_name, role]):
            logger.error("Missing lab_name or role in pty_input")
            return
        
        pty_session = self.get_pty_session(sid)
        if not pty_session:
            return
        
        if 'input' in data:
            pty_session.write(data['input'])
        
        if 'resize' in data:
            rows = data['resize'].get('rows', 24)
            cols = data['resize'].get('cols', 80)
            pty_session.resize(rows, cols) 