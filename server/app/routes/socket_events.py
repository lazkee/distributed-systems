import re
from flask import request
from flask_socketio import join_room, disconnect
from flask_jwt_extended import decode_token
from app.extensions import socketio
from app.constants.user_roles import UserRole

_sockets: dict[str, dict] = {}

_USER_ROOM_RE = re.compile(r"^user_(\d+)$")


@socketio.on("connect")
def handle_connect(auth):
    if not isinstance(auth, dict):
        return False

    token = auth.get("token")
    if not token:
        return False

    try:
        decoded = decode_token(token)
    except Exception:
        return False

    try:
        user_id = int(decoded["sub"])
    except (KeyError, TypeError, ValueError):
        return False

    role = decoded.get("role")
    if not role:
        return False

    _sockets[request.sid] = {"user_id": user_id, "role": role}


@socketio.on("join")
def handle_join(room):
    current_user = _sockets.get(request.sid)
    if not current_user:
        disconnect()
        return

    if not isinstance(room, str):
        disconnect()
        return

    if room == "admins":
        if current_user["role"] == UserRole.ADMIN.value:
            join_room(room)
        else:
            disconnect()
        return

    match = _USER_ROOM_RE.match(room)
    if match:
        if int(match.group(1)) == current_user["user_id"]:
            join_room(room)
        else:
            disconnect()
        return

    disconnect()


@socketio.on("disconnect")
def handle_disconnect():
    _sockets.pop(request.sid, None)
