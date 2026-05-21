from flask import Blueprint, jsonify, request

from app.middlewares.require_internal import require_internal
from app.validators.create_quiz_validator import validate_create_quiz
from app.validators.edit_quiz_validator import validate_edit_quiz
from app.validators.reject_quiz_validator import validate_reject_quiz
from app.services.quiz_service import QuizService

quiz_bp = Blueprint("quiz", __name__, url_prefix="/quiz")


@quiz_bp.route("/<int:quiz_id>", methods=["GET"])
@require_internal
def get_quiz(quiz_id: int):
    try:
        quiz_data = QuizService.get_quiz(quiz_id)
        return jsonify({
            "success": True,
            "data": quiz_data
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 404
    except Exception as ex:
        return jsonify({
            "success": False,
            "message": f"Failed to fetch quiz {ex}"
        }), 500


@quiz_bp.get("/catalog")
@require_internal
def get_catalog():
    try:
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 12, type=int)

        data = QuizService.get_catalog(page=page, page_size=page_size)
        return jsonify({
            "success": True,
            "data": data
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500