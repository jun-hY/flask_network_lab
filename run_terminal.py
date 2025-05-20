#!/usr/bin/env python3
"""
실행 방법:
    python run_terminal.py
"""
import os
import sys
from app import create_app, socketio

# 애플리케이션 생성
app, _ = create_app()

if __name__ == '__main__':
    # 웹소켓 서버 실행
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True,
        log_output=True
    )
