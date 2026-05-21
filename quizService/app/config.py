from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:1234@localhost:3306/quiz_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key")  #Flask-JWT-Extended reads it from Flask app config automatically!
    SERVER_URL = os.getenv("SERVER_URL", "http://127.0.0.1:8000")
    MAILJET_API_KEY = os.getenv("MAILJET_API_KEY")
    MAILJET_SECRET_KEY = os.getenv("MAILJET_SECRET_KEY")
    MAILJET_FROM_EMAIL = os.getenv("MAILJET_FROM_EMAIL")
    MAILJET_FROM_NAME = os.getenv("MAILJET_FROM_NAME")
    MAILJET_URL=os.getenv("MAILJET_URL")

    INTERNAL_SERVICE_SECRET = os.getenv("INTERNAL_SERVICE_SECRET", "")
