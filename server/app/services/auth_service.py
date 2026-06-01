from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token

from app.extensions import db
from app.models.user import User
from app.constants.user_roles import UserRole
from ..validators.auth_validator import validate_register_data

class AuthService:

    @staticmethod
    def register_user(data):

        validate_register_data(data)

        user = User(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            country=data["country"],
            role=UserRole.PLAYER.value,
            consent_given_at=datetime.utcnow()
        )

        user.set_password(data["password"])

        db.session.add(user)
        db.session.commit()

        claims = {"email": user.email, "role": user.role}
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=claims
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims=claims
        )

        return {"access_token": access_token, "refresh_token": refresh_token, "user_id": user.id}


    @staticmethod
    def login_user(email: str, password: str):
        user = User.query.filter_by(email=email).first()

        if not user:
            return {
                "success": False,
                "message": "Invalid credentials",
                "status": 401
            }


        # Check if user is currently blocked
        now = datetime.utcnow()

        if user.blocked_until and user.blocked_until > now:
            return {
                "success": False,
                "message": f"Too many unsuccessful login attempts.\nAccount blocked for 60 seconds.",    # 15 minutes by specification
                "status": 403
            }

        # Check password
        if not user.check_password(password):
            user.failed_login_attempts += 1

            if user.failed_login_attempts >= 3:
                user.blocked_until = now + timedelta(minutes=1)
                user.failed_login_attempts = 0

            db.session.commit()

            return {
                "success": False,
                "message": "Invalid credentials",
                "status": 401
            }

        # Successful login
        user.failed_login_attempts = 0
        user.blocked_until = None
        db.session.commit()

        claims = {"email": user.email, "role": user.role}
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=claims
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims=claims
        )

        return {
            "success": True,
            "message": "Login successful",
            "data": {"access_token": access_token, "refresh_token": refresh_token},
            "user_id": user.id,
            "status": 200
        }
