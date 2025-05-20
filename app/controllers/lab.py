"""
랩 환경 관리를 위한 컨트롤러
"""

from flask import Blueprint, jsonify, request, current_app, redirect, url_for, render_template
from flask_socketio import emit
from app.exceptions.custom_exceptions import LabError

# 블루프린트 생성
lab_bp = Blueprint('lab', __name__, url_prefix='/lab')

@lab_bp.route('/')
def index():
    """기본 페이지를 표시합니다."""
    if not current_app.docker_available:
        return redirect(url_for('lab.docker_status'))
    
    # 랩 환경 목록 가져오기
    labs = []
    for lab_name, lab_config in current_app.config['LAB_CONFIG'].items():
        labs.append({
            'name': lab_name,
            'description': lab_config.get('description', ''),
            'roles': lab_config.get('roles', [])
        })
    
    return render_template('lab_list.html', labs=labs)

@lab_bp.route('/status')
def docker_status():
    """Docker 상태 확인 페이지를 표시합니다."""
    return render_template('docker_status.html', 
                         docker_available=current_app.docker_available)

@lab_bp.route('/<lab_name>')
def lab_detail(lab_name):
    """특정 랩 환경의 상세 페이지를 표시합니다."""
    if not current_app.docker_available:
        return redirect(url_for('lab.docker_status'))
    
    # 랩 설정 확인
    lab_config = current_app.config['LAB_CONFIG'].get(lab_name)
    if not lab_config:
        return "Lab not found", 404
    
    lab_data = {
        "name": lab_name,
        "roles": lab_config.get("roles", []),
        "description": lab_config.get("description", "")
    }
    
    return render_template('lab.html', lab=lab_data)

@lab_bp.route('/list', methods=['GET'])
def get_labs():
    """사용 가능한 랩 환경 목록을 반환합니다."""
    if not current_app.docker_available:
        return jsonify({'error': 'Docker 서비스가 사용 불가능합니다.'}), 503
    try:
        labs = []
        for lab_name, lab_config in current_app.config['LAB_CONFIG'].items():
            labs.append({
                'name': lab_name,
                'description': lab_config.get('description', ''),
                'roles': lab_config.get('roles', [])
            })
        return jsonify({'labs': labs})
    except Exception as e:
        raise LabError(f"랩 목록 조회 실패: {str(e)}")

@lab_bp.route('/<lab_name>/start', methods=['POST'])
def start_lab(lab_name):
    """랩 환경을 시작합니다."""
    if not current_app.docker_available:
        return jsonify({'error': 'Docker 서비스가 사용 불가능합니다.'}), 503
    try:
        docker_service = current_app.docker_service
        session_service = current_app.session_service
        
        # 랩 설정 확인
        lab_config = current_app.config['LAB_CONFIG'].get(lab_name)
        if not lab_config:
            raise LabError(f"존재하지 않는 랩 환경: {lab_name}")
        
        # Docker 컨테이너 시작
        containers = docker_service.start_lab(lab_name, lab_config)
        
        # 세션 생성
        session_id = session_service.create_session(lab_name, containers)
        
        return jsonify({
            'session_id': session_id,
            'lab_name': lab_name,
            'containers': containers
        })
    except Exception as e:
        raise LabError(f"랩 시작 실패: {str(e)}")

@lab_bp.route('/<lab_name>/stop', methods=['POST'])
def stop_lab(lab_name):
    """랩 환경을 중지합니다."""
    if not current_app.docker_available:
        return jsonify({'error': 'Docker 서비스가 사용 불가능합니다.'}), 503
    try:
        docker_service = current_app.docker_service
        session_service = current_app.session_service
        
        # 세션 정리
        session_service.cleanup_session(lab_name)
        
        # Docker 컨테이너 중지
        docker_service.stop_lab(lab_name)
        
        return jsonify({'message': '랩 환경이 중지되었습니다.'})
    except Exception as e:
        raise LabError(f"랩 중지 실패: {str(e)}")

def register_socketio_handlers(socketio):
    """SocketIO 이벤트 핸들러를 등록합니다."""
    
    @socketio.on('connect')
    def handle_connect():
        """클라이언트 연결 시 호출됩니다."""
        if not current_app.docker_available:
            emit('error', {'message': 'Docker 서비스에 연결할 수 없습니다. Docker Desktop이 실행 중인지 확인해주세요.'})
            return False
        emit('connection_response', {'data': 'Connected'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """클라이언트 연결 해제 시 호출됩니다."""
        pass
    
    @socketio.on('terminal_input')
    def handle_terminal_input(data):
        """터미널 입력을 처리합니다."""
        try:
            session_id = data.get('session_id')
            container_id = data.get('container_id')
            input_data = data.get('input')
            
            if not all([session_id, container_id, input_data]):
                raise LabError("필수 파라미터가 누락되었습니다.")
            
            session_service = current_app.session_service
            session_service.send_input(session_id, container_id, input_data)
            
        except Exception as e:
            emit('error', {'message': str(e)})
    
    @socketio.on('terminal_resize')
    def handle_terminal_resize(data):
        """터미널 크기 조정을 처리합니다."""
        try:
            session_id = data.get('session_id')
            container_id = data.get('container_id')
            rows = data.get('rows')
            cols = data.get('cols')
            
            if not all([session_id, container_id, rows, cols]):
                raise LabError("필수 파라미터가 누락되었습니다.")
            
            session_service = current_app.session_service
            session_service.resize_terminal(session_id, container_id, rows, cols)
            
        except Exception as e:
            emit('error', {'message': str(e)}) 