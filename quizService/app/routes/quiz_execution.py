from threading import Thread
from flask import Blueprint, current_app, request, jsonify
from app.middlewares.require_internal import require_internal
from app.services.quiz_execution_service import QuizExecutionService

quiz_execution_bp = Blueprint(
    "quiz_execution",
    __name__,
    url_prefix="/quiz-execution"
)


@quiz_execution_bp.route("/start", methods=["POST"])
@require_internal
def start_quiz():
    data = request.get_json()

    attempt = QuizExecutionService.start_quiz(
        quiz_id = int(data.get("quiz_id")),
        player_id = int(data.get("player_id"))
    )

    return jsonify({
        "success": True,
        "message": "Quiz started successfully",
        "data": attempt
    }), 201


@quiz_execution_bp.route("/answer", methods=["POST"])
@require_internal
def submit_answer():
    data = request.get_json()

    result = QuizExecutionService.submit_answer(
        attempt_id=int(data.get("attempt_id")),
        question_id=int(data.get("question_id")),
        answer_ids=list(map(int, data.get("answer_ids", [])))
    )

    return jsonify({
        "success": True,
        "message": "Answer submitted successfully",
        "data": result
    }), 200


def finish_quiz_background(attempt_id, player_email, app):
        with app.app_context():
            try:
                QuizExecutionService.finish_quiz(int(attempt_id), player_email)
            except Exception:
                app.logger.exception(f"Error finishing quiz {attempt_id}")


@quiz_execution_bp.route("/finish", methods=["POST"])
@require_internal
def finish_quiz():
    data = request.get_json()

    attempt_id = data.get("attempt_id")
    player_email = data.get("player_email")

    if not attempt_id or not player_email:
        return jsonify({
            "success": False,
            "message": "attempt_id and player_email are required"
        }), 400

    app = current_app._get_current_object()

    Thread(
        target=lambda: finish_quiz_background(attempt_id, player_email, app),
        daemon=True
    ).start()
    
    return jsonify({
        "success": True,
        "message": "Quiz finished successfully. Results will be sent via email.",
    }), 200
