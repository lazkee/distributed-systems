import math
from multiprocessing import Process
from typing import List, Dict, Any
from app.models.user import User

from app.extensions import db
from app.constants.user_roles import UserRole
from app.services.mail_service import MailService
from app.services import jwt_blocklist_service
from ..config import Config
import requests
from app.utils.internal_headers import make_internal_headers

class AdminService:

   #all users
    @staticmethod
    def list_all_users(page: int, page_size: int) -> Dict[str, Any]:
        page = max(1, page)
        page_size = max(1, min(100, page_size))

        total = User.query.count()
        pages = max(1, math.ceil(total / page_size))

        users = (
            User.query
            .order_by(User.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = [
            {
                "id": user.id,
                "email": user.email,
                "firstName": user.first_name,
                "lastName": user.last_name,
                "role": user.role,
                "created_at": user.created_at.isoformat()
                if getattr(user, "created_at", None)
                else None,
            }
            for user in users
        ]

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": pages,
        }

    #change user role
    @staticmethod
    def change_user_role(user_id: int, new_role: UserRole) -> User:
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} does not exist.")

        if user.role == new_role.value:
            return user

        user.role = new_role.value
        db.session.flush()

        try:
            jwt_blocklist_service.invalidate_user_tokens(user_id)
        except Exception:
            db.session.rollback()
            raise RuntimeError("Token invalidation failed")

        db.session.commit()

        Process(target=MailService.send_role_change_email, args=(user.email, new_role)).start()

        return user

    #delete user
    @staticmethod
    def delete_user(user_id: int) -> bool:
        user = User.query.get(user_id)
        if not user:
            return False

        db.session.delete(user)
        db.session.commit()
        return True
    
    @staticmethod
    def get_report_player_ids(quiz_ids: list[int]) -> list[int]:
        url = f"{Config.QUIZ_SERVICE_BASE_URL}/quiz-mail/reports/player-ids"
        payload = {"quiz_ids": quiz_ids}
        response = requests.post(url, json=payload, headers=make_internal_headers(), timeout=10)

        if response.status_code == 400:
            message = response.json().get("message", "Invalid quiz IDs for report")
            raise ValueError(message)

        if response.status_code != 200:
            raise RuntimeError("Quiz service player ID lookup failed")

        return response.json()["data"]["player_ids"]

    @staticmethod
    def generate_report(quiz_ids: list[int], admin_email: str, users: list[dict]):
        url = f"{Config.QUIZ_SERVICE_BASE_URL}/quiz-mail/reports"

        payload = {
            "quiz_ids": quiz_ids,
            "admin_email": admin_email,
            "users": users
        }

        response = requests.post(url, json=payload, headers=make_internal_headers())

        if response.status_code == 400:
            message = response.json().get("message", "Invalid quiz IDs for report")
            raise ValueError(message)

        if response.status_code != 202:
            raise RuntimeError("Quiz service report generation failed")

        return response.json()
