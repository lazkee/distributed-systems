import re
from app.models.user import User

# Requires: ≥12 chars, ≥1 uppercase, ≥1 lowercase, ≥1 digit, ≥1 special char.
_PASSWORD_RE = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$'
)

_PASSWORD_POLICY_MSG = (
    "Password must be at least 12 characters and include an uppercase letter, "
    "a lowercase letter, a digit, and a special character."
)


def validate_register_data(data: dict):
    if not data.get("privacy_policy_accepted"):
        raise ValueError("You must accept the privacy policy to register.")

    if len(data["first_name"]) < 3 or len(data["first_name"]) > 20:
        raise ValueError("First name must be 3–20 characters long.")

    if len(data["last_name"]) < 3 or len(data["last_name"]) > 20:
        raise ValueError("Last name must be 3–20 characters long.")

    if not _PASSWORD_RE.match(data["password"]):
        raise ValueError(_PASSWORD_POLICY_MSG)
    
    email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    if not re.match(email_regex, data["email"]):
        raise ValueError("Invalid email format.")
    
    if User.query.filter_by(email=data["email"]).first():
        raise ValueError("Email already exists.")
