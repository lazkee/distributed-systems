"""
Security tests for JWT cookie-only transport and CSRF protection.

Tests 1-2 read the production Config class to confirm security settings.
Tests 3-7 use a minimal Flask + Flask-JWT-Extended app to prove the library
enforces those settings under real conditions:
  3. POST with JWT cookie but missing CSRF header → 401, body not executed.
  4. POST with JWT cookie but wrong CSRF value → 401, body not executed.
  5. Authorization: Bearer header alone (no cookie) → 401 (cookie-only enforced).
  6. Refresh-protected POST without refresh CSRF header → 401.
  7. Correct CSRF token allows the request through → 200, body executed once.

No real database, no Redis, no quizService, no email.
"""
import os
import importlib.util

# Set env vars required by Config's class-level guards before any import of
# config.py.  os.environ.setdefault leaves already-set vars untouched.
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

import pytest
from flask import Flask, jsonify
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    jwt_required,
    set_access_cookies,
    set_refresh_cookies,
)

# ---------------------------------------------------------------------------
# Load production Config in isolation — not injected into sys.modules so it
# does not interfere with other test files' stubs.
# ---------------------------------------------------------------------------

_cfg_path = os.path.join(os.path.dirname(__file__), "..", "app", "config.py")
_cfg_spec = importlib.util.spec_from_file_location("_prod_config_under_test", _cfg_path)
_cfg_mod = importlib.util.module_from_spec(_cfg_spec)
_cfg_spec.loader.exec_module(_cfg_mod)
ProductionConfig = _cfg_mod.Config

# ---------------------------------------------------------------------------
# Minimal Flask app — same JWT cookie/CSRF policy as production.
# Cookie paths are collapsed to "/" so the test client sends cookies to all
# test routes; this does not affect what we are testing (CSRF validation).
# ---------------------------------------------------------------------------

_app = Flask(__name__)
_app.config.update(
    SECRET_KEY="test-secret",
    JWT_SECRET_KEY="test-jwt-secret",
    TESTING=True,
    JWT_TOKEN_LOCATION=["cookies"],
    JWT_COOKIE_CSRF_PROTECT=True,
    JWT_COOKIE_SECURE=False,          # must be False for plain HTTP in tests
    JWT_COOKIE_SAMESITE="Lax",
    JWT_ACCESS_COOKIE_PATH="/",
    JWT_REFRESH_COOKIE_PATH="/",
    JWT_ACCESS_CSRF_COOKIE_PATH="/",
    JWT_REFRESH_CSRF_COOKIE_PATH="/",
)
JWTManager(_app)

_hit: dict = {}


@_app.route("/set-cookies", methods=["POST"])
def _set_cookies():
    resp = jsonify({"ok": True})
    set_access_cookies(resp, create_access_token(identity="1"))
    set_refresh_cookies(resp, create_refresh_token(identity="1"))
    return resp, 200


@_app.route("/protected", methods=["POST"])
@jwt_required()
def _protected():
    _hit["access"] = _hit.get("access", 0) + 1
    return jsonify({"ok": True}), 200


@_app.route("/refresh-protected", methods=["POST"])
@jwt_required(refresh=True)
def _refresh_protected():
    _hit["refresh"] = _hit.get("refresh", 0) + 1
    return jsonify({"ok": True}), 200


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_client_with_cookies():
    """
    Return a fresh test client with access+refresh cookies already set,
    plus a dict containing the extracted CSRF token values.
    """
    client = _app.test_client()
    resp = client.post("/set-cookies")
    csrf = {}
    for header in resp.headers.getlist("Set-Cookie"):
        if header.startswith("csrf_access_token="):
            csrf["access"] = header.split("=", 1)[1].split(";")[0]
        elif header.startswith("csrf_refresh_token="):
            csrf["refresh"] = header.split("=", 1)[1].split(";")[0]
    return client, csrf


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset():
    _hit.clear()
    yield


# ---------------------------------------------------------------------------
# Tests 1-2: production Config security settings
# ---------------------------------------------------------------------------

class TestProductionConfig:

    def test_jwt_token_location_is_cookies_only(self):
        assert ProductionConfig.JWT_TOKEN_LOCATION == ["cookies"]

    def test_csrf_protection_is_enabled(self):
        assert ProductionConfig.JWT_COOKIE_CSRF_PROTECT is True


# ---------------------------------------------------------------------------
# Tests 3-7: cookie/CSRF enforcement via real Flask-JWT-Extended
# ---------------------------------------------------------------------------

class TestCookieCsrfEnforcement:

    def test_missing_csrf_header_rejects_post(self):
        client, _ = _new_client_with_cookies()
        resp = client.post("/protected")          # has cookie, no X-CSRF-TOKEN
        assert resp.status_code == 401
        assert _hit.get("access", 0) == 0

    def test_wrong_csrf_value_rejects_post(self):
        client, _ = _new_client_with_cookies()
        resp = client.post("/protected", headers={"X-CSRF-TOKEN": "tampered-value"})
        assert resp.status_code == 401
        assert _hit.get("access", 0) == 0

    def test_bearer_header_alone_is_rejected(self):
        client = _app.test_client()              # fresh — no cookies in jar
        with _app.app_context():
            token = create_access_token(identity="1")
        resp = client.post("/protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
        assert _hit.get("access", 0) == 0

    def test_refresh_route_requires_refresh_csrf(self):
        client, _ = _new_client_with_cookies()
        resp = client.post("/refresh-protected")  # has refresh cookie, no CSRF
        assert resp.status_code == 401
        assert _hit.get("refresh", 0) == 0

    def test_correct_csrf_allows_request(self):
        client, csrf = _new_client_with_cookies()
        resp = client.post("/protected", headers={"X-CSRF-TOKEN": csrf["access"]})
        assert resp.status_code == 200
        assert _hit.get("access", 0) == 1
