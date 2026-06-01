from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from app.middlewares.require_auth import require_auth
from app.services.user_service import UserService
from app.services.cloudinary_service import CloudinaryService
from app.validators.user_validator import validate_patch_me


user_bp = Blueprint("user", __name__, url_prefix="/users")


@user_bp.get("/me")
@require_auth
def get_me():
    user_id = int(get_jwt_identity())
    result = UserService.get_me(user_id)

    status = result.pop("status", 200)
    return jsonify(result), status


@user_bp.patch("/me")
@require_auth
def patch_me():
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True)

    validation = validate_patch_me(payload)
    if not validation.ok:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Validation error",
                    "errors": validation.errors,
                }
            ),
            400,
        )

    result = UserService.update_profile(user_id, validation.data)
    status = result.pop("status", 200)
    return jsonify(result), status



@user_bp.delete("/me")
@require_auth
def erase_me():
    user_id = int(get_jwt_identity())
    result = UserService.erase_my_account(user_id)
    status = result.pop("status", 200)
    return jsonify(result), status


@user_bp.get("/me/export")
@require_auth
def export_my_data():
    user_id = int(get_jwt_identity())
    result = UserService.export_my_data(user_id)
    status = result.pop("status", 200)
    return jsonify(result), status


@user_bp.post("/set-profile-picture")
@require_auth
def upload_profile_picture():
    user_id = int(get_jwt_identity())

    if "image" not in request.files:
        return jsonify({"success": False, "message": "No image provided"}), 400

    image = request.files["image"]

    try:
        result = CloudinaryService.upload_profile_picture(user_id, image)
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception:
        return jsonify({"success": False, "message": "Failed to upload profile picture"}), 500

    return jsonify(
        {
            "success": True,
            "message": "Profile picture uploaded successfully",
            "data": result,
        }
    ), 200
