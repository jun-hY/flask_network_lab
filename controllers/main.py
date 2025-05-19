from flask import Blueprint, render_template
from config import LABS

# 블루프린트 생성
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """메인 페이지를 표시합니다."""
    return render_template('index.html', labs=LABS)
