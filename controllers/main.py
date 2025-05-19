from flask import Blueprint, render_template
from config import LABS  # config.py에서 불러오기

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html', labs=LABS)
