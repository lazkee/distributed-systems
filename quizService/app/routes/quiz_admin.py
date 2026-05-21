from flask import Blueprint, jsonify, request

from app.middlewares.require_internal import require_internal
from app.validators.reject_quiz_validator import validate_reject_quiz
from  app.services.quiz_admin_service import QuizAdminService

quiz_admin_bp = Blueprint("quiz_admin", __name__, url_prefix="/quiz")


@quiz_admin_bp.get("/getApproved")
@require_internal
def get_approved():
    try:
        quizzes = QuizAdminService.get_approved()
        return jsonify({
            "success": True,
            "data": quizzes
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@quiz_admin_bp.get("/getPending")
@require_internal
def get_pending():
    try:
        quizzes = QuizAdminService.get_pending()
        return jsonify({
            "success": True,
            "data": quizzes
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@quiz_admin_bp.route("/admin/<int:quiz_id>", methods=["GET"])
@require_internal
def get_quiz_for_admin(quiz_id: int):
    try:
        quiz = QuizAdminService.get_quiz_for_admin(quiz_id)
        return jsonify({
            "success": True,
            "data": quiz
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


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

    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to approve quiz: {str(e)}"
        }), 500


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
        msg = str(e)
        if "not found" in msg:
            return jsonify({"success": False, "message": msg}), 404
        return jsonify({"success": False, "message": msg}), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to reject quiz: {str(e)}"
        }), 500


@quiz_admin_bp.route("/delete/<int:quiz_id>", methods=["DELETE"])
@require_internal
def delete_quiz(quiz_id):
    try:
        result = QuizAdminService.delete_quiz(quiz_id)

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to delete quiz: {str(e)}"
        }), 500