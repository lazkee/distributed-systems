import uuid
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from .config import Config
from .extensions import db, jwt

from app.routes.quiz import quiz_bp
from app.routes.quiz_execution import quiz_execution_bp
from app.routes.quiz_mail import quiz_mail_bp
from app.routes.quiz_admin import quiz_admin_bp
from app.routes.quiz_moderator import quiz_moderator_bp
from app.routes.quiz_leaderboard import quiz_leaderboard_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):
            return jsonify({"success": False, "message": error.description}), error.code
        ref = str(uuid.uuid4())[:8]
        app.logger.exception(f"Unhandled exception [ref={ref}]")
        return jsonify({
            "success": False,
            "message": f"An internal error occurred. Reference: {ref}"
        }), 500

    app.register_blueprint(quiz_bp)
    app.register_blueprint(quiz_execution_bp)
    app.register_blueprint(quiz_mail_bp)
    app.register_blueprint(quiz_admin_bp)
    app.register_blueprint(quiz_moderator_bp)
    app.register_blueprint(quiz_leaderboard_bp)

    return app
