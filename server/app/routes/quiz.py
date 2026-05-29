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
from app.cache.quiz_cache import QuizCache

quiz_bp = Blueprint("quiz", __name__, url_prefix="/quiz")

base = (os.getenv("QUIZ_SERVICE_BASE_URL") or "").rstrip("/")
QUIZ_SERVICE_BASE_URL = f"{base}/quiz"


@quiz_bp.route("", methods=["POST"])
@jwt_required()
def create_quiz():
    try:
        if get_jwt()["role"] != UserRole.MODERATOR.value:
            return jsonify({
                "success": False,
                "message": "Forbidden"
            }), 403

        payload = dict(request.get_json(silent=True) or {})
        payload.pop("author_id", None)

        response = requests.post(
            QUIZ_SERVICE_BASE_URL,
            json=payload,
            headers=make_internal_headers(
                user_id=get_jwt_identity(),
                user_role=get_jwt().get("role"),
            ),
            timeout=5
        )

        try:
            data = response.json()
        except ValueError:
            data = {
                "success": False,
                "message": "Invalid response from quiz service"
            }

        if response.status_code != 201:
            return jsonify(data), response.status_code

        quiz = data.get("data", data)
        QuizCache.clear()

        # real-time admin notification
        socketio.emit("quiz_created", quiz, room="admins")

        return jsonify(data), 201

    except requests.RequestException:
        return jsonify({
            "success": False,
            "message": "Quiz service is unreachable"
        }), 503


@quiz_bp.route("/<int:quiz_id>", methods=["GET"])
@require_auth
def get_quiz(quiz_id: int):
    try:
        response = requests.get(
            f"{QUIZ_SERVICE_BASE_URL}/{quiz_id}",
            headers=make_internal_headers(),
            timeout=10
        )
        return jsonify(response.json()), response.status_code
    except requests.RequestException:
        return jsonify({
            "success": False,
            "message": "Quiz service is unreachable"
        }), 503


@quiz_bp.get("/approvedQuizzes")
@require_auth
def get_approved_quizzes():
    try:
        cached = QuizCache.get("approved_quizzes")
        if cached:
            quizzes = cached
            return cached
        else:
            quizzes = QuizService.get_approved_quizzes_from_quizService()
            QuizCache.set("approved_quizzes", quizzes)

        users = UserService.get_all_user_emails()
        id_to_email = {user["id"]: user["email"] for user in users}

        for quiz in quizzes["data"]:
            author_id = quiz.get("author_id", None)
            quiz["author_email"] = id_to_email.get(author_id, "unknown@example.com")

        return jsonify(quizzes), 200

    except requests.exceptions.RequestException:
        return jsonify({"success": False, "message": "Quiz service is unreachable"}), 503


@quiz_bp.get("/pendingQuizzes")
@require_auth
def get_pending_quizzes():
    try:
        cached = QuizCache.get("pending_quizzes")
        if cached:
            quizzes = cached
            return cached
        else:
            quizzes = QuizService.get_pending_quizzes_from_quizService()
            QuizCache.set("pending_quizzes", quizzes)

        users = UserService.get_all_user_emails()
        id_to_email = {user["id"]: user["email"] for user in users}

        for quiz in quizzes["data"]:
            author_id = quiz.get("author_id", None)
            quiz["author_email"] = id_to_email.get(author_id, "unknown@example.com")

        return jsonify(quizzes), 200

    except requests.exceptions.RequestException:
        return jsonify({"success": False, "message": "Quiz service is unreachable"}), 503


@quiz_bp.get("/catalog")
@require_auth
def get_catalog():
    try:
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 12, type=int)

        cache_key = f"catalog:{page}:{page_size}"
        catalog = QuizCache.get(cache_key)

        if catalog is not None:
            return catalog

        if catalog is None:
            catalog = QuizService.get_catalog_from_quizService(page=page, page_size=page_size)

            if not isinstance(catalog, dict) or catalog.get("success") is False:
                return jsonify(catalog), 502

            data = catalog.get("data") or {}
            items = data.get("items") or []

            users = UserService.get_all_user_emails()
            id_to_email = {u["id"]: u["email"] for u in users}

            for quiz in items:
                author_id = quiz.get("author_id")
                quiz["author_email"] = id_to_email.get(author_id, "unknown@example.com")

            catalog["data"] = data
            catalog["data"]["items"] = items

            QuizCache.set(cache_key, catalog)

            existing_keys = [k for k in QuizCache._cache.keys() if k.startswith("catalog:")]
            if len(existing_keys) > 3:
                QuizCache._cache.pop(existing_keys[0], None)

        return jsonify(catalog), 200

    except requests.exceptions.RequestException:
        return jsonify({"success": False, "message": "Quiz service is unreachable"}), 503


