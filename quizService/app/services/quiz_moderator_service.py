from app.extensions import db
from app.models.quizzes import Quiz
from app.models.questions import Question
from app.models.answers import Answer
from typing import Dict
from app.constants.quiz_status import QuizStatus
from app.services.quiz_service import QuizService
from app.utils.sanitize_text import sanitize_text

class QuizModeratorService:
    @staticmethod
    def create_quiz(data):
        try:
            quiz = Quiz(
                title=sanitize_text(data["title"]),
                duration_seconds=data["duration"],
                author_id=data["author_id"],
                status=QuizStatus.PENDING.value,
            )

            db.session.add(quiz)
            db.session.flush()

            for q in data["questions"]:
                question = Question(
                    quiz_id=quiz.quiz_id,
                    question_text=sanitize_text(q["text"]),
                    points=q["points"],
                )
                db.session.add(question)
                db.session.flush()

                for a in q["answers"]:
                    answer = Answer(
                        question_id=question.question_id,
                        answer_text=sanitize_text(a["text"]),
                        is_correct=a["is_correct"],
                    )
                    db.session.add(answer)

            db.session.commit()

            return {
                "quiz_id": quiz.quiz_id,
                "title": quiz.title,
                "author_id": quiz.author_id,
                "status": quiz.status
            }

        except Exception as e:
            db.session.rollback()
            raise e


    @staticmethod
    def get_by_author(author_id: int) -> list[Dict]:
        quizzes = Quiz.query.filter(Quiz.author_id == author_id).all()
        return [
            {
                "id": q.quiz_id,
                "title": q.title,
                "status": q.status,
                "duration_seconds": q.duration_seconds,
                "created_at": q.created_at.strftime("%d/%m/%y %H:%M:%S"),
            }
            for q in quizzes
        ]


    @staticmethod
    def get_rejected_quiz_for_edit(quiz_id: int, requester_id: int) -> Dict:
        quiz = Quiz.query.get(quiz_id)

        if not quiz:
            raise ValueError("Quiz not found")

        if quiz.status != QuizStatus.REJECTED.value:
            raise ValueError("Quiz is not rejected and cannot be edited")

        if quiz.author_id != requester_id:
            raise PermissionError("Access forbidden")

        dto = QuizService.quiz_to_dto(quiz)
        dto["admin_comment"] = quiz.rejection_reason

        return dto


    @staticmethod
    def edit_quiz(quiz_id: int, data: Dict, requester_id: int) -> Dict:
        quiz = Quiz.query.get(quiz_id)

        if not quiz:
            raise ValueError("Quiz not found")

        if quiz.status != QuizStatus.REJECTED.value:
            raise ValueError("Only rejected quizzes can be edited")

        if quiz.author_id != requester_id:
            raise PermissionError("Access forbidden")

        quiz.title = sanitize_text(data.get("title", quiz.title))
        quiz.duration_seconds = data.get("duration", quiz.duration_seconds)

        for q_data in data.get("questions", []):
            qid = q_data.get("question_id")

            if qid:
                # Update existing question
                question = Question.query.get(qid)
                if not question:
                    db.session.rollback()
                    raise ValueError("Question not found")
                if question.quiz_id != quiz_id:
                    db.session.rollback()
                    raise ValueError("Question does not belong to this quiz")
                question.question_text = sanitize_text(q_data["text"])
                question.points = q_data["points"]
            else:
                # Create new question
                question = Question(
                    quiz_id=quiz_id,
                    question_text=sanitize_text(q_data["text"]),
                    points=q_data["points"],
                )
                db.session.add(question)
                db.session.flush()  # get question_id before processing its answers

            for a_data in q_data.get("answers", []):
                aid = a_data.get("answer_id")

                if aid:
                    # Update existing answer
                    answer = Answer.query.get(aid)
                    if not answer:
                        db.session.rollback()
                        raise ValueError("Answer not found")
                    if answer.question_id != question.question_id:
                        db.session.rollback()
                        raise ValueError("Answer does not belong to this question")
                    answer.answer_text = sanitize_text(a_data["text"])
                    answer.is_correct = a_data["is_correct"]
                else:
                    # Create new answer
                    answer = Answer(
                        question_id=question.question_id,
                        answer_text=sanitize_text(a_data["text"]),
                        is_correct=a_data["is_correct"],
                    )
                    db.session.add(answer)

        quiz.status = QuizStatus.PENDING.value
        quiz.rejection_reason = None

        db.session.commit()

        return {
            "quiz_id": quiz.quiz_id,
            "status": quiz.status
        }