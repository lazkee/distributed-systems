"""
Sanitization tests for quiz content.

Proves that:
  1. sanitize_text strips all HTML / script content and trims whitespace.
  2. QuizModeratorService.create_quiz sanitizes title, question_text, answer_text
     before they reach the database.
  3. QuizModeratorService.edit_quiz sanitizes every text field it touches —
     both existing (update-by-id) and newly created records.

No database, Docker, or external services are required.
The real sanitize_text.py and quiz_moderator_service.py are loaded from disk;
all app.* imports are satisfied by lightweight stubs or the real enum file.
"""
import sys
import os
import types
import importlib.util
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE = os.path.join(os.path.dirname(__file__), "..")


def _load_real_module(dotted_name: str, rel_path: str):
    full_path = os.path.join(_BASE, rel_path)
    spec = importlib.util.spec_from_file_location(dotted_name, full_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[dotted_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _ns(**kwargs):
    """Tiny namespace: kwargs become attributes, any extra attribute set later is allowed."""
    class _Obj:
        pass
    obj = _Obj()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


# ---------------------------------------------------------------------------
# Fake ORM model classes
#
# Each class records every instance created via __init__ in _created[], so
# tests can inspect the sanitized values that were actually persisted.
# A class-level `query` MagicMock supports .query.get() for edit_quiz tests.
# ---------------------------------------------------------------------------

class FakeQuiz:
    _created: list = []
    query: MagicMock = MagicMock()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if not hasattr(self, "quiz_id"):
            self.quiz_id = 1
        FakeQuiz._created.append(self)

    @classmethod
    def reset(cls):
        cls._created.clear()
        cls.query.reset_mock()


class FakeQuestion:
    _created: list = []
    query: MagicMock = MagicMock()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if not hasattr(self, "question_id"):
            self.question_id = 10
        FakeQuestion._created.append(self)

    @classmethod
    def reset(cls):
        cls._created.clear()
        cls.query.reset_mock()


class FakeAnswer:
    _created: list = []
    query: MagicMock = MagicMock()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if not hasattr(self, "answer_id"):
            self.answer_id = 100
        FakeAnswer._created.append(self)

    @classmethod
    def reset(cls):
        cls._created.clear()
        cls.query.reset_mock()


# ---------------------------------------------------------------------------
# sys.modules stubs — installed at collection time
# ---------------------------------------------------------------------------

def _install_stubs() -> None:
    sys.modules.setdefault("app", types.ModuleType("app"))

    # app.utils — load the real sanitize_text so tests exercise actual bleach logic
    sys.modules.setdefault("app.utils", types.ModuleType("app.utils"))

    # app.extensions — db is a MagicMock; session.add/flush/commit/rollback are no-ops
    if "app.extensions" not in sys.modules:
        ext = types.ModuleType("app.extensions")
        ext.db = MagicMock()
        ext.jwt = MagicMock()
        sys.modules["app.extensions"] = ext

    # app.models — swap in the fake classes so service calls capture kwargs
    sys.modules.setdefault("app.models", types.ModuleType("app.models"))
    for dotted, cls in [
        ("app.models.quizzes",   ("Quiz",    FakeQuiz)),
        ("app.models.questions", ("Question", FakeQuestion)),
        ("app.models.answers",   ("Answer",   FakeAnswer)),
    ]:
        mod = sys.modules.get(dotted) or types.ModuleType(dotted)
        setattr(mod, cls[0], cls[1])        # always set — ensures our fake class wins
        sys.modules[dotted] = mod

    # app.constants — load the real QuizStatus enum
    sys.modules.setdefault("app.constants", types.ModuleType("app.constants"))
    if "app.constants.quiz_status" not in sys.modules:
        _load_real_module("app.constants.quiz_status", "app/constants/quiz_status.py")

    # app.services.quiz_service — only used in paths we don't test here
    sys.modules.setdefault("app.services", types.ModuleType("app.services"))
    if "app.services.quiz_service" not in sys.modules:
        qs_mod = types.ModuleType("app.services.quiz_service")
        qs_mod.QuizService = MagicMock()
        sys.modules["app.services.quiz_service"] = qs_mod


_install_stubs()

# Load real modules from disk (bypasses app/__init__.py)
_sanitize_mod  = _load_real_module("app.utils.sanitize_text",           "app/utils/sanitize_text.py")
_moderator_mod = _load_real_module("app.services.quiz_moderator_service", "app/services/quiz_moderator_service.py")

sanitize_text        = _sanitize_mod.sanitize_text
QuizModeratorService = _moderator_mod.QuizModeratorService

# Stable reference to the db mock (same object the service captured at import time)
_db = sys.modules["app.extensions"].db

# Real QuizStatus for building edit_quiz fixtures
QuizStatus = sys.modules["app.constants.quiz_status"].QuizStatus

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _no_html(value: str) -> bool:
    """Return True when *value* contains no recognisable HTML markers."""
    for bad in ("<", ">", "script", "onclick"):
        if bad in value:
            return False
    return True


@pytest.fixture(autouse=True)
def reset_state():
    """Isolate each test: clear fake model state and db call history."""
    FakeQuiz.reset()
    FakeQuestion.reset()
    FakeAnswer.reset()
    _db.reset_mock()
    yield


# ---------------------------------------------------------------------------
# 1. sanitize_text unit tests
# ---------------------------------------------------------------------------

class TestSanitizeText:

    def test_script_tag_stripped(self):
        result = sanitize_text("<script>alert(1)</script>Hello")
        assert "<script>" not in result
        assert "</script>" not in result
        assert "script" not in result

    def test_bold_tag_stripped_text_preserved(self):
        result = sanitize_text("<b>Correct answer</b>")
        assert "<" not in result
        assert ">" not in result
        assert "Correct answer" in result

    def test_surrounding_whitespace_stripped(self):
        assert sanitize_text("   hello   ") == "hello"

    def test_inline_event_handler_stripped(self):
        result = sanitize_text('<button onclick="evil()">Click</button>')
        assert "onclick" not in result
        assert "<" not in result

    def test_nested_tags_stripped(self):
        result = sanitize_text("<div><p><b>text</b></p></div>")
        assert "<" not in result
        assert "text" in result

    def test_plain_text_unchanged(self):
        assert sanitize_text("No HTML here") == "No HTML here"

    def test_empty_string(self):
        assert sanitize_text("") == ""


# ---------------------------------------------------------------------------
# 2. create_quiz — sanitization of all persisted fields
# ---------------------------------------------------------------------------

DIRTY_TITLE    = "<script>steal()</script>My Quiz"
DIRTY_QUESTION = "<b>What is 2+2?</b>"
DIRTY_ANSWER   = '<span onclick="bad()">Four</span>'

CREATE_PAYLOAD = {
    "title":     DIRTY_TITLE,
    "duration":  60,
    "author_id": 1,
    "questions": [{
        "text":   DIRTY_QUESTION,
        "points": 5,
        "answers": [
            {"text": DIRTY_ANSWER,   "is_correct": True},
            {"text": "<em>Five</em>", "is_correct": False},
        ],
    }],
}


class TestCreateQuizSanitization:

    def test_quiz_title_is_sanitized(self):
        QuizModeratorService.create_quiz(CREATE_PAYLOAD)
        assert _no_html(FakeQuiz._created[0].title)

    def test_quiz_title_retains_readable_text(self):
        QuizModeratorService.create_quiz(CREATE_PAYLOAD)
        assert "My Quiz" in FakeQuiz._created[0].title

    def test_question_text_is_sanitized(self):
        QuizModeratorService.create_quiz(CREATE_PAYLOAD)
        assert _no_html(FakeQuestion._created[0].question_text)

    def test_question_text_retains_readable_text(self):
        QuizModeratorService.create_quiz(CREATE_PAYLOAD)
        assert "What is 2+2?" in FakeQuestion._created[0].question_text

    def test_answer_text_is_sanitized(self):
        QuizModeratorService.create_quiz(CREATE_PAYLOAD)
        for ans in FakeAnswer._created:
            assert _no_html(ans.answer_text)

    def test_answer_text_retains_readable_text(self):
        QuizModeratorService.create_quiz(CREATE_PAYLOAD)
        texts = [a.answer_text for a in FakeAnswer._created]
        assert any("Four" in t for t in texts)
        assert any("Five" in t for t in texts)

    def test_commit_called_once_on_success(self):
        QuizModeratorService.create_quiz(CREATE_PAYLOAD)
        assert _db.session.commit.call_count == 1

    def test_rollback_not_called_on_success(self):
        QuizModeratorService.create_quiz(CREATE_PAYLOAD)
        _db.session.rollback.assert_not_called()


# ---------------------------------------------------------------------------
# 3. edit_quiz — sanitization of all persisted fields
# ---------------------------------------------------------------------------

def _make_edit_fixtures():
    """Return pre-configured fake DB objects for a REJECTED quiz."""
    fake_quiz = _ns(
        quiz_id=7,
        title="Old Title",
        duration_seconds=60,
        author_id=99,
        status=QuizStatus.REJECTED.value,
        rejection_reason="had issues",
    )
    fake_question = _ns(
        question_id=10,
        quiz_id=7,
        question_text="Old question",
        points=5,
    )
    fake_answer = _ns(
        answer_id=100,
        question_id=10,
        answer_text="Old answer",
        is_correct=True,
    )
    FakeQuiz.query.get.return_value     = fake_quiz
    FakeQuestion.query.get.return_value = fake_question
    FakeAnswer.query.get.return_value   = fake_answer
    return fake_quiz, fake_question, fake_answer


class TestEditQuizSanitizationExistingRecords:
    """edit_quiz with update-by-id for all records."""

    EDIT_PAYLOAD = {
        "title":    "<img src=x onerror=alert(1)>Updated Title",
        "duration": 90,
        "questions": [{
            "question_id": 10,
            "text":        "<script>q()</script>Updated question",
            "points":      10,
            "answers": [{
                "answer_id": 100,
                "text":      '<a href="evil">Updated answer</a>',
                "is_correct": True,
            }],
        }],
    }

    def test_quiz_title_is_sanitized(self):
        fake_quiz, _, _ = _make_edit_fixtures()
        QuizModeratorService.edit_quiz(quiz_id=7, data=self.EDIT_PAYLOAD, requester_id=99)
        assert _no_html(fake_quiz.title)

    def test_quiz_title_retains_readable_text(self):
        fake_quiz, _, _ = _make_edit_fixtures()
        QuizModeratorService.edit_quiz(quiz_id=7, data=self.EDIT_PAYLOAD, requester_id=99)
        assert "Updated Title" in fake_quiz.title

    def test_question_text_is_sanitized(self):
        _, fake_question, _ = _make_edit_fixtures()
        QuizModeratorService.edit_quiz(quiz_id=7, data=self.EDIT_PAYLOAD, requester_id=99)
        assert _no_html(fake_question.question_text)

    def test_question_text_retains_readable_text(self):
        _, fake_question, _ = _make_edit_fixtures()
        QuizModeratorService.edit_quiz(quiz_id=7, data=self.EDIT_PAYLOAD, requester_id=99)
        assert "Updated question" in fake_question.question_text

    def test_answer_text_is_sanitized(self):
        _, _, fake_answer = _make_edit_fixtures()
        QuizModeratorService.edit_quiz(quiz_id=7, data=self.EDIT_PAYLOAD, requester_id=99)
        assert _no_html(fake_answer.answer_text)

    def test_answer_text_retains_readable_text(self):
        _, _, fake_answer = _make_edit_fixtures()
        QuizModeratorService.edit_quiz(quiz_id=7, data=self.EDIT_PAYLOAD, requester_id=99)
        assert "Updated answer" in fake_answer.answer_text

    def test_commit_called_once_on_success(self):
        _make_edit_fixtures()
        QuizModeratorService.edit_quiz(quiz_id=7, data=self.EDIT_PAYLOAD, requester_id=99)
        assert _db.session.commit.call_count == 1


class TestEditQuizSanitizationNewRecords:
    """edit_quiz with newly created question and answer (no ids supplied)."""

    NEW_RECORD_PAYLOAD = {
        "title":    "Clean Title",
        "duration": 60,
        "questions": [{
            # no question_id → service creates a new Question
            "text":   "<b>New question text</b>",
            "points": 3,
            "answers": [{
                # no answer_id → service creates a new Answer
                "text":      '<script>a()</script>New answer',
                "is_correct": False,
            }],
        }],
    }

    def test_new_question_text_is_sanitized(self):
        fake_quiz = _ns(
            quiz_id=7, title="Old", duration_seconds=60,
            author_id=99, status=QuizStatus.REJECTED.value,
            rejection_reason=None,
        )
        FakeQuiz.query.get.return_value = fake_quiz
        QuizModeratorService.edit_quiz(quiz_id=7, data=self.NEW_RECORD_PAYLOAD, requester_id=99)
        assert FakeQuestion._created, "expected a new Question to be constructed"
        assert _no_html(FakeQuestion._created[0].question_text)

    def test_new_answer_text_is_sanitized(self):
        fake_quiz = _ns(
            quiz_id=7, title="Old", duration_seconds=60,
            author_id=99, status=QuizStatus.REJECTED.value,
            rejection_reason=None,
        )
        FakeQuiz.query.get.return_value = fake_quiz
        QuizModeratorService.edit_quiz(quiz_id=7, data=self.NEW_RECORD_PAYLOAD, requester_id=99)
        assert FakeAnswer._created, "expected a new Answer to be constructed"
        assert _no_html(FakeAnswer._created[0].answer_text)

    def test_new_question_retains_readable_text(self):
        fake_quiz = _ns(
            quiz_id=7, title="Old", duration_seconds=60,
            author_id=99, status=QuizStatus.REJECTED.value,
            rejection_reason=None,
        )
        FakeQuiz.query.get.return_value = fake_quiz
        QuizModeratorService.edit_quiz(quiz_id=7, data=self.NEW_RECORD_PAYLOAD, requester_id=99)
        assert "New question text" in FakeQuestion._created[0].question_text

    def test_new_answer_retains_readable_text(self):
        fake_quiz = _ns(
            quiz_id=7, title="Old", duration_seconds=60,
            author_id=99, status=QuizStatus.REJECTED.value,
            rejection_reason=None,
        )
        FakeQuiz.query.get.return_value = fake_quiz
        QuizModeratorService.edit_quiz(quiz_id=7, data=self.NEW_RECORD_PAYLOAD, requester_id=99)
        assert "New answer" in FakeAnswer._created[0].answer_text
