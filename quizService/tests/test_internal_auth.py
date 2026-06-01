"""
Tests for the require_internal decorator (X-Internal-Token authentication).

"""
import sys
import os
import types
import importlib

import structlog
import pytest
from flask import Flask, jsonify


def _install_app_stubs():
    if "app" in sys.modules:
        return  

    structlog.configure(
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    _audit = structlog.get_logger("audit")

    logging_stub = types.ModuleType("app.logging_config")
    logging_stub.audit_log = _audit
    logging_stub.get_request_ip = lambda: "127.0.0.1"
    logging_stub.get_user_agent = lambda: ""

    app_stub = types.ModuleType("app")
    middlewares_stub = types.ModuleType("app.middlewares")

    sys.modules["app"] = app_stub
    sys.modules["app.logging_config"] = logging_stub
    sys.modules["app.middlewares"] = middlewares_stub


_install_app_stubs()


_MIDDLEWARE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "app", "middlewares", "require_internal.py"
)
_spec = importlib.util.spec_from_file_location("app.middlewares.require_internal", _MIDDLEWARE_PATH)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["app.middlewares.require_internal"] = _mod
_spec.loader.exec_module(_mod)

require_internal = _mod.require_internal

# ---------------------------------------------------------------------------

TEST_SECRET = "test-internal-secret"


@pytest.fixture()
def app():
    """Minimal Flask app with a single @require_internal–protected route."""
    flask_app = Flask(__name__)
    flask_app.config.update(
        TESTING=True,
        INTERNAL_SERVICE_SECRET=TEST_SECRET,
        SECRET_KEY="test-only-key",
    )

    @flask_app.route("/test-protected")
    @require_internal
    def protected():
        return jsonify({"success": True}), 200

    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRequireInternalDecorator:
    def test_no_token_returns_401(self, client):
        response = client.get("/test-protected")
        assert response.status_code == 401

    def test_wrong_token_returns_401(self, client):
        response = client.get(
            "/test-protected",
            headers={"X-Internal-Token": "wrong-token"},
        )
        assert response.status_code == 401

    def test_correct_token_returns_200(self, client):
        response = client.get(
            "/test-protected",
            headers={"X-Internal-Token": TEST_SECRET},
        )
        assert response.status_code == 200

    def test_empty_token_returns_401(self, client):
        response = client.get(
            "/test-protected",
            headers={"X-Internal-Token": ""},
        )
        assert response.status_code == 401

    def test_no_token_response_does_not_expose_secret(self, client):
        body = client.get("/test-protected").get_data(as_text=True)
        assert TEST_SECRET not in body

    def test_wrong_token_response_does_not_expose_secret(self, client):
        body = client.get(
            "/test-protected",
            headers={"X-Internal-Token": "wrong-token"},
        ).get_data(as_text=True)
        assert TEST_SECRET not in body

    def test_401_body_shape(self, client):
        data = client.get("/test-protected").get_json()
        assert data["success"] is False
        assert "message" in data
