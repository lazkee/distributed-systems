from flask import Blueprint, request, jsonify
from app.middlewares.require_role import require_role
from app.constants.user_roles import UserRole
from app.services.admin_service import AdminService
from app.services.admin_service import AdminService
from app.constants.user_roles import UserRole
from flask_jwt_extended import get_jwt
from app.services.user_service import UserService

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/users")
@require_role([UserRole.ADMIN])
def list_users():
    users = AdminService.list_all_users()

    return jsonify({
        "success": True,
        "data": users
    }), 200


@admin_bp.route("/change-role", methods=["POST"])
@require_role([UserRole.ADMIN])
def change_role():
    data = request.get_json()
    user_id = data.get("user_id")
    new_role_str = data.get("new_role")

    if not user_id or not new_role_str:
        return jsonify({"success": False, "message": "user_id and new_role required"}), 400

    try:
        new_role = UserRole(new_role_str)  # Convert string to enum
    except ValueError:
        return jsonify({"success": False, "message": "Invalid role"}), 400

    try:
        user = AdminService.change_user_role(user_id, new_role)
        return jsonify({
            "success": True,
            "message": f"User role updated to {new_role.value}",
            "data": {"id": user.id, "email": user.email, "role": user.role, "firstName": user.first_name, "lastName": user.last_name}
        }), 200
    except ValueError:
        return jsonify({"success": False, "message": "User not found"}), 404
    except RuntimeError:
        return jsonify({"success": False, "message": "Role change could not be completed"}), 503


@admin_bp.delete("/delete-user/<int:user_id>")
@require_role([UserRole.ADMIN])
def delete_user(user_id: int):
    deleted = AdminService.delete_user(user_id)

    if not deleted:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    return jsonify({
        "success": True,
        "message": "User deleted"
    }), 200

@admin_bp.post("/report")
@require_role([UserRole.ADMIN])
def generate_report():
    claims = get_jwt()
    admin_email = claims.get("email")

    data = request.get_json()
    quiz_ids = data["quiz_ids"]

    users = UserService.get_all_user_emails()

    if not quiz_ids or not isinstance(quiz_ids, list):
        return jsonify({"success": False, "message": "quiz_ids must be a list"}), 400
    
    if not users or not isinstance(users, list):
        return jsonify({"success": False, "message": "users must be a list"}), 400

    try:
        response = AdminService.generate_report(quiz_ids, admin_email, users)
    except ValueError:
        return jsonify({"success": False, "message": "One or more quiz IDs are invalid or not approved"}), 400

    return jsonify({
        "success": True,
        "message": response.get("message", "Report generation started")
    }), 202