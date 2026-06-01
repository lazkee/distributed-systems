from datetime import datetime
from multiprocessing import Process
import time

from app.extensions import db
from app.cache.quiz_execution_cache import QuizExecutionCache

from app.models.quizzes import Quiz
from app.models.questions import Question
from app.models.answers import Answer
from app.models.quiz_attempts import QuizAttempt
from app.constants.attempt_status import AttemptStatus
from app.services.quiz_mail_service import QuizMailService


class QuizExecutionService:

    @staticmethod
    def start_quiz(quiz_id: int, player_id: int):
        QuizExecutionCache.cleanup_expired()    # Delete useless data from cache

        if QuizExecutionCache.has_active_attempt(player_id, quiz_id):
            raise ValueError("Active attempt already exists for this quiz")

        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            raise ValueError("Quiz not found")

        if quiz.status != "approved":
            raise ValueError("Quiz is not available")

        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        if not questions:
            raise ValueError("Quiz has no questions")

        question_ids = [q.question_id for q in questions]
        answers = Answer.query.filter(Answer.question_id.in_(question_ids)).all()

        attempt = QuizAttempt(      # Create quiz attempt
            quiz_id=quiz_id,
            player_id=player_id,
            started_at=datetime.utcnow(),
            status=AttemptStatus.IN_PROGRESS.value
        )

        db.session.add(attempt)
        db.session.commit()  # We need attempt_id

        QuizExecutionCache.start_quiz(
            attempt_id=attempt.attempt_id,
            player_id=player_id,
            quiz={"quiz_id": quiz.quiz_id, "title": quiz.title, "duration_seconds": quiz.duration_seconds},
            questions=[{"question_id": q.question_id, "points": q.points, "text": q.question_text} for q in questions],
            answers=[{"answer_id": a.answer_id, "question_id": a.question_id, "is_correct": a.is_correct, "text": a.answer_text} for a in answers]
        )

        return {
            "attempt_id": attempt.attempt_id,
            "quiz_id": quiz.quiz_id,
            "duration_seconds": quiz.duration_seconds,
            "started_at": attempt.started_at
        }


    @staticmethod
    def submit_answer(attempt_id: int, question_id: int, answer_ids: list[int], player_id: int):
        session = QuizExecutionCache.get_quiz(attempt_id)
        if not session:
            raise ValueError("Quiz attempt not found or expired")

        if session["player_id"] != player_id:
            raise PermissionError("Access forbidden")

        if datetime.utcnow() > session["expires_at"]:
            QuizExecutionCache.finish_quiz(attempt_id)
            raise ValueError("Quiz time expired")

        # Validate that the question belongs to this quiz
        question_ids = [q["question_id"] for q in session["questions"]]
        if question_id not in question_ids:
            raise ValueError("Invalid question for this quiz")

        # Validate that all submitted answer IDs belong to the question
        valid_answer_ids = [a["answer_id"] for a in session["answers"] if a["question_id"] == question_id]
        invalid_ids = [a_id for a_id in answer_ids if a_id not in valid_answer_ids]
        if invalid_ids:
            raise ValueError("Invalid answer IDs submitted for this question")

        QuizExecutionCache.save_answer(attempt_id, question_id, answer_ids)

        return {
            "attempt_id": attempt_id,
            "question_id": question_id,
            "answer_ids": answer_ids,
            "answered_questions": len(session["player_answers"]),
            "total_questions": len(session["questions"])
        }


    @staticmethod
    def finish_quiz(attempt_id: int, user_email: str, player_id: int):
        # Verify ownership before any state mutation
        session_check = QuizExecutionCache.get_quiz(attempt_id)
        if not session_check:
            raise ValueError("Quiz attempt not found or expired")

        if session_check["player_id"] != player_id:
            raise PermissionError("Access forbidden")

        finished_at = datetime.utcnow()

        session = QuizExecutionCache.finish_quiz(attempt_id)
        if not session:
            raise ValueError("Quiz attempt not found or already finished")

        attempt = QuizAttempt.query.get(attempt_id)
        if not attempt:
            raise ValueError("QuizAttempt record not found in database")

        time.sleep(5)  # Simulation of long processing

        score = 0
        total_points = 0

        # Calculate total points
        for question in session["questions"]:
            total_points += question["points"]

        # Calculate score based on submitted answers
        for question in session["questions"]:
            q_id = question["question_id"]
            submitted_ids = session["player_answers"].get(q_id, [])

            correct_ids = [
                a["answer_id"] for a in session["answers"]
                if a["question_id"] == q_id and a["is_correct"]
            ]

            # Full points only if all correct answers submitted and no incorrect ones
            if set(submitted_ids) == set(correct_ids) and correct_ids:
                score += question["points"]

        attempt.finished_at = finished_at
        attempt.time_taken_seconds = int((finished_at - attempt.started_at).total_seconds())
        attempt.score = score
        attempt.status = AttemptStatus.PROCESSED.value

        db.session.commit()

        try:
            QuizMailService.send_quiz_result_email(
                user_email,
                session["quiz"]["title"],
                score,
                total_points,
                attempt.time_taken_seconds
            )
        except Exception:
            print(f"Failed to send email for attempt {attempt_id}")

        return {
            "attempt_id": attempt_id,
            "score": score,
            "total_points": total_points,
            "time_taken_seconds": attempt.time_taken_seconds
        }