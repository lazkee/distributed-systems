from sqlalchemy import desc
from app.extensions import db
from app.models.quizzes import Quiz
from app.models.questions import Question
from app.models.answers import Answer
from typing import Dict
from app.constants.quiz_status import QuizStatus

class QuizService:
    @staticmethod
    def quiz_to_dto(quiz: Quiz):
        return {
            "id": quiz.quiz_id,   
            "title": quiz.title,
            "duration_seconds": quiz.duration_seconds,
            "author_id": quiz.author_id,
            "status": quiz.status,
            "questions": [
                {
                    "id": q.question_id,        
                    "text": q.question_text,   
                    "points": q.points,
                    "answers": [
                        {
                            "id": a.answer_id,        
                            "text": a.answer_text,   
                            "is_correct": a.is_correct
                        } for a in q.answers
                    ]
                } for q in quiz.questions
            ]
        }


    @staticmethod
    def get_quiz(quiz_id: int):
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            raise ValueError("Quiz not found")

        if quiz.status != "approved":
            raise ValueError("Quiz is not available")

        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        if not questions:
            raise ValueError("Quiz has no questions")

        question_list = []
        for q in questions:
            answers = Answer.query.filter_by(question_id=q.question_id).all()
            answer_list = [
                {"answer_id": a.answer_id, "text": a.answer_text}
                for a in answers
            ]
            question_list.append({
                "question_id": q.question_id,
                "text": q.question_text,
                "points": q.points,
                "answers": answer_list
            })

        return {
            "quiz_id": quiz.quiz_id,
            "title": quiz.title,
            "duration_seconds": quiz.duration_seconds,
            "questions": question_list
        }


    @staticmethod
    def validate_approved_quiz_ids(quiz_ids: list) -> None:
        if not quiz_ids or not isinstance(quiz_ids, list):
            raise ValueError("quiz_ids must be a non-empty list")

        try:
            int_ids = [int(qid) for qid in quiz_ids]
        except (TypeError, ValueError):
            raise ValueError("quiz_ids must be a list of integers")

        found = Quiz.query.filter(Quiz.quiz_id.in_(int_ids)).all()

        found_ids = {q.quiz_id for q in found}
        if set(int_ids) - found_ids:
            raise ValueError("One or more quiz IDs do not exist")

        non_approved = [q for q in found if q.status != QuizStatus.APPROVED.value]
        if non_approved:
            raise ValueError("Reports can only be generated for approved quizzes")


    @staticmethod
    def get_quiz_titles(quiz_ids:list[str]) -> list[Dict[str, str]]:
        quizzes = Quiz.query.filter(Quiz.quiz_id.in_(quiz_ids)).all()
        return [{"id": q.quiz_id, "title": q.title} for q in quizzes]


    @staticmethod
    def get_catalog(page: int = 1, page_size: int = 12) -> dict:
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 12

        page_size = min(page_size, 50)

        query = (
            Quiz.query
            .filter(Quiz.status == QuizStatus.APPROVED.value)
            .order_by(desc(Quiz.created_at))
        )
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        items = [
            {
                "id": q.quiz_id,
                "title": q.title,
                "duration_seconds": q.duration_seconds,
                "created_at": q.created_at.isoformat() if q.created_at else None,
                "author_id": q.author_id
            }
            for q in pagination.items
        ]

        return {
            "items": items,
            "page": pagination.page,
            "page_size": pagination.per_page,
            "total_items": pagination.total,
            "total_pages": pagination.pages,
        }