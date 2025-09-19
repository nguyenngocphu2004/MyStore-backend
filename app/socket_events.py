from flask import request
from flask_socketio import join_room, leave_room, emit
from . import socketio

clients_rooms = {}  # lưu mapping client_sid -> room_id

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    room = clients_rooms.get(request.sid)
    if room:
        leave_room(room)
        del clients_rooms[request.sid]
        emit('admin-notify-disconnect', {'roomId': room}, broadcast=True)

@socketio.on('client-join-admin-chat')
def handle_client_join():
    room = request.sid  # dùng session id làm room id
    join_room(room)
    clients_rooms[request.sid] = room
    print(f"Client {request.sid} joined room {room}")
    emit('admin-notify', {'roomId': room, 'msg': f"Khách hàng {room} đã kết nối"}, broadcast=True)

@socketio.on('client-message')
def handle_client_message(msg):
    room = clients_rooms.get(request.sid)
    if room:
        print(f"Message from client {request.sid} in room {room}: {msg}")
        emit('admin-message', {'room': room, 'text': f"{msg}"}, room=room)
    else:
        print("Client chưa join room admin chat")

@socketio.on('admin-join-room')
def handle_admin_join(data):
    room = data.get('room')
    if room:
        join_room(room)
        print(f"Admin joined room {room}")

@socketio.on('admin-message')
def handle_admin_message(data):
    room = data.get('room')
    msg = data.get('msg')
    if room and msg:
        print(f"Admin gửi tin nhắn trong room {room}: {msg}")
        emit('client-message', {'room': room, 'text': f"{msg}"}, room=room)