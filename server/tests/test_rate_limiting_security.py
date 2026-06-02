"""
Security tests for rate limiting on auth endpoints.

Tests 1-3 inspect production config and decorator registration to prove
the correct limits are declared without executing route bodies.
Tests 4-6 use real Flask-Limiter (in-memory storage, no Redis) with a
minimal Flask app to prove 429 responses are returned and the protected
route body is not called after the limit is exceeded.

No real database, no Redis, no quizService, no email.
"""
import os
import sys
import types
import importlib.util
from unittest.mock import MagicMock

import pytest
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ---------------------------------------------------------------------------
# Env vars required by production Config class-level guards
# ---------------------------------------------------------------------------
for _k, _v in {
    "SECRET_KEY": "test-secret",
    "DATABASE_URL": "sqlite:///:memory:",
    "JWT_SECRET_KEY": "test-jwt-secret",
    "QUIZ_SERVICE_BASE_URL": "http://fake:5000",
    "INTERNAL_SERVICE_SECRET": "test-internal-secret",
    "REDIS_URL": "redis://fake:6379/0",
    "FRONTEND_ORIGINS": "http://localhost:3000",
}.items():
    os.environ.setdefault(_k, _v)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SERVER_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _load_real_module(dotted: str, rel: str):
    path = os.path.join(_SERVER_ROOT, rel)
    spec = importlib.util.spec_from_file_location(dotted, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[dotted] = mod
    spec.loader.exec_module(mod)
    return mod


def _ensure_pkg(name: str) -> types.ModuleType:
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)
    m = sys.modules[name]
    if not hasattr(m, "__path__"):
        m.__path__ = []
    return m


# ---------------------------------------------------------------------------
# Tracking limiter — records limit strings when auth.py decorates its routes
# ---------------------------------------------------------------------------

_captured_limits: list = []


class _TrackingLimiter:
    def limit(self, value: str):
        _captured_limits.append(value)
        return lambda fn: fn   # pass-through: real route functions stay intact


_tracking_limiter = _TrackingLimiter()

# ---------------------------------------------------------------------------
# sys.modules stubs — must run before any production module import
# ---------------------------------------------------------------------------

def _install_stubs() -> None:
    _ensure_pkg("app")
    _ensure_pkg("app.constants")
    if "app.constants.user_roles" not in sys.modules:
        _load_real_module("app.constants.user_roles", "app/constants/user_roles.py")

    # app.extensions: inject the tracking limiter so auth.py captures it
    if "app.extensions" not in sys.modules:
        sys.modules["app.extensions"] = types.ModuleType("app.extensions")
    ext = sys.modules["app.extensions"]
    for _a in ("db", "jwt"):
        if not hasattr(ext, _a):
            setattr(ext, _a, MagicMock())
    if not hasattr(ext, "socketio"):
        ext.socketio = MagicMock()
        ext.socketio.on = lambda event: (lambda fn: fn)
    ext.limiter = _tracking_limiter   # always set — auth.py must see this

    # flask_jwt_extended — use the real library (installed in this venv)
    if "flask_jwt_extended" not in sys.modules:
        import flask_jwt_extended as _fjwt  # noqa: F401

    _ensure_pkg("app.models")
    if "app.models.user" not in sys.modules:
        um = types.ModuleType("app.models.user")
        um.User = MagicMock()
        sys.modules["app.models.user"] = um
    elif not hasattr(sys.modules["app.models.user"], "User"):
        sys.modules["app.models.user"].User = MagicMock()

    _ensure_pkg("app.services")
    if "app.services.auth_service" not in sys.modules:
        asvc = types.ModuleType("app.services.auth_service")
        asvc.AuthService = MagicMock()
        sys.modules["app.services.auth_service"] = asvc
    elif not hasattr(sys.modules["app.services.auth_service"], "AuthService"):
        sys.modules["app.services.auth_service"].AuthService = MagicMock()

    if "app.services.jwt_blocklist_service" not in sys.modules:
        jbl = types.ModuleType("app.services.jwt_blocklist_service")
        jbl.revoke_token = MagicMock()
        sys.modules["app.services.jwt_blocklist_service"] = jbl

    if "app.logging_config" not in sys.modules:
        sys.modules["app.logging_config"] = types.ModuleType("app.logging_config")
    lc = sys.modules["app.logging_config"]
    for _attr in ("audit_log", "get_request_ip", "get_user_agent"):
        if not hasattr(lc, _attr):
            setattr(lc, _attr, MagicMock())


_install_stubs()

# ---------------------------------------------------------------------------
# A. Load real extensions.py in isolation for config inspection (test 1).
#    Uses a private module name so it does not overwrite sys.modules["app.extensions"].
# ---------------------------------------------------------------------------

_ext_spec = importlib.util.spec_from_file_location(
    "_prod_extensions_under_test",
    os.path.join(_SERVER_ROOT, "app", "extensions.py"),
)
_ext_mod = importlib.util.module_from_spec(_ext_spec)
_ext_spec.loader.exec_module(_ext_mod)
_prod_limiter = _ext_mod.limiter

# ---------------------------------------------------------------------------
# B. Load auth.py so @limiter.limit(...) decorators fire and populate
#    _captured_limits (tests 2-3).  AuthService / jwt_blocklist_service are
#    stubs so no real work happens during import.
# ---------------------------------------------------------------------------

_auth_mod = _load_real_module("app.routes.auth", "app/routes/auth.py")

# ---------------------------------------------------------------------------
# C. Minimal Flask app with real Flask-Limiter for behavioral tests (4-6).
#    Each test uses a unique REMOTE_ADDR so the shared in-memory storage
#    never bleeds between tests.
# ---------------------------------------------------------------------------

_beh_app = Flask(__name__)
_beh_app.config["TESTING"] = True
_beh_limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)
_beh_limiter.init_app(_beh_app)

_hit: dict = {}


@_beh_app.route("/register", methods=["POST"])
@_beh_limiter.limit("5 per minute")
def _beh_register():
    _hit["register"] = _hit.get("register", 0) + 1
    return "ok", 200


@_beh_app.route("/login", methods=["POST"])
@_beh_limiter.limit("10 per minute")
def _beh_login():
    _hit["login"] = _hit.get("login", 0) + 1
    return "ok", 200


_beh_client = _beh_app.test_client()

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset():
    _hit.clear()
    yield


# ---------------------------------------------------------------------------
# Test 1: production global default limit
# ---------------------------------------------------------------------------

class TestProductionConfig:

    def test_global_default_limit_is_100_per_minute(self):
        dl = _prod_limiter.limit_manager._default_limits
        assert len(dl) >= 1
        assert dl[0].limit_provider == "100 per minute"


# ---------------------------------------------------------------------------
# Tests 2-3: auth.py route decorator limits (inspected, not executed)
# ---------------------------------------------------------------------------

class TestRouteDecoratorLimits:

    def test_register_uses_5_per_minute(self):
        assert "5 per minute" in _captured_limits

    def test_login_uses_10_per_minute(self):
        assert "10 per minute" in _captured_limits


# ---------------------------------------------------------------------------
# Tests 4-6: real Flask-Limiter enforcement behavior
# ---------------------------------------------------------------------------

class TestLimiterEnforcement:

    def test_register_returns_429_after_5_requests(self):
        env = {"REMOTE_ADDR": "10.0.1.1"}
        for _ in range(5):
            assert _beh_client.post("/register", environ_base=env).status_code == 200
        assert _beh_client.post("/register", environ_base=env).status_code == 429
        assert _hit.get("register", 0) == 5   # body not called on the 429

    def test_login_returns_429_after_10_requests(self):
        env = {"REMOTE_ADDR": "10.0.1.2"}
        for _ in range(10):
            assert _beh_client.post("/login", environ_base=env).status_code == 200
        assert _beh_client.post("/login", environ_base=env).status_code == 429
        assert _hit.get("login", 0) == 10

    def test_rate_limit_is_per_ip(self):
        exhausted = {"REMOTE_ADDR": "10.0.1.3"}
        other = {"REMOTE_ADDR": "10.0.1.4"}
        for _ in range(5):
            _beh_client.post("/register", environ_base=exhausted)
        assert _beh_client.post("/register", environ_base=exhausted).status_code == 429
        assert _beh_client.post("/register", environ_base=other).status_code == 200
