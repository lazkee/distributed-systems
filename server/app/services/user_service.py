from __future__ import annotations

from typing import Any, Dict, Optional

from app.extensions import db
from app.models.user import User


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
            "date_of_birth": user.date_of_birth.isoformat() if getattr(user, "date_of_birth", None) else None,
            "gender": getattr(user, "gender", None),
            "country": getattr(user, "country", None),
            "street": getattr(user, "street", None),
            "street_number": getattr(user, "street_number", None),
            "role": getattr(user, "role", None),
            "profile_picture_url": getattr(user, "profile_picture_url", None),
        }
    
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
