from app.models.quiz_attempts import QuizAttempt
from app.constants.attempt_status import AttemptStatus

class AttemptsService:
    @staticmethod
    def get_attempts_for_quizzes(quiz_ids: list[str]) -> list[dict]:
        attempts = (
            QuizAttempt.query
            .filter(
                QuizAttempt.quiz_id.in_(quiz_ids),
                QuizAttempt.status == AttemptStatus.PROCESSED.value
            )
            .order_by(
                QuizAttempt.score.desc(),
                QuizAttempt.time_taken_seconds.asc()
            )
            .all()
        )

        return [
            {
                "quiz_id": attempt.quiz_id,
                "player_id": attempt.player_id,
                "started_at": attempt.started_at.strftime("%Y-%m-%d %H:%M:%S"),
                "finished_at": attempt.finished_at.strftime("%Y-%m-%d %H:%M:%S"),
                "score": attempt.score,
                "time_taken_seconds": attempt.time_taken_seconds,
            }
            for attempt in attempts
        ]

    @staticmethod
    def get_attempts_for_user_export(user_id: int) -> list[dict]:
        attempts = (
            QuizAttempt.query
            .filter(QuizAttempt.player_id == user_id)
            .order_by(QuizAttempt.started_at.desc())
            .all()
        )
        return [
            {
                "attempt_id": a.attempt_id,
                "quiz_id": a.quiz_id,
                "started_at": a.started_at.isoformat() if a.started_at else None,
                "finished_at": a.finished_at.isoformat() if a.finished_at else None,
                "score": a.score,
                "time_taken_seconds": a.time_taken_seconds,
                "status": a.status,
            }
            for a in attempts
        ]

    @staticmethod
    def get_player_ids_for_quizzes(quiz_ids: list[int]) -> list[int]:
        rows = (
            QuizAttempt.query
            .filter(
                QuizAttempt.quiz_id.in_(quiz_ids),
                QuizAttempt.status == AttemptStatus.PROCESSED.value
            )
            .with_entities(QuizAttempt.player_id)
            .distinct()
            .all()
        )
        return [row.player_id for row in rows]
