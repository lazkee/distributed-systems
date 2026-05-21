import requests
from app.config import Config
from app.utils.internal_headers import make_internal_headers

class QuizService:
    @staticmethod
    def get_approved_quizzes_from_quizService():
        url = f"{Config.QUIZ_SERVICE_BASE_URL}/quiz/getApproved"
        res = requests.get(url, headers=make_internal_headers())
        res.raise_for_status()
        return res.json()

    @staticmethod
    def get_pending_quizzes_from_quizService():
        url = f"{Config.QUIZ_SERVICE_BASE_URL}/quiz/getPending"
        res = requests.get(url, headers=make_internal_headers())
        res.raise_for_status()
        return res.json()

    @staticmethod
    def get_catalog_from_quizService(page: int = 1, page_size: int = 12):
        url = f"{Config.QUIZ_SERVICE_BASE_URL}/quiz/catalog"
        res = requests.get(url, params={"page": page, "page_size": page_size}, headers=make_internal_headers())
        res.raise_for_status()
        return res.json()