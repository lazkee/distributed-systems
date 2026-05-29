from flask import Blueprint, jsonify
from app.middlewares.require_internal import require_internal
from app.services.quiz_attempts_service import AttemptsService

quiz_leaderboard_bp = Blueprint("quiz-leaderboard", __name__, url_prefix="/quiz")

@quiz_leaderboard_bp.get("/<int:quiz_id>/leaderboard")
@require_internal
def get_leaderboard(quiz_id: int):
    attempts = AttemptsService.get_attempts_for_quizzes([str(quiz_id)])

    return jsonify({
        "success": True,
        "data": attempts
    }), 200
