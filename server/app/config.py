import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set")

    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY is not set")

    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    QUIZ_SERVICE_BASE_URL = os.getenv("QUIZ_SERVICE_BASE_URL")
    if not QUIZ_SERVICE_BASE_URL:
        raise RuntimeError("QUIZ_SERVICE_BASE_URL is not set")

    MAILJET_API_KEY = os.getenv("MAILJET_API_KEY")
    MAILJET_SECRET_KEY = os.getenv("MAILJET_SECRET_KEY")
    MAILJET_FROM_EMAIL = os.getenv("MAILJET_FROM_EMAIL")
    MAILJET_FROM_NAME = os.getenv("MAILJET_FROM_NAME")
    MAILJET_URL = os.getenv("MAILJET_URL")

    INTERNAL_SERVICE_SECRET = os.getenv("INTERNAL_SERVICE_SECRET")
    if not INTERNAL_SERVICE_SECRET:
        raise RuntimeError("INTERNAL_SERVICE_SECRET is not set")

    REDIS_URL = os.getenv("REDIS_URL")
    if not REDIS_URL:
        raise RuntimeError("REDIS_URL is not set")

    FRONTEND_ORIGINS_RAW = os.getenv("FRONTEND_ORIGINS")
    if not FRONTEND_ORIGINS_RAW:
        raise RuntimeError("FRONTEND_ORIGINS is not set")

    FRONTEND_ORIGINS = [
        origin.strip()
        for origin in FRONTEND_ORIGINS_RAW.split(",")
        if origin.strip()
    ]

    if not FRONTEND_ORIGINS:
        raise RuntimeError("FRONTEND_ORIGINS is not set")