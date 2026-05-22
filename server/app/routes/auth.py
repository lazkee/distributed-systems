from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity, create_access_token
from app.services.auth_service import AuthService
from app.services import jwt_blocklist_service

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    token = AuthService.register_user(data)

    return jsonify({
        "success": True,
        "message": "User registered successfully",
        "data": token
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    result = AuthService.login_user(
        email=data.get("email"),
        password=data.get("password")
    )

    response = {
        "success": result["success"],
        "message": result["message"]
    }

    if result.get("data"):
        response["data"] = result["data"]

    return jsonify(response), result["status"]


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims = get_jwt()
    access_token = create_access_token(
        identity=identity,
        additional_claims={"email": claims.get("email"), "role": claims.get("role")}
    )
    return jsonify({
        "success": True,
        "message": "Token refreshed",
        "data": {"access_token": access_token}
    }), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    claims = get_jwt()
    try:
        jwt_blocklist_service.revoke_token(claims["jti"], claims["exp"])
    except Exception:
        return jsonify({"success": False, "message": "Logout failed"}), 503
    return jsonify({"success": True, "message": "Logged out successfully"}), 200


@auth_bp.route("/logout-refresh", methods=["POST"])
@jwt_required(refresh=True)
def logout_refresh():
    claims = get_jwt()
    try:
        jwt_blocklist_service.revoke_token(claims["jti"], claims["exp"])
    except Exception:
        return jsonify({"success": False, "message": "Logout failed"}), 503
    return jsonify({"success": True, "message": "Refresh token revoked successfully"}), 200