from __future__ import annotations

from typing import Any, Dict, Optional

import requests as http_requests

from app.extensions import db
from app.models.user import User
from app.config import Config
from app.utils.internal_headers import make_internal_headers
from app.services import jwt_blocklist_service
from app.services.cloudinary_service import CloudinaryService


class UserService:
    @staticmethod
    def get_me(user_id: int) -> Dict[str, Any]:
        user = UserService._get_user_or_none(user_id)
        if not user:
            return {"success": False, "message": "User not found", "status": 404}

        return {
            "success": True,
            "message": "User fetched successfully",
            "data": UserService._to_profile_dto(user),
            "status": 200,
        }

    @staticmethod
    def update_profile(user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        `updates` must be validated/sanitized by validator (allowed fields, types, date parsing).
        """
        user = UserService._get_user_or_none(user_id)
        if not user:
            return {"success": False, "message": "User not found", "status": 404}

        if not updates:
            return {"success": False, "message": "No changes provided", "status": 400}

        try:
            for key, value in updates.items():
                setattr(user, key, value)

            db.session.commit()
        except Exception:
            db.session.rollback()
            return {"success": False, "message": "Failed to update profile", "status": 500}

        return {
            "success": True,
            "message": "Profile updated",
            "data": UserService._to_profile_dto(user),
            "status": 200,
        }

    # -------------------------
    # Helpers
    # -------------------------

    @staticmethod
    def _get_user_or_none(user_id: int) -> Optional[User]:
        return User.query.get(user_id)

    @staticmethod
    def _to_profile_dto(user: User) -> Dict[str, Any]:
        return {
            "id": user.id,
            "email": getattr(user, "email", None),
            "first_name": getattr(user, "first_name", None),
            "last_name": getattr(user, "last_name", None),
            "country": getattr(user, "country", None),
            "role": getattr(user, "role", None),
            "profile_picture_url": getattr(user, "profile_picture_url", None),
        }
    
    @staticmethod
    def export_my_data(user_id: int) -> Dict[str, Any]:
        user = UserService._get_user_or_none(user_id)
        if not user:
            return {"success": False, "message": "User not found", "status": 404}

        profile = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "country": getattr(user, "country", None),
            "role": user.role,
            "consent_given_at": user.consent_given_at.isoformat() if user.consent_given_at else None,
            "profile_picture_url": getattr(user, "profile_picture_url", None),
        }

        url = f"{Config.QUIZ_SERVICE_BASE_URL}/quiz-execution/user/{user_id}/export"
        try:
            resp = http_requests.get(
                url,
                headers=make_internal_headers(user_id=user_id),
                timeout=10,
            )
            if resp.status_code == 200:
                quiz_attempts = resp.json().get("data", [])
            else:
                quiz_attempts = []
        except http_requests.RequestException:
            return {"success": False, "message": "Quiz service is unavailable", "status": 503}

        return {
            "success": True,
            "message": "Data export successful",
            "data": {
                "profile": profile,
                "quiz_attempts": quiz_attempts,
            },
            "status": 200,
        }

    @staticmethod
    def erase_my_account(user_id: int) -> Dict[str, Any]:
        user = UserService._get_user_or_none(user_id)
        if not user:
            return {"success": False, "message": "User not found", "status": 404}

        try:
            jwt_blocklist_service.invalidate_user_tokens(user_id)
        except Exception:
            return {"success": False, "message": "Failed to erase account", "status": 500}

        if user.profile_picture_public_id:
            try:
                CloudinaryService.delete_profile_picture(user.profile_picture_public_id)
            except Exception:
                pass

        url = f"{Config.QUIZ_SERVICE_BASE_URL}/quiz-execution/user/{user_id}/erase"
        try:
            http_requests.post(
                url,
                headers=make_internal_headers(user_id=user_id),
                timeout=10,
            )
        except http_requests.RequestException:
            pass

        try:
            user.email = f"deleted_user_{user_id}@deleted.local"
            user.first_name = "Deleted"
            user.last_name = "User"
            user.country = ""
            user.profile_picture_url = None
            user.profile_picture_public_id = None

            db.session.commit()
        except Exception:
            db.session.rollback()
            return {"success": False, "message": "Failed to erase account", "status": 500}

        return {"success": True, "message": "Account erased successfully", "status": 200}

    @staticmethod
    def get_all_user_emails() -> list[dict]:
        users = User.query.all()
        return [{"id": user.id, "email": user.email} for user in users]

    @staticmethod
    def get_user_emails_by_ids(user_ids: list[int]) -> list[dict]:
        cleaned = []
        for uid in user_ids:
            try:
                cleaned.append(int(uid))
            except (TypeError, ValueError):
                pass
        cleaned = list(set(cleaned))
        if not cleaned:
            return []
        users = User.query.filter(User.id.in_(cleaned)).all()
        return [{"id": user.id, "email": user.email} for user in users]
