from datetime import timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required, get_jwt, get_jwt_identity, create_access_token,
    set_access_cookies, set_refresh_cookies,
    unset_access_cookies, unset_refresh_cookies,
)
from app.extensions import limiter
from app.services.auth_service import AuthService
from app.services import jwt_blocklist_service
from app.models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    data = request.get_json()

    tokens = AuthService.register_user(data)

    response = jsonify({"success": True, "message": "User registered successfully"})
    set_access_cookies(response, tokens["access_token"])
    set_refresh_cookies(response, tokens["refresh_token"])
    return response, 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()

    result = AuthService.login_user(
        email=data.get("email"),
        password=data.get("password")
    )

    if not result.get("data"):
        return jsonify({"success": result["success"], "message": result["message"]}), result["status"]

    response = jsonify({"success": True, "message": "Login successful"})
    set_access_cookies(response, result["data"]["access_token"])
    set_refresh_cookies(response, result["data"]["refresh_token"])
    return response, 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    user = User.query.get(int(identity))
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 401

    access_token = create_access_token(
        identity=identity,
        additional_claims={"email": user.email, "role": user.role}
    )
    response = jsonify({"success": True, "message": "Token refreshed"})
    set_access_cookies(response, access_token)
    return response, 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    claims = get_jwt()
    try:
        jwt_blocklist_service.revoke_token(claims["jti"], claims["exp"])
    except Exception:
        return jsonify({"success": False, "message": "Logout failed"}), 503

    response = jsonify({"success": True, "message": "Logged out successfully"})
    unset_access_cookies(response)
    return response, 200


@auth_bp.route("/ws-token", methods=["GET"])
@jwt_required()
def ws_token():
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid identity"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 401

    token = create_access_token(
        identity=identity,
        additional_claims={"email": user.email, "role": user.role},
        expires_delta=timedelta(seconds=60),
    )
    return jsonify({"success": True, "message": "WebSocket token issued", "data": {"ws_token": token}}), 200


@auth_bp.route("/refresh/logout", methods=["POST"])
@jwt_required(refresh=True)
def logout_refresh():
    claims = get_jwt()
    try:
        jwt_blocklist_service.revoke_token(claims["jti"], claims["exp"])
    except Exception:
        return jsonify({"success": False, "message": "Logout failed"}), 503

    response = jsonify({"success": True, "message": "Refresh token revoked successfully"})
    unset_refresh_cookies(response)
    return response, 200