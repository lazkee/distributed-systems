from app.extensions import db
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

from app.constants.user_roles import UserRole

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)

    country = db.Column(db.String(100), nullable=False)
    street = db.Column(db.String(100), nullable=False)
    street_number = db.Column(db.String(20), nullable=False)

    role = db.Column(db.String(20), default=UserRole.PLAYER.value)  # Player | Moderator | Admin

    failed_login_attempts = db.Column(db.Integer, default=0)
    blocked_until = db.Column(db.DateTime, nullable=True)

    profile_picture_url = db.Column(db.String(500), nullable=True)
    profile_picture_public_id = db.Column(db.String(255), nullable=True)

    consent_given_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self): #this is something like ToString
        return f"<User {self.email}>"
    
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