@quiz_bp.get("/admin/<int:quiz_id>")
@require_role([UserRole.ADMIN])
def get_quiz_for_admin(quiz_id: int):
    try:
        response = requests.get(
            f"{QUIZ_SERVICE_BASE_URL}/admin/{quiz_id}",
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


@quiz_bp.route("/admin/<int:quiz_id>/approve", methods=["PUT"])
@require_auth
@require_role([UserRole.ADMIN])
def approve_quiz(quiz_id):
    try:
        response = requests.put(
            f"{QUIZ_SERVICE_BASE_URL}/admin/{quiz_id}/approve",
            json=request.json,
            headers=make_internal_headers(
                user_id=get_jwt_identity(),
                user_role=get_jwt().get("role"),
            ),
            timeout=5
        )

        QuizCache.clear()

        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({"success": False, "message": "Quiz service is unreachable"}), 503



@quiz_bp.route("/admin/<int:quiz_id>/reject", methods=["PUT"])
@require_auth
@require_role([UserRole.ADMIN])
def reject_quiz(quiz_id):
    data = request.get_json()

    if not data or not data.get("comment"):
        return jsonify({
            "success": False,
            "message": "Comment is required"
        }), 400

    try:
        response = requests.put(
            f"{QUIZ_SERVICE_BASE_URL}/admin/{quiz_id}/reject",
            json=data,
            headers=make_internal_headers(
                user_id=get_jwt_identity(),
                user_role=get_jwt().get("role"),
            ),
            timeout=5
        )
        quiz_data = response.json()
        QuizCache.clear()

        data = quiz_data.get("data", {})
        author_id = data.get("author_id")
        comment = data.get("admin_comment")

        if author_id:
            socketio.emit(
                "quiz_rejected",
                {
                    "quiz_id": quiz_id,
                    "comment": comment,
                    "message": "Your quiz was rejected by admin"
                },
                room=f"user_{author_id}"
            )
        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({
            "success": False,
            "message": "Quiz service is unreachable"
        }), 503


@quiz_bp.route("/delete/<int:quiz_id>", methods=["OPTIONS"])
def delete_quiz_options(quiz_id):
    return "", 200 


@quiz_bp.route("/delete/<int:quiz_id>", methods=["DELETE"])
@require_auth
@require_role([UserRole.ADMIN, UserRole.MODERATOR])
def delete_quiz(quiz_id):
    try:
        response = requests.delete(
            f"{QUIZ_SERVICE_BASE_URL}/delete/{quiz_id}",
            headers=make_internal_headers(
                user_id=get_jwt_identity(),
                user_role=get_jwt().get("role"),
            ),
            timeout=5
        )

        try:
            data = response.json()
        except ValueError:
            data = {
                "success": False,
                "message": "Invalid response from quizService"
            }

        QuizCache.clear()

        return jsonify(data), response.status_code

    except requests.RequestException:
        return jsonify({
            "success": False,
            "message": "Quiz service is unreachable"
        }), 503


@quiz_bp.get("/my")
@require_auth
@require_role([UserRole.MODERATOR])
def get_my_quizzes():
    try:
        user_id = get_jwt_identity()
        cache_key = f"my_quizzes:{user_id}"

        cached = QuizCache.get(cache_key)
        if cached:
            return jsonify(cached), 200

        response = requests.get(
            f"{QUIZ_SERVICE_BASE_URL}/my/{user_id}",
            headers=make_internal_headers(
                user_id=get_jwt_identity(),
                user_role=get_jwt().get("role"),
            ),
            timeout=10
        )
        data = response.json()
        if response.status_code == 200:
            QuizCache.set(cache_key, data)

        return jsonify(data), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({"success": False, "message": "Quiz service is unreachable"}), 503


@quiz_bp.route("/getRejected/<int:quiz_id>", methods=["GET"])
@require_auth
@require_role([UserRole.MODERATOR])
def get_rejected_quiz_for_moderator(quiz_id: int):
    try:
        response = requests.get(
            f"{QUIZ_SERVICE_BASE_URL}/getRejected/{quiz_id}",
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


@quiz_bp.route("/edit/<int:quiz_id>", methods=["PUT"])
@require_auth
@require_role([UserRole.MODERATOR])
def edit_quiz(quiz_id: int):
    try:
        response = requests.put(
            f"{QUIZ_SERVICE_BASE_URL}/edit/{quiz_id}",
            json=request.json,
            headers=make_internal_headers(
                user_id=get_jwt_identity(),
                user_role=get_jwt().get("role"),
            ),
            timeout=10
        )
        quiz_data = response.json()
        if response.status_code == 200 and quiz_data.get("success"):
            quiz = quiz_data.get("data", {})

            socketio.emit("quiz_created", quiz, room="admins")
        
        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({
            "success": False,
            "message": "Quiz service is unreachable"
        }), 503