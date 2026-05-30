from datetime import datetime, timedelta
from threading import Lock

class QuizExecutionCache:   # In memory cache for active quiz executions - we don't communicate with DB while quiz is played

    _lock = Lock()
    _active_quizzes = {}

    @classmethod
    def start_quiz(cls, attempt_id, quiz, questions, answers, player_id):  # cls - Class itself (like 'this' in C#)
        with cls._lock:
            cls._active_quizzes[attempt_id] = {
                "player_id": player_id,
                "quiz": quiz,
                "started_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(seconds=quiz["duration_seconds"]),
                "questions": questions,
                "answers": answers,
                "player_answers": {}
            }

    @classmethod
    def get_quiz(cls, attempt_id):
        return cls._active_quizzes.get(attempt_id)

    @classmethod
    def save_answer(cls, attempt_id, question_id, answer_ids):
        with cls._lock:
            quiz = cls._active_quizzes.get(attempt_id)
            if not quiz:
                return False

            quiz["player_answers"][question_id] = answer_ids
            return True

    @classmethod
    def is_expired(cls, attempt_id):
        quiz = cls._active_quizzes.get(attempt_id)
        if not quiz:
            return True

        return datetime.utcnow() > quiz["expires_at"]

    @classmethod
    def has_active_attempt(cls, player_id: int, quiz_id: int) -> bool:
        with cls._lock:
            return any(
                session["player_id"] == player_id and session["quiz"]["quiz_id"] == quiz_id
                for session in cls._active_quizzes.values()
            )

    @classmethod
    def finish_quiz(cls, attempt_id):
        with cls._lock:
            return cls._active_quizzes.pop(attempt_id, None)

    @classmethod
    def cleanup_expired(cls):
        now = datetime.utcnow()
        with cls._lock:
            expired = [
                attempt_id
                for attempt_id, quiz in cls._active_quizzes.items() # Iterating over dictionary (key, value) = (attempt_id, quiz)
                if quiz["expires_at"] < now
            ]
            for attempt_id in expired:                  # Doing like this because we can't modify dictionary while iterating over it
                cls._active_quizzes.pop(attempt_id)