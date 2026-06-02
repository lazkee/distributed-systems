"""
Ownership tests for QuizExecutionService.

Proves that one player cannot submit answers or finish another player's
active quiz attempt, and that rejected operations leave the cache unchanged.

"""
import sys
import os
import types
import importlib.util
from datetime import datetime, timedelta
from enum import Enum
from unittest.mock import MagicMock, patch

import pytest


_BASE = os.path.join(os.path.dirname(__file__), "..")


def _load_real_module(dotted_name: str, rel_path: str):
    """Load a real source file into sys.modules under *dotted_name*."""
    full_path = os.path.join(_BASE, rel_path)
    spec = importlib.util.spec_from_file_location(dotted_name, full_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[dotted_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _install_stubs() -> None:
    
    sys.modules.setdefault("app", types.ModuleType("app"))

    if "app.extensions" not in sys.modules:
        ext = types.ModuleType("app.extensions")
        ext.db = MagicMock()
        ext.jwt = MagicMock()
        sys.modules["app.extensions"] = ext

    sys.modules.setdefault("app.cache", types.ModuleType("app.cache"))

    sys.modules.setdefault("app.models", types.ModuleType("app.models"))
    for dotted, class_names in [
        ("app.models.quizzes",      ["Quiz"]),
        ("app.models.questions",    ["Question"]),
        ("app.models.answers",      ["Answer"]),
        ("app.models.quiz_attempts", ["QuizAttempt"]),
    ]:
        if dotted not in sys.modules:
            mod = types.ModuleType(dotted)
            for name in class_names:
                setattr(mod, name, MagicMock())
            sys.modules[dotted] = mod

    sys.modules.setdefault("app.constants", types.ModuleType("app.constants"))
    if "app.constants.attempt_status" not in sys.modules:
        class AttemptStatus(Enum):
            IN_PROGRESS = "in_progress"
            PROCESSED   = "processed"
        mod = types.ModuleType("app.constants.attempt_status")
        mod.AttemptStatus = AttemptStatus
        sys.modules["app.constants.attempt_status"] = mod

    sys.modules.setdefault("app.services", types.ModuleType("app.services"))
    if "app.services.quiz_mail_service" not in sys.modules:
        mod = types.ModuleType("app.services.quiz_mail_service")
        mod.QuizMailService = MagicMock()
        sys.modules["app.services.quiz_mail_service"] = mod


_install_stubs()

_cache_mod   = _load_real_module(
    "app.cache.quiz_execution_cache",
    "app/cache/quiz_execution_cache.py",
)
_service_mod = _load_real_module(
    "app.services.quiz_execution_service",
    "app/services/quiz_execution_service.py",
)

QuizExecutionCache   = _cache_mod.QuizExecutionCache
QuizExecutionService = _service_mod.QuizExecutionService

_QuizAttemptMock = sys.modules["app.models.quiz_attempts"].QuizAttempt

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ATTEMPT_ID  = 42
OWNER_ID    = 1
INTRUDER_ID = 2


def _seed_cache(expires_in: int = 300) -> None:
    """Insert a minimal active attempt owned by OWNER_ID."""
    QuizExecutionCache._active_quizzes[ATTEMPT_ID] = {
        "player_id":     OWNER_ID,
        "quiz":          {"quiz_id": 7, "title": "Demo Quiz", "duration_seconds": expires_in},
        "started_at":    datetime.utcnow(),
        "expires_at":    datetime.utcnow() + timedelta(seconds=expires_in),
        "questions":     [{"question_id": 10, "points": 5, "text": "Q1"}],
        "answers":       [{"answer_id": 100, "question_id": 10, "is_correct": True, "text": "A1"}],
        "player_answers": {},
    }


@pytest.fixture(autouse=True)
def isolated_cache():
    """Each test starts and ends with an empty cache."""
    QuizExecutionCache._active_quizzes.clear()
    yield
    QuizExecutionCache._active_quizzes.clear()


# ---------------------------------------------------------------------------
# submit_answer — ownership checks
# ---------------------------------------------------------------------------

class TestSubmitAnswerOwnership:

    def test_wrong_player_raises_permission_error(self):
        _seed_cache()
        with pytest.raises(PermissionError):
            QuizExecutionService.submit_answer(
                attempt_id=ATTEMPT_ID,
                question_id=10,
                answer_ids=[100],
                player_id=INTRUDER_ID,
            )

    def test_wrong_player_does_not_record_any_answer(self):
        _seed_cache()
        before = dict(QuizExecutionCache._active_quizzes[ATTEMPT_ID]["player_answers"])

        with pytest.raises(PermissionError):
            QuizExecutionService.submit_answer(
                attempt_id=ATTEMPT_ID,
                question_id=10,
                answer_ids=[100],
                player_id=INTRUDER_ID,
            )

        assert QuizExecutionCache._active_quizzes[ATTEMPT_ID]["player_answers"] == before

    def test_correct_player_can_submit(self):
        """Positive control: owner clears the ownership check."""
        _seed_cache()
        result = QuizExecutionService.submit_answer(
            attempt_id=ATTEMPT_ID,
            question_id=10,
            answer_ids=[100],
            player_id=OWNER_ID,
        )
        assert result["attempt_id"] == ATTEMPT_ID
        assert result["question_id"] == 10
        assert QuizExecutionCache._active_quizzes[ATTEMPT_ID]["player_answers"][10] == [100]


# ---------------------------------------------------------------------------
# finish_quiz — ownership checks
# ---------------------------------------------------------------------------

class TestFinishQuizOwnership:

    def test_wrong_player_raises_permission_error(self):
        _seed_cache()
        with pytest.raises(PermissionError):
            QuizExecutionService.finish_quiz(
                attempt_id=ATTEMPT_ID,
                user_email="intruder@example.com",
                player_id=INTRUDER_ID,
            )

    def test_wrong_player_does_not_pop_attempt_from_cache(self):
        _seed_cache()
        with pytest.raises(PermissionError):
            QuizExecutionService.finish_quiz(
                attempt_id=ATTEMPT_ID,
                user_email="intruder@example.com",
                player_id=INTRUDER_ID,
            )
        assert ATTEMPT_ID in QuizExecutionCache._active_quizzes

    def test_wrong_player_does_not_mutate_cached_state(self):
        _seed_cache()
        snapshot = {
            "player_id":     QuizExecutionCache._active_quizzes[ATTEMPT_ID]["player_id"],
            "player_answers": dict(QuizExecutionCache._active_quizzes[ATTEMPT_ID]["player_answers"]),
        }
        with pytest.raises(PermissionError):
            QuizExecutionService.finish_quiz(
                attempt_id=ATTEMPT_ID,
                user_email="intruder@example.com",
                player_id=INTRUDER_ID,
            )
        entry = QuizExecutionCache._active_quizzes[ATTEMPT_ID]
        assert entry["player_id"] == snapshot["player_id"]
        assert entry["player_answers"] == snapshot["player_answers"]

    @patch("time.sleep")
    def test_correct_player_can_finish(self, _sleep):
        """Positive control: owner clears ownership check and completes."""
        _seed_cache()

        mock_attempt = MagicMock()
        mock_attempt.started_at = datetime.utcnow() - timedelta(seconds=10)
        _QuizAttemptMock.query.get.return_value = mock_attempt

        result = QuizExecutionService.finish_quiz(
            attempt_id=ATTEMPT_ID,
            user_email="owner@example.com",
            player_id=OWNER_ID,
        )

        assert result["attempt_id"] == ATTEMPT_ID
        # Cache entry must be removed after a successful finish
        assert ATTEMPT_ID not in QuizExecutionCache._active_quizzes

