from flask import Blueprint, jsonify, request

from app.middlewares.require_internal import require_internal
from app.validators.reject_quiz_validator import validate_reject_quiz
from  app.services.quiz_admin_service import QuizAdminService

quiz_admin_bp = Blueprint("quiz_admin", __name__, url_prefix="/quiz")


@quiz_admin_bp.get("/getApproved")
@require_internal
def get_approved():
    quizzes = QuizAdminService.get_approved()
    return jsonify({
        "success": True,
        "data": quizzes
    }), 200


@quiz_admin_bp.get("/getPending")
@require_internal
def get_pending():
    quizzes = QuizAdminService.get_pending()
    return jsonify({
        "success": True,
        "data": quizzes
    }), 200


@quiz_admin_bp.route("/admin/<int:quiz_id>", methods=["GET"])
@require_internal
def get_quiz_for_admin(quiz_id: int):
    try:
        quiz = QuizAdminService.get_quiz_for_admin(quiz_id)
        return jsonify({
            "success": True,
            "data": quiz
        }), 200
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Quiz not found"
        }), 404


@quiz_admin_bp.route("/admin/<int:quiz_id>/approve", methods=["PUT"])
@require_internal
def approve_quiz(quiz_id: int):
    try:
        result = QuizAdminService.approve_quiz(quiz_id)

        return jsonify({
            "success": True,
            "message": "Quiz approved successfully",
            "data": result
        }), 200

    except ValueError:
        return jsonify({
            "success": False,
            "message": "Quiz not found"
        }), 400


@quiz_admin_bp.route("/admin/<int:quiz_id>/reject", methods=["PUT"])
@require_internal
def reject_quiz(quiz_id: int):
    payload = request.get_json(silent=True)

    validation = validate_reject_quiz(payload)
    if not validation.ok:
        return jsonify({
            "success": False,
            "message": "Validation error",
            "errors": validation.errors
        }), 400

    try:
        result = QuizAdminService.reject_quiz(quiz_id, validation.data["comment"])

        return jsonify({
            "success": True,
            "message": "Quiz rejected successfully",
            "data": result
        }), 200

    except ValueError as e:
        if "not found" in str(e).lower():
            return jsonify({"success": False, "message": "Quiz not found"}), 404
        return jsonify({"success": False, "message": "Operation could not be completed"}), 400


@quiz_admin_bp.route("/delete/<int:quiz_id>", methods=["DELETE"])
@require_internal
def delete_quiz(quiz_id):
    user_id_header = request.headers.get("X-User-Id")
    if not user_id_header:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    role_header = request.headers.get("X-User-Role")
    if not role_header:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        requester_id = int(user_id_header)
    except ValueError:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    is_admin = role_header == "Admin"

    try:
        result = QuizAdminService.delete_quiz(quiz_id, requester_id, is_admin)

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result), 200

    except PermissionError:
        return jsonify({
            "success": False,
            "message": "Forbidden"
        }), 403