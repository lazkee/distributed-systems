"""
Security tests for JWT logout / token revocation.

Proves that:
  1-2. revoke_token writes to Redis with a positive TTL, and silently skips
       already-expired tokens.
  3.   is_token_revoked fails CLOSED when Redis is unavailable.
  4.   invalidate_user_tokens stores an invalid-before timestamp with the
       correct key prefix and TTL.
  5.   is_token_invalid_for_user fails CLOSED when Redis is unavailable.
  6-7. is_token_invalid_for_user correctly rejects/allows tokens based on iat
       vs the stored invalid-before timestamp.
  8.   AdminService.change_user_role calls invalidate_user_tokens; if that
       call fails the DB transaction is rolled back and commit is not called.

No real Redis, no real database, no Flask app startup.
"""
import sys
import os
import types
import importlib.util
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# FakeRedisError must be defined BEFORE any stub installation so that the
# service module's `except RedisError:` clause references the same class.
# ---------------------------------------------------------------------------
class FakeRedisError(Exception):
    pass

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SERVER_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _load_real_module(dotted_name: str, rel_path: str):
    full_path = os.path.join(_SERVER_ROOT, rel_path)
    spec = importlib.util.spec_from_file_location(dotted_name, full_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[dotted_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_with_package(dotted_name: str, rel_path: str, package: str):
    """Like _load_real_module but sets __package__ for relative imports."""
    full_path = os.path.join(_SERVER_ROOT, rel_path)
    spec = importlib.util.spec_from_file_location(dotted_name, full_path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = package
    sys.modules[dotted_name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# sys.modules stubs — installed before any app.* or redis import
# ---------------------------------------------------------------------------

def _install_stubs() -> None:
    # redis — stub Redis class and RedisError before jwt_blocklist_service loads
    redis_stub = types.ModuleType("redis")
    redis_stub.Redis = MagicMock()
    redis_stub.RedisError = FakeRedisError
    sys.modules["redis"] = redis_stub

    # requests — needed by admin_service, but not exercised in role-change tests
    if "requests" not in sys.modules:
        req_stub = types.ModuleType("requests")
        req_stub.post = MagicMock()
        sys.modules["requests"] = req_stub

    # app package — __path__ makes it a package for relative imports
    app_mod = sys.modules.get("app") or types.ModuleType("app")
    if not hasattr(app_mod, "__path__"):
        app_mod.__path__ = []
    sys.modules["app"] = app_mod

    # app.config — fake Config with only the fields that are read at import time
    if "app.config" not in sys.modules:
        cfg_mod = types.ModuleType("app.config")
        class _Config:
            REDIS_URL = "redis://fake-host:6379/0"
            QUIZ_SERVICE_BASE_URL = "http://fake-quiz:5000"
        cfg_mod.Config = _Config
        sys.modules["app.config"] = cfg_mod

    # app.extensions
    if "app.extensions" not in sys.modules:
        ext = types.ModuleType("app.extensions")
        ext.db  = MagicMock()
        ext.jwt = MagicMock()
        sys.modules["app.extensions"] = ext

    # app.models.*
    sys.modules.setdefault("app.models", types.ModuleType("app.models"))
    if "app.models.user" not in sys.modules:
        user_mod = types.ModuleType("app.models.user")
        user_mod.User = MagicMock()
        sys.modules["app.models.user"] = user_mod

    # app.constants.user_roles — load the real enum
    sys.modules.setdefault("app.constants", types.ModuleType("app.constants"))
    if "app.constants.user_roles" not in sys.modules:
        _load_real_module("app.constants.user_roles", "app/constants/user_roles.py")

    # app.services package
    svc_pkg = sys.modules.get("app.services") or types.ModuleType("app.services")
    if not hasattr(svc_pkg, "__path__"):
        svc_pkg.__path__ = []
    sys.modules["app.services"] = svc_pkg

    if "app.services.mail_service" not in sys.modules:
        mail_mod = types.ModuleType("app.services.mail_service")
        mail_mod.MailService = MagicMock()
        sys.modules["app.services.mail_service"] = mail_mod

    # app.utils.*
    sys.modules.setdefault("app.utils", types.ModuleType("app.utils"))
    if "app.utils.internal_headers" not in sys.modules:
        hdr_mod = types.ModuleType("app.utils.internal_headers")
        hdr_mod.make_internal_headers = MagicMock(return_value={})
        sys.modules["app.utils.internal_headers"] = hdr_mod


_install_stubs()

# ---------------------------------------------------------------------------
# Load the real jwt_blocklist_service
# (module-level Redis.from_url() runs here against the fake Redis stub)
# ---------------------------------------------------------------------------
_blocklist_mod = _load_real_module(
    "app.services.jwt_blocklist_service",
    "app/services/jwt_blocklist_service.py",
)

# Wire parent→child attributes so patch("app.services.jwt_blocklist_service…")
# can resolve the dotted path via getattr traversal.
_svc_pkg = sys.modules["app.services"]
sys.modules["app"].services = _svc_pkg
_svc_pkg.jwt_blocklist_service = _blocklist_mod

# ---------------------------------------------------------------------------
# Load the real admin_service
# The `from ..config import Config` relative import needs __package__ set.
# ---------------------------------------------------------------------------
_admin_mod = _load_with_package(
    "app.services.admin_service",
    "app/services/admin_service.py",
    package="app.services",
)

# Wire so patch("app.services.admin_service.Process") resolves correctly.
_svc_pkg.admin_service = _admin_mod

AdminService = _admin_mod.AdminService
UserRole     = sys.modules["app.constants.user_roles"].UserRole

# Stable references
_db        = sys.modules["app.extensions"].db
_UserMock  = sys.modules["app.models.user"].User

# Matches _USER_INVALID_BEFORE_TTL in jwt_blocklist_service.py
_INVALID_BEFORE_TTL = 7 * 24 * 60 * 60   # 7 days in seconds

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def fresh_redis(monkeypatch):
    """
    Give each test a clean MagicMock for _client.
    Replacing the module-level variable works because every function in the
    service looks up _client in the module globals at call time.
    """
    fake = MagicMock()
    monkeypatch.setattr(_blocklist_mod, "_client", fake)
    _db.reset_mock()
    _UserMock.reset_mock()
    return fake


# ---------------------------------------------------------------------------
# 1-2  revoke_token
# ---------------------------------------------------------------------------

class TestRevokeToken:

    def test_future_token_calls_setex(self, fresh_redis):
        now = 1_000_000
        with patch.object(_blocklist_mod.time, "time", return_value=now):
            _blocklist_mod.revoke_token("abc", now + 300)
        fresh_redis.setex.assert_called_once()

    def test_key_has_jti_prefix(self, fresh_redis):
        now = 1_000_000
        with patch.object(_blocklist_mod.time, "time", return_value=now):
            _blocklist_mod.revoke_token("myjti", now + 60)
        key = fresh_redis.setex.call_args[0][0]
        assert key == "jwt:blocklist:myjti"

    def test_ttl_is_exp_minus_now(self, fresh_redis):
        now = 1_000_000
        with patch.object(_blocklist_mod.time, "time", return_value=now):
            _blocklist_mod.revoke_token("j", now + 500)
        ttl = fresh_redis.setex.call_args[0][1]
        assert ttl == 500

    def test_ttl_is_positive(self, fresh_redis):
        now = 2_000_000
        with patch.object(_blocklist_mod.time, "time", return_value=now):
            _blocklist_mod.revoke_token("j", now + 1)
        ttl = fresh_redis.setex.call_args[0][1]
        assert ttl > 0

    def test_expired_token_skips_setex(self, fresh_redis):
        now = 3_000_000
        with patch.object(_blocklist_mod.time, "time", return_value=now):
            _blocklist_mod.revoke_token("old", now - 10)   # expired 10 s ago
        fresh_redis.setex.assert_not_called()

    def test_token_at_exact_expiry_skips_setex(self, fresh_redis):
        now = 3_000_000
        with patch.object(_blocklist_mod.time, "time", return_value=now):
            _blocklist_mod.revoke_token("edge", now)        # TTL == 0
        fresh_redis.setex.assert_not_called()


# ---------------------------------------------------------------------------
# 3  is_token_revoked — fails CLOSED on RedisError
# ---------------------------------------------------------------------------

class TestIsTokenRevokedFailsClosed:

    def test_redis_error_returns_true(self, fresh_redis):
        fresh_redis.exists.side_effect = FakeRedisError("gone")
        assert _blocklist_mod.is_token_revoked("any-jti") is True

    def test_present_jti_returns_true(self, fresh_redis):
        fresh_redis.exists.return_value = 1
        assert _blocklist_mod.is_token_revoked("blocked") is True

    def test_absent_jti_returns_false(self, fresh_redis):
        fresh_redis.exists.return_value = 0
        assert _blocklist_mod.is_token_revoked("clean") is False


# ---------------------------------------------------------------------------
# 4  invalidate_user_tokens — stores invalid-before timestamp
# ---------------------------------------------------------------------------

class TestInvalidateUserTokens:

    def test_calls_setex(self, fresh_redis):
        with patch.object(_blocklist_mod.time, "time", return_value=0):
            _blocklist_mod.invalidate_user_tokens(1)
        fresh_redis.setex.assert_called_once()

    def test_key_contains_user_id(self, fresh_redis):
        with patch.object(_blocklist_mod.time, "time", return_value=0):
            _blocklist_mod.invalidate_user_tokens(77)
        key = fresh_redis.setex.call_args[0][0]
        assert "jwt:user_invalid_before:" in key
        assert "77" in key

    def test_ttl_matches_refresh_window(self, fresh_redis):
        with patch.object(_blocklist_mod.time, "time", return_value=0):
            _blocklist_mod.invalidate_user_tokens(1)
        ttl = fresh_redis.setex.call_args[0][1]
        assert ttl == _INVALID_BEFORE_TTL

    def test_stored_value_is_current_timestamp(self, fresh_redis):
        now = 9_999_999
        with patch.object(_blocklist_mod.time, "time", return_value=now):
            _blocklist_mod.invalidate_user_tokens(3)
        value = fresh_redis.setex.call_args[0][2]
        assert value == str(now)


# ---------------------------------------------------------------------------
# 5  is_token_invalid_for_user — fails CLOSED on RedisError
# ---------------------------------------------------------------------------

class TestIsTokenInvalidForUserFailsClosed:

    def test_redis_error_returns_true(self, fresh_redis):
        fresh_redis.get.side_effect = FakeRedisError("timeout")
        assert _blocklist_mod.is_token_invalid_for_user(user_id=1, iat=0) is True


# ---------------------------------------------------------------------------
# 6-7  is_token_invalid_for_user — boundary correctness
# ---------------------------------------------------------------------------

class TestIsTokenInvalidForUserLogic:

    def test_token_before_invalid_timestamp_is_rejected(self, fresh_redis):
        invalid_before = 1_000_000
        old_iat        = 999_999        # issued one second before the cut-off
        fresh_redis.get.return_value = str(invalid_before)
        assert _blocklist_mod.is_token_invalid_for_user(user_id=5, iat=old_iat) is True

    def test_token_after_invalid_timestamp_is_allowed(self, fresh_redis):
        invalid_before = 1_000_000
        newer_iat      = 1_000_001      # issued one second after the cut-off
        fresh_redis.get.return_value = str(invalid_before)
        assert _blocklist_mod.is_token_invalid_for_user(user_id=5, iat=newer_iat) is False

    def test_no_record_in_redis_allows_token(self, fresh_redis):
        fresh_redis.get.return_value = None
        assert _blocklist_mod.is_token_invalid_for_user(user_id=5, iat=12345) is False

    def test_checks_correct_user_key(self, fresh_redis):
        fresh_redis.get.return_value = None
        _blocklist_mod.is_token_invalid_for_user(user_id=42, iat=0)
        key = fresh_redis.get.call_args[0][0]
        assert "jwt:user_invalid_before:" in key
        assert "42" in key


# ---------------------------------------------------------------------------
# 8  AdminService.change_user_role — token invalidation wiring
# ---------------------------------------------------------------------------

def _fake_user(role: str = "Player"):
    """Minimal user object with mutable attributes matching what admin_service reads."""
    return types.SimpleNamespace(id=10, email="admin-target@example.com", role=role)


class TestAdminRoleChangeInvalidatesTokens:

    @patch("app.services.admin_service.Process")
    def test_invalidate_user_tokens_is_called(self, _proc, fresh_redis):
        _UserMock.query.get.return_value = _fake_user("Player")
        with patch.object(_blocklist_mod, "invalidate_user_tokens") as mock_inv:
            AdminService.change_user_role(user_id=10, new_role=UserRole.MODERATOR)
        mock_inv.assert_called_once_with(10)

    @patch("app.services.admin_service.Process")
    def test_commit_called_once_on_success(self, _proc, fresh_redis):
        _UserMock.query.get.return_value = _fake_user("Player")
        with patch.object(_blocklist_mod, "invalidate_user_tokens"):
            AdminService.change_user_role(user_id=10, new_role=UserRole.MODERATOR)
        _db.session.commit.assert_called_once()

    @patch("app.services.admin_service.Process")
    def test_invalidation_failure_triggers_rollback(self, _proc, fresh_redis):
        _UserMock.query.get.return_value = _fake_user("Player")
        with patch.object(_blocklist_mod, "invalidate_user_tokens",
                          side_effect=Exception("Redis unavailable")):
            with pytest.raises(RuntimeError, match="Token invalidation failed"):
                AdminService.change_user_role(user_id=10, new_role=UserRole.MODERATOR)
        _db.session.rollback.assert_called_once()

    @patch("app.services.admin_service.Process")
    def test_invalidation_failure_prevents_commit(self, _proc, fresh_redis):
        _UserMock.query.get.return_value = _fake_user("Player")
        with patch.object(_blocklist_mod, "invalidate_user_tokens",
                          side_effect=Exception("Redis unavailable")):
            with pytest.raises(RuntimeError):
                AdminService.change_user_role(user_id=10, new_role=UserRole.MODERATOR)
        _db.session.commit.assert_not_called()
