import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import requests
from app.extensions import socketio
from app.constants.user_roles import UserRole
from app.middlewares.require_auth import require_auth
from app.middlewares.require_role import require_role
from app.utils.internal_headers import make_internal_headers
from app.services.quiz_service import QuizService
from app.services.user_service import UserService

quiz_leaderboard_bp = Blueprint("quiz-leaderboard", __name__, url_prefix="/quiz")

base = (os.getenv("QUIZ_SERVICE_BASE_URL") or "").rstrip("/")
QUIZ_SERVICE_BASE_URL = f"{base}/quiz"
@quiz_leaderboard_bp.get("/<int:quiz_id>/leaderboard")
@require_auth
def get_leaderboard(quiz_id: int):
    try:
        url = f"{QUIZ_SERVICE_BASE_URL}/{quiz_id}/leaderboard"
        resp = requests.get(url, headers=make_internal_headers(), timeout=20)

        payload = resp.json()

        data = payload.get("data", [])

        player_ids = [a.get("player_id") for a in data if a.get("player_id") is not None]
        id_to_email = {u["id"]: u["email"] for u in UserService.get_user_emails_by_ids(player_ids)}

        for attempt in data:
            player_id = attempt.get("player_id")
            attempt["player_email"] = id_to_email.get(
                player_id,
                "unknown@example.com"
            )

            attempt.pop("player_id", None)

        return jsonify({
            "success": True,
            "data": data
        }), resp.status_code

    except requests.RequestException:
        return jsonify({
            "success": False,
            "message": "Quiz service is unreachable"
        }), 503
