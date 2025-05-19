from flask import Flask
from flask_socketio import SocketIO, join_room
from controllers.main import main_bp
from controllers.lab import lab_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# SocketIO 초기화
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# 블루프린트 등록
app.register_blueprint(main_bp)
app.register_blueprint(lab_bp)

# SocketIO 이벤트 핸들러
@socketio.on('join_lab')
def handle_join_lab(data):
    room = data['lab_name']
    join_room(room)
    print(f"Client joined room: {room}")

if __name__ == '__main__':
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
