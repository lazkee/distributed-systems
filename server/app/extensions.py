from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

socketio = SocketIO()

db = SQLAlchemy()
jwt = JWTManager()
