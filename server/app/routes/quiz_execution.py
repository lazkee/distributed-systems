from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
import requests
import os

from app.middlewares.require_role import require_role
from app.constants.user_roles import UserRole
from app.utils.internal_headers import make_internal_headers

quiz_execution_bp = Blueprint(
    "quiz_execution",
    __name__,
    url_prefix="/quiz-execution"
)

base = (os.getenv("QUIZ_SERVICE_BASE_URL") or "").rstrip("/")
QUIZ_SERVICE_BASE_URL = f"{base}/quiz-execution"


@quiz_execution_bp.route("/start", methods=["POST"])
@require_role([UserRole.PLAYER])
def start_quiz():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    quiz_id = data.get("quiz_id")

    if not quiz_id:
        return jsonify({
            "success": False,
            "message": "quiz_id is required"
        }), 400

    payload = {
        "quiz_id": quiz_id,
        "player_id": user_id
    }

    try:
        response = requests.post(
            f"{QUIZ_SERVICE_BASE_URL}/start",
            json=payload,
            headers=make_internal_headers(
                user_id=get_jwt_identity(),
                user_role=get_jwt().get("role"),
            ),
            timeout=10
        )
        return jsonify(response.json()), response.status_code
    except requests.RequestException:
        return jsonify({
            "success": False,
            "message": "Quiz service is unreachable"
        }), 503


@quiz_execution_bp.route("/answer", methods=["POST"])
@require_role([UserRole.PLAYER])
def submit_answer():
    data = request.get_json()
    attempt_id = data.get("attempt_id")
    question_id = data.get("question_id")
    answer_ids = data.get("answer_ids")

    if not attempt_id or not question_id or not answer_ids:
        return jsonify({
            "success": False,
            "message": "attempt_id, question_id, and answer_ids are required"
        }), 400

    try:
        answer_ids = list(map(int, answer_ids))
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "answer_ids must be a list of integers"
        }), 400

    payload = {
        "attempt_id": attempt_id,
        "question_id": question_id,
        "answer_ids": answer_ids
    }

    try:
        response = requests.post(
            f"{QUIZ_SERVICE_BASE_URL}/answer",
            json=payload,
            headers=make_internal_headers(
                user_id=get_jwt_identity(),
                user_role=get_jwt().get("role"),
            ),
            timeout=10
        )
        return jsonify(response.json()), response.status_code
    except requests.RequestException:
        return jsonify({
            "success": False,
            "message": "Quiz service is unreachable"
        }), 503


@quiz_execution_bp.route("/finish", methods=["POST"])
@require_role([UserRole.PLAYER])
def finish_quiz():
    data = request.get_json()
    attempt_id = data.get("attempt_id")

    if not attempt_id:
        return jsonify({
            "success": False,
            "message": "attempt_id is required"
        }), 400

    claims = get_jwt()
    user_email = claims.get("email")
    user_id = int(get_jwt_identity())

    if not user_email:
        return jsonify({
            "success": False,
            "message": "User email not found in token"
        }), 400

    payload = {
        "attempt_id": attempt_id,
        "player_id": user_id,
        "player_email": user_email
    }

    try:
        response = requests.post(
            f"{QUIZ_SERVICE_BASE_URL}/finish",
            json=payload,
            headers=make_internal_headers(
                user_id=get_jwt_identity(),
                user_role=get_jwt().get("role"),
            ),
            timeout=10
        )
        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({
            "success": False,
            "message": "Quiz service is unreachable"
        }), 503