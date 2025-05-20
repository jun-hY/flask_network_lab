#!/usr/bin/env python3
"""
터미널 실행 스크립트
"""

import os
import sys
from app import create_app

def main():
    """터미널을 실행합니다."""
    app, socketio = create_app()
    
    try:
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=app.config.get('DEBUG', False),
            use_reloader=False
        )
    except Exception as e:
        app.logger.error(f"터미널 실행 중 오류 발생: {str(e)}")
        raise

if __name__ == '__main__':
    main()
