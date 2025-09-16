from flask_socketio import emit
from . import socketio

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('client-message')
def handle_client_message(msg):
    print(f"Message from client: {msg}")
    emit('admin-message', f"Quản trị viên: Tôi đã nhận được: {msg}", broadcast=False)
