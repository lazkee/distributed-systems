from flask import Blueprint, jsonify, request

from app.middlewares.require_internal import require_internal
from app.validators.create_quiz_validator import validate_create_quiz
from app.validators.edit_quiz_validator import validate_edit_quiz
from app.services.quiz_moderator_service import QuizModeratorService

quiz_moderator_bp = Blueprint("quiz_moderator", __name__, url_prefix="/quiz")


@quiz_moderator_bp.post("")
@require_internal
def create_quiz():
    user_id_header = request.headers.get("X-User-Id")
    if not user_id_header:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        requester_id = int(user_id_header)
    except ValueError:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        payload["author_id"] = requester_id

    validation = validate_create_quiz(payload)
    if not validation.ok:
        return jsonify({
            "success": False,
            "message": "Validation error",
            "errors": validation.errors
        }), 400

    try:
        result = QuizModeratorService.create_quiz(validation.data)
        return jsonify({
            "success": True,
            "data": result
        }), 201

    except ValueError:
        return jsonify({
            "success": False,
            "message": "Quiz creation failed"
        }), 400



@quiz_moderator_bp.get("/my/<int:user_id>")
@require_internal
def get_my_quizzes(user_id: int):
    user_id_header = request.headers.get("X-User-Id")
    if not user_id_header:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        requester_id = int(user_id_header)
    except ValueError:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if requester_id != user_id:
        return jsonify({"success": False, "message": "Forbidden"}), 403

    quizzes = QuizModeratorService.get_by_author(user_id)
    return jsonify({
        "success": True,
        "data": quizzes
    }), 200


@quiz_moderator_bp.route("/getRejected/<int:quiz_id>", methods=["GET"])
@require_internal
def get_rejected_quiz(quiz_id: int):
    user_id_header = request.headers.get("X-User-Id")
    if not user_id_header:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        requester_id = int(user_id_header)
    except ValueError:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        quiz = QuizModeratorService.get_rejected_quiz_for_edit(quiz_id, requester_id)
        return jsonify({
            "success": True,
            "data": quiz
        }), 200
    except PermissionError:
        return jsonify({
            "success": False,
            "message": "Forbidden"
        }), 403
    except ValueError as e:
        if "not found" in str(e).lower():
            return jsonify({"success": False, "message": "Quiz not found"}), 400
        return jsonify({"success": False, "message": "Quiz cannot be edited in its current state"}), 400


@quiz_moderator_bp.route("/edit/<int:quiz_id>", methods=["PUT"])
@require_internal
def edit_quiz(quiz_id: int):
    user_id_header = request.headers.get("X-User-Id")
    if not user_id_header:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        requester_id = int(user_id_header)
    except ValueError:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    payload = request.get_json(silent=True)

    validation = validate_edit_quiz(payload)
    if not validation.ok:
        return jsonify({
            "success": False,
            "message": "Validation error",
            "errors": validation.errors
        }), 400

    if not payload:
        return jsonify({
            "success": False,
            "message": "Request body is required"
        }), 400

    try:
        result = QuizModeratorService.edit_quiz(quiz_id, payload, requester_id)
        return jsonify({
            "success": True,
            "message": "Quiz updated successfully",
            "data": result
        }), 200

    except PermissionError:
        return jsonify({
            "success": False,
            "message": "Forbidden"
        }), 403

    except ValueError as e:
        if "not found" in str(e).lower():
            return jsonify({"success": False, "message": "Quiz not found"}), 400
        return jsonify({"success": False, "message": "Quiz cannot be edited in its current state"}), 400

