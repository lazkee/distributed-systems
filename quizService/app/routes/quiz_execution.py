from threading import Thread
from flask import Blueprint, current_app, request, jsonify
from app.middlewares.require_internal import require_internal
from app.cache.quiz_execution_cache import QuizExecutionCache
from app.services.quiz_execution_service import QuizExecutionService
from app.services.quiz_attempts_service import AttemptsService

quiz_execution_bp = Blueprint(
    "quiz_execution",
    __name__,
    url_prefix="/quiz-execution"
)


@quiz_execution_bp.get("/user/<int:user_id>/export")
@require_internal
def export_user_attempts(user_id: int):
    header_user_id = request.headers.get("X-User-Id")
    try:
        if int(header_user_id) != user_id:
            return jsonify({"success": False, "message": "Forbidden"}), 403
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Forbidden"}), 403

    attempts = AttemptsService.get_attempts_for_user_export(user_id)
    return jsonify({"success": True, "data": attempts}), 200


@quiz_execution_bp.route("/start", methods=["POST"])
@require_internal
def start_quiz():
    data = request.get_json()

    try:
        attempt = QuizExecutionService.start_quiz(
            quiz_id=int(data.get("quiz_id")),
            player_id=int(data.get("player_id"))
        )
    except ValueError as e:
        status = 409 if "active attempt" in str(e).lower() else 400
        return jsonify({"success": False, "message": str(e)}), status

    return jsonify({
        "success": True,
        "message": "Quiz started successfully",
        "data": attempt
    }), 201


@quiz_execution_bp.route("/answer", methods=["POST"])
@require_internal
def submit_answer():
    user_id_header = request.headers.get("X-User-Id")
    if not user_id_header:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    try:
        player_id = int(user_id_header)
    except ValueError:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json()

    try:
        result = QuizExecutionService.submit_answer(
            attempt_id=int(data.get("attempt_id")),
            question_id=int(data.get("question_id")),
            answer_ids=list(map(int, data.get("answer_ids", []))),
            player_id=player_id
        )
    except PermissionError:
        return jsonify({"success": False, "message": "Forbidden"}), 403
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    return jsonify({
        "success": True,
        "message": "Answer submitted successfully",
        "data": result
    }), 200


def finish_quiz_background(attempt_id, player_email, player_id, app):
    with app.app_context():
        try:
            QuizExecutionService.finish_quiz(int(attempt_id), player_email, player_id)
        except Exception:
            app.logger.exception(f"Error finishing quiz {attempt_id}")


@quiz_execution_bp.route("/finish", methods=["POST"])
@require_internal
def finish_quiz():
    user_id_header = request.headers.get("X-User-Id")
    if not user_id_header:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    try:
        player_id = int(user_id_header)
    except ValueError:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json()

    attempt_id = data.get("attempt_id")
    player_email = data.get("player_email")

    if not attempt_id or not player_email:
        return jsonify({
            "success": False,
            "message": "attempt_id and player_email are required"
        }), 400

    # Ownership check synchronously before any background work
    session = QuizExecutionCache.get_quiz(int(attempt_id))
    if not session:
        return jsonify({"success": False, "message": "Quiz attempt not found or expired"}), 404
    if session["player_id"] != player_id:
        return jsonify({"success": False, "message": "Forbidden"}), 403

    app = current_app._get_current_object()

    Thread(
        target=lambda: finish_quiz_background(attempt_id, player_email, player_id, app),
        daemon=True
    ).start()

    return jsonify({
        "success": True,
        "message": "Quiz finished successfully. Results will be sent via email.",
    }), 200
