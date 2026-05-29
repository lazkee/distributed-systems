from flask import Flask
from .config import Config
from .extensions import db, jwt, socketio
from .extensions import db, jwt, socketio, limiter
from flask_cors import CORS
import cloudinary

from .routes.auth import auth_bp
from .services import jwt_blocklist_service
from .routes.admin import admin_bp
from .routes.user import user_bp
from .routes.quiz import quiz_bp
from .routes.quiz_execution import quiz_execution_bp
from .routes.quiz_leaderboard import quiz_leaderboard_bp
from .routes import socket_events 


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    cloudinary.config(
        cloud_name=Config.CLOUDINARY_CLOUD_NAME,
        api_key=Config.CLOUDINARY_API_KEY,
        api_secret=Config.CLOUDINARY_API_SECRET
    )

    CORS(
        app,
        resources={r"/*": {"origins": Config.FRONTEND_ORIGINS}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-TOKEN"]
    )


    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app, cors_allowed_origins=Config.FRONTEND_ORIGINS)

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload.get("jti")
        sub = jwt_payload.get("sub")
        iat = jwt_payload.get("iat")

        if not jti or sub is None or iat is None:
            return True

        try:
            user_id = int(sub)
        except (TypeError, ValueError):
            return True

        return (
            jwt_blocklist_service.is_token_revoked(jti)
            or jwt_blocklist_service.is_token_invalid_for_user(user_id, iat)
        )

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(quiz_execution_bp)
    app.register_blueprint(quiz_leaderboard_bp)
    return app
  