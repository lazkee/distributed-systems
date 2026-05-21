from app.extensions import db
from app.models.quizzes import Quiz
from typing import Dict
from app.constants.quiz_status import QuizStatus
from app.services.quiz_service import QuizService

class QuizAdminService:
    @staticmethod
    def get_quiz_for_admin(quiz_id: int) -> Dict:
        quiz = Quiz.query.get(quiz_id)

        if not quiz:
            raise ValueError("Quiz not found")

        return QuizService.quiz_to_dto(quiz)


    @staticmethod
    def get_approved() -> list[Dict]:
        quizzes = Quiz.query.filter(Quiz.status == QuizStatus.APPROVED.value).all()
        return [{"id": q.quiz_id, "title": q.title, "author_id": q.author_id, "duration_seconds": q.duration_seconds, "created_at": q.created_at.strftime("%d/%m/%y %H:%M:%S")} for q in quizzes]


    @staticmethod
    def get_pending() -> list[Dict]:
        quizzes = Quiz.query.filter(Quiz.status == QuizStatus.PENDING.value).all()
        return [{"id": q.quiz_id, "title": q.title, "author_id": q.author_id, "duration_seconds": q.duration_seconds, "created_at": q.created_at.strftime("%d/%m/%y %H:%M:%S")} for q in quizzes]    


    @staticmethod
    def approve_quiz(quiz_id):
        quiz = Quiz.query.get(quiz_id)

        if not quiz:
            raise ValueError("Quiz not found")

        quiz.status = QuizStatus.APPROVED.value

        db.session.commit()

        return {
        "id": quiz.quiz_id,
        "status": quiz.status
        }


    @staticmethod
    def reject_quiz(quiz_id, comment):
        quiz = Quiz.query.get(quiz_id)

        if not quiz:
            raise ValueError("Quiz not found")

        quiz.status = QuizStatus.REJECTED.value
        quiz.rejection_reason = comment

        db.session.commit()

        return {
            "id": quiz.quiz_id,
            "status": quiz.status,
            "admin_comment": quiz.rejection_reason,
            "author_id": quiz.author_id
        }


    @staticmethod
    def delete_quiz(quiz_id: int, requester_id: int, is_admin: bool):
        quiz = Quiz.query.get(quiz_id)

        if not quiz:
            return {
                "success": False,
                "message": "Quiz not found"
            }

        if not is_admin and quiz.author_id != requester_id:
            raise PermissionError("Access forbidden")

        db.session.delete(quiz)
        db.session.commit()

        return {
            "success": True,
            "message": "Quiz deleted successfully",
            "quiz_id": quiz_id
        }