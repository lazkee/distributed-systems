from dotenv import load_dotenv
import os

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


class Config:
    SECRET_KEY = _require("SECRET_KEY")

    DATABASE_URL = _require("DATABASE_URL")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    JWT_SECRET_KEY = _require("JWT_SECRET_KEY")
    SERVER_URL = _require("SERVER_URL")
    INTERNAL_SERVICE_SECRET = _require("INTERNAL_SERVICE_SECRET")

    MAILJET_API_KEY = os.getenv("MAILJET_API_KEY")
    MAILJET_SECRET_KEY = os.getenv("MAILJET_SECRET_KEY")
    MAILJET_FROM_EMAIL = os.getenv("MAILJET_FROM_EMAIL")
    MAILJET_FROM_NAME = os.getenv("MAILJET_FROM_NAME")
    MAILJET_URL = os.getenv("MAILJET_URL")
