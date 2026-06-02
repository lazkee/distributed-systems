"""
Security tests for server/app/middlewares/require_role.py.

Proves that the decorator:
  1. Rejects missing/invalid JWTs with 401; body contains no token,
     stack traces, or internal exception details.
  2. Blocks authenticated users whose role is not in the allowed set (403);
     the protected route body is never executed.
  3. Passes authenticated users whose role IS in the allowed set (200);
     route body is executed exactly once.
  4. Supports multiple allowed roles; only exact enum-value matches pass.
  5. Treats a token with no role claim as forbidden (403).
  6. Treats tampered/unknown role values as forbidden (403).
  7. Key route functions carry the expected require_role allowed sets,
     verified via closure inspection without executing route bodies or
     calling any external service.

No real database, no Redis, no quizService calls, no Flask app startup
beyond the minimal test app defined here.
"""
import sys
import os
import types
import importlib.util
from unittest.mock import MagicMock

import pytest
from flask import Flask, jsonify

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

_SERVER_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _load_real_module(dotted_name: str, rel_path: str):
    """Load a source file as a real module, registered in sys.modules."""
    full_path = os.path.join(_SERVER_ROOT, rel_path)
    spec = importlib.util.spec_from_file_location(dotted_name, full_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[dotted_name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# sys.modules stubs
# Defensive: idempotent regardless of which test file is collected first.
# ---------------------------------------------------------------------------

def _ensure_pkg(dotted: str) -> types.ModuleType:
    """Return (creating if absent) a package stub with __path__ set."""
    if dotted not in sys.modules:
        sys.modules[dotted] = types.ModuleType(dotted)
    m = sys.modules[dotted]
    if not hasattr(m, "__path__"):
        m.__path__ = []
    return m


def _install_stubs() -> None:
    # ── top-level app package ────────────────────────────────────────────
    _ensure_pkg("app")

    # ── app.constants + real UserRole ────────────────────────────────────
    _ensure_pkg("app.constants")
    if "app.constants.user_roles" not in sys.modules:
        _load_real_module("app.constants.user_roles", "app/constants/user_roles.py")

    # ── flask_jwt_extended ───────────────────────────────────────────────
    # Stub only if not yet importable; the real library is also fine since
    # we patch require_role's module-level names per-test anyway.
    if "flask_jwt_extended" not in sys.modules:
        fjwt = types.ModuleType("flask_jwt_extended")
        fjwt.verify_jwt_in_request = MagicMock()
        fjwt.get_jwt = MagicMock(return_value={})
        fjwt.get_jwt_identity = MagicMock(return_value="1")
        fjwt.jwt_required = lambda fn: fn
        sys.modules["flask_jwt_extended"] = fjwt

    # ── app.middlewares ──────────────────────────────────────────────────
    _ensure_pkg("app.middlewares")
    if "app.middlewares.require_auth" not in sys.modules:
        ra = types.ModuleType("app.middlewares.require_auth")
        ra.require_auth = lambda fn: fn          # pass-through for route loading
        sys.modules["app.middlewares.require_auth"] = ra
    elif not hasattr(sys.modules["app.middlewares.require_auth"], "require_auth"):
        sys.modules["app.middlewares.require_auth"].require_auth = lambda fn: fn

    # ── app.extensions ───────────────────────────────────────────────────
    if "app.extensions" not in sys.modules:
        sys.modules["app.extensions"] = types.ModuleType("app.extensions")
    ext = sys.modules["app.extensions"]
    for _attr in ("db", "jwt", "socketio"):
        if not hasattr(ext, _attr):
            setattr(ext, _attr, MagicMock())

    # ── app.config ───────────────────────────────────────────────────────
    if "app.config" not in sys.modules:
        cfg_mod = types.ModuleType("app.config")
        class _Config:
            REDIS_URL = "redis://fake:6379/0"
            QUIZ_SERVICE_BASE_URL = "http://fake-quiz:5000"
        cfg_mod.Config = _Config
        sys.modules["app.config"] = cfg_mod

    # ── app.models ───────────────────────────────────────────────────────
    _ensure_pkg("app.models")
    if "app.models.user" not in sys.modules:
        um = types.ModuleType("app.models.user")
        um.User = MagicMock()
        sys.modules["app.models.user"] = um

    # ── app.utils ────────────────────────────────────────────────────────
    _ensure_pkg("app.utils")
    if "app.utils.internal_headers" not in sys.modules:
        hdr = types.ModuleType("app.utils.internal_headers")
        hdr.make_internal_headers = MagicMock(return_value={})
        sys.modules["app.utils.internal_headers"] = hdr
    elif not hasattr(sys.modules["app.utils.internal_headers"], "make_internal_headers"):
        sys.modules["app.utils.internal_headers"].make_internal_headers = MagicMock(return_value={})

    # ── app.services ─────────────────────────────────────────────────────
    _ensure_pkg("app.services")
    for _full, _cls in [
        ("app.services.quiz_service", "QuizService"),
        ("app.services.user_service", "UserService"),
        ("app.services.mail_service", "MailService"),
    ]:
        if _full not in sys.modules:
            _m = types.ModuleType(_full)
            setattr(_m, _cls, MagicMock())
            sys.modules[_full] = _m
        elif not hasattr(sys.modules[_full], _cls):
            setattr(sys.modules[_full], _cls, MagicMock())

    # ── app.cache ────────────────────────────────────────────────────────
    _ensure_pkg("app.cache")
    if "app.cache.quiz_cache" not in sys.modules:
        qc = types.ModuleType("app.cache.quiz_cache")
        qc.QuizCache = MagicMock()
        sys.modules["app.cache.quiz_cache"] = qc
    elif not hasattr(sys.modules["app.cache.quiz_cache"], "QuizCache"):
        sys.modules["app.cache.quiz_cache"].QuizCache = MagicMock()

    # ── app.logging_config ───────────────────────────────────────────────
    if "app.logging_config" not in sys.modules:
        lc = types.ModuleType("app.logging_config")
        lc.audit_log = MagicMock()
        lc.get_request_ip = MagicMock(return_value="127.0.0.1")
        sys.modules["app.logging_config"] = lc
    else:
        lc = sys.modules["app.logging_config"]
        if not hasattr(lc, "audit_log"):
            lc.audit_log = MagicMock()
        if not hasattr(lc, "get_request_ip"):
            lc.get_request_ip = MagicMock(return_value="127.0.0.1")

    # ── requests ─────────────────────────────────────────────────────────
    # requests is installed in the project venv; stub only if absent.
    if "requests" not in sys.modules:
        req = types.ModuleType("requests")
        for _fn in ("get", "post", "put", "delete"):
            setattr(req, _fn, MagicMock())
        req.RequestException = Exception
        req_exc = types.ModuleType("requests.exceptions")
        req_exc.RequestException = Exception
        req.exceptions = req_exc
        sys.modules["requests"] = req
        sys.modules["requests.exceptions"] = req_exc


_install_stubs()

# ---------------------------------------------------------------------------
# Load the real modules under test
# ---------------------------------------------------------------------------

_rr_mod = _load_real_module(
    "app.middlewares.require_role",
    "app/middlewares/require_role.py",
)
sys.modules["app.middlewares"].require_role = _rr_mod

_quiz_routes_mod = _load_real_module(
    "app.routes.quiz",
    "app/routes/quiz.py",
)

_quiz_exec_mod = _load_real_module(
    "app.routes.quiz_execution",
    "app/routes/quiz_execution.py",
)

# Stable references
require_role = _rr_mod.require_role
UserRole = sys.modules["app.constants.user_roles"].UserRole

# ---------------------------------------------------------------------------
# Minimal Flask test application
# ---------------------------------------------------------------------------

_test_app = Flask(__name__)
_test_app.config["TESTING"] = True

_route_hit_counter: dict = {}


@_test_app.route("/admin-only")
@require_role([UserRole.ADMIN])
def _admin_only():
    _route_hit_counter["admin_only"] = _route_hit_counter.get("admin_only", 0) + 1
    return jsonify({"ok": True}), 200


@_test_app.route("/multi-role")
@require_role([UserRole.ADMIN, UserRole.MODERATOR])
def _multi_role():
    _route_hit_counter["multi_role"] = _route_hit_counter.get("multi_role", 0) + 1
    return jsonify({"ok": True}), 200


_client = _test_app.test_client()

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    """Fresh MagicMocks and zero hit counters before every test."""
    _route_hit_counter.clear()
    monkeypatch.setattr(_rr_mod, "verify_jwt_in_request", MagicMock())
    monkeypatch.setattr(_rr_mod, "get_jwt", MagicMock(return_value={}))
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stub_jwt(role=None, fail=False):
    """Configure the stubs that require_role reads at call time."""
    if fail:
        _rr_mod.verify_jwt_in_request.side_effect = Exception("token invalid")
    else:
        _rr_mod.verify_jwt_in_request.side_effect = None
        _rr_mod.verify_jwt_in_request.return_value = None

    claims = {"role": role} if role is not None else {}
    _rr_mod.get_jwt.return_value = claims


def _get_allowed(fn):
    """Return the `allowed` set baked into a require_role-decorated function."""
    for cell in (fn.__closure__ or []):
        try:
            val = cell.cell_contents
            if isinstance(val, set):
                return val
        except ValueError:
            pass
    return None


# ---------------------------------------------------------------------------
# 1. Missing / invalid JWT → 401, no internal detail in body
# ---------------------------------------------------------------------------

class TestInvalidJwtRejected:

    def test_status_is_401(self):
        _stub_jwt(fail=True)
        assert _client.get("/admin-only").status_code == 401

    def test_body_is_json_with_success_false(self):
        _stub_jwt(fail=True)
        data = _client.get("/admin-only").get_json()
        assert data is not None
        assert data["success"] is False

    def test_body_omits_raw_exception_text(self):
        _stub_jwt(fail=True)
        text = _client.get("/admin-only").data.decode()
        # The raw exception message "token invalid" must not leak into the response
        assert "token invalid" not in text

    def test_body_has_no_stack_trace(self):
        _stub_jwt(fail=True)
        text = _client.get("/admin-only").data.decode()
        assert "Traceback" not in text
        assert "Exception" not in text

    def test_route_body_not_executed_on_401(self):
        _stub_jwt(fail=True)
        _client.get("/admin-only")
        assert _route_hit_counter.get("admin_only", 0) == 0


# ---------------------------------------------------------------------------
# 2. Authenticated user with wrong role → 403, route body not executed
# ---------------------------------------------------------------------------

class TestWrongRoleForbidden:

    def test_status_is_403(self):
        _stub_jwt(role="Player")
        assert _client.get("/admin-only").status_code == 403

    def test_body_success_is_false(self):
        _stub_jwt(role="Player")
        data = _client.get("/admin-only").get_json()
        assert data is not None
        assert data["success"] is False

    def test_route_body_not_executed_on_403(self):
        _stub_jwt(role="Player")
        _client.get("/admin-only")
        assert _route_hit_counter.get("admin_only", 0) == 0


# ---------------------------------------------------------------------------
# 3. Authenticated user with allowed role → 200, body executed once
# ---------------------------------------------------------------------------

class TestAllowedRoleReachesRoute:

    def test_status_is_200(self):
        _stub_jwt(role="Admin")
        assert _client.get("/admin-only").status_code == 200

    def test_route_body_executed_exactly_once(self):
        _stub_jwt(role="Admin")
        _client.get("/admin-only")
        assert _route_hit_counter.get("admin_only", 0) == 1


# ---------------------------------------------------------------------------
# 4. Multiple allowed roles: each allowed role passes, others do not
# ---------------------------------------------------------------------------

class TestMultipleAllowedRoles:

    def test_admin_is_allowed(self):
        _stub_jwt(role="Admin")
        assert _client.get("/multi-role").status_code == 200

    def test_moderator_is_allowed(self):
        _stub_jwt(role="Moderator")
        assert _client.get("/multi-role").status_code == 200

    def test_player_is_forbidden(self):
        _stub_jwt(role="Player")
        assert _client.get("/multi-role").status_code == 403

    def test_player_does_not_execute_body(self):
        _stub_jwt(role="Player")
        _client.get("/multi-role")
        assert _route_hit_counter.get("multi_role", 0) == 0


# ---------------------------------------------------------------------------
# 5. Token with no role claim must not be treated as authorized
# ---------------------------------------------------------------------------

class TestMissingRoleClaim:

    def test_empty_claims_is_403(self):
        _stub_jwt(role=None)   # get_jwt returns {}
        assert _client.get("/admin-only").status_code == 403

    def test_explicit_none_role_is_403(self):
        _rr_mod.verify_jwt_in_request.side_effect = None
        _rr_mod.get_jwt.return_value = {"role": None}
        assert _client.get("/admin-only").status_code == 403

    def test_missing_role_does_not_execute_body(self):
        _stub_jwt(role=None)
        _client.get("/admin-only")
        assert _route_hit_counter.get("admin_only", 0) == 0


# ---------------------------------------------------------------------------
# 6. Tampered / unknown role values are rejected
# ---------------------------------------------------------------------------

class TestTamperedRole:

    def test_superadmin_is_forbidden(self):
        _stub_jwt(role="SuperAdmin")
        assert _client.get("/admin-only").status_code == 403

    def test_lowercase_admin_is_forbidden(self):
        # Enum value is "Admin"; "admin" must not pass
        _stub_jwt(role="admin")
        assert _client.get("/admin-only").status_code == 403

    def test_empty_string_is_forbidden(self):
        _stub_jwt(role="")
        assert _client.get("/admin-only").status_code == 403

    def test_numeric_role_is_forbidden(self):
        _stub_jwt(role=1)
        assert _client.get("/admin-only").status_code == 403


# ---------------------------------------------------------------------------
# 7. Route decorator audit via closure inspection
#
# Each assertion reads the `allowed` set baked into the wrapper closure at
# decoration time.  No request is made and no external service is called.
# ---------------------------------------------------------------------------

class TestRouteDecoratorAudit:

    # ── quiz.py routes ───────────────────────────────────────────────────

    def test_create_quiz_requires_moderator(self):
        assert _get_allowed(_quiz_routes_mod.create_quiz) == {"Moderator"}

    def test_approve_quiz_requires_admin(self):
        assert _get_allowed(_quiz_routes_mod.approve_quiz) == {"Admin"}

    def test_reject_quiz_requires_admin(self):
        assert _get_allowed(_quiz_routes_mod.reject_quiz) == {"Admin"}

    def test_get_quiz_for_admin_requires_admin(self):
        assert _get_allowed(_quiz_routes_mod.get_quiz_for_admin) == {"Admin"}

    def test_delete_quiz_requires_admin_or_moderator(self):
        assert _get_allowed(_quiz_routes_mod.delete_quiz) == {"Admin", "Moderator"}

    # ── quiz_execution.py routes ─────────────────────────────────────────

    def test_start_quiz_requires_player(self):
        assert _get_allowed(_quiz_exec_mod.start_quiz) == {"Player"}

    def test_submit_answer_requires_player(self):
        assert _get_allowed(_quiz_exec_mod.submit_answer) == {"Player"}

    def test_finish_quiz_requires_player(self):
        assert _get_allowed(_quiz_exec_mod.finish_quiz) == {"Player"}
