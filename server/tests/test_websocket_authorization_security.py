"""
Security tests for WebSocket connection and room authorization.

Tests 1-7  prove that handle_connect rejects connections with absent,
malformed, or structurally invalid tokens without storing any socket
identity.

Tests 8-12 prove that handle_join enforces role and identity checks:
non-admins cannot enter the admins room, and users cannot enter rooms
belonging to other users.

No real database, no Redis, no Socket.IO network, no quizService.
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
# sys.modules stubs
# ---------------------------------------------------------------------------

def _install_stubs() -> None:
    _ensure_pkg("app")

    # ── real UserRole ────────────────────────────────────────────────────────
    _ensure_pkg("app.constants")
    if "app.constants.user_roles" not in sys.modules:
        _load_real_module("app.constants.user_roles", "app/constants/user_roles.py")

    # ── flask_jwt_extended: ensure decode_token is importable ────────────────
    if "flask_jwt_extended" not in sys.modules:
        fjwt = types.ModuleType("flask_jwt_extended")
        fjwt.verify_jwt_in_request = MagicMock()
        fjwt.get_jwt = MagicMock(return_value={})
        fjwt.get_jwt_identity = MagicMock(return_value="1")
        fjwt.jwt_required = lambda fn: fn
        fjwt.decode_token = MagicMock()
        sys.modules["flask_jwt_extended"] = fjwt
    elif not hasattr(sys.modules["flask_jwt_extended"], "decode_token"):
        sys.modules["flask_jwt_extended"].decode_token = MagicMock()

    # ── flask_socketio: stub join_room / disconnect ──────────────────────────
    if "flask_socketio" not in sys.modules:
        fsio = types.ModuleType("flask_socketio")
        fsio.join_room = MagicMock()
        fsio.disconnect = MagicMock()
        sys.modules["flask_socketio"] = fsio
    else:
        fsio = sys.modules["flask_socketio"]
        for _attr in ("join_room", "disconnect"):
            if not hasattr(fsio, _attr):
                setattr(fsio, _attr, MagicMock())

    # ── app.extensions.socketio ─────────────────────────────────────────────
    # CRITICAL: @socketio.on("event") must be a pass-through decorator so that
    # handle_connect / handle_join stay as the real functions after decoration.
    # A plain MagicMock's .on() returns another MagicMock, which would replace
    # the decorated function — breaking all subsequent tests.
    if "app.extensions" not in sys.modules:
        sys.modules["app.extensions"] = types.ModuleType("app.extensions")
    ext = sys.modules["app.extensions"]
    for _a in ("db", "jwt"):
        if not hasattr(ext, _a):
            setattr(ext, _a, MagicMock())
    # Always (re-)set .on to the identity pass-through, even if socketio already
    # exists as a MagicMock from another test file.
    if not hasattr(ext, "socketio"):
        ext.socketio = MagicMock()
    ext.socketio.on = lambda event: (lambda fn: fn)


_install_stubs()

# ---------------------------------------------------------------------------
# Load the real socket_events module
# ---------------------------------------------------------------------------

_socket_mod = _load_real_module(
    "app.routes.socket_events",
    "app/routes/socket_events.py",
)

# Verify the handlers are the real functions, not MagicMock wrappers.
assert callable(_socket_mod.handle_connect), "handle_connect was overwritten by decorator stub"
assert callable(_socket_mod.handle_join),    "handle_join was overwritten by decorator stub"

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

_SID = "ws-test-sid"


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    """Clear socket state and patch all module-level callables before each test."""
    _socket_mod._sockets.clear()
    monkeypatch.setattr(_socket_mod, "request", types.SimpleNamespace(sid=_SID))
    monkeypatch.setattr(_socket_mod, "decode_token", MagicMock(
        return_value={"sub": "1", "role": "Admin"}
    ))
    monkeypatch.setattr(_socket_mod, "join_room", MagicMock())
    monkeypatch.setattr(_socket_mod, "disconnect", MagicMock())
    yield


# ---------------------------------------------------------------------------
# Tests 1-7: handle_connect rejects invalid auth before storing any identity
# ---------------------------------------------------------------------------

class TestHandleConnect:

    def test_none_auth_rejected(self):
        assert _socket_mod.handle_connect(auth=None) is False
        assert _SID not in _socket_mod._sockets

    @pytest.mark.parametrize("auth", ["Bearer xyz", [1, 2], 42])
    def test_non_dict_auth_rejected(self, auth):
        assert _socket_mod.handle_connect(auth=auth) is False
        assert _SID not in _socket_mod._sockets

    def test_missing_token_rejected(self):
        assert _socket_mod.handle_connect(auth={"token": ""}) is False
        assert _SID not in _socket_mod._sockets

    def test_invalid_token_rejected(self, monkeypatch):
        monkeypatch.setattr(_socket_mod, "decode_token",
                            MagicMock(side_effect=Exception("bad token")))
        assert _socket_mod.handle_connect(auth={"token": "corrupt"}) is False
        assert _SID not in _socket_mod._sockets

    def test_missing_sub_rejected(self, monkeypatch):
        monkeypatch.setattr(_socket_mod, "decode_token",
                            MagicMock(return_value={"role": "Admin"}))
        assert _socket_mod.handle_connect(auth={"token": "tok"}) is False
        assert _SID not in _socket_mod._sockets

    def test_non_numeric_sub_rejected(self, monkeypatch):
        monkeypatch.setattr(_socket_mod, "decode_token",
                            MagicMock(return_value={"sub": "not-a-number", "role": "Admin"}))
        assert _socket_mod.handle_connect(auth={"token": "tok"}) is False
        assert _SID not in _socket_mod._sockets

    def test_missing_role_rejected(self, monkeypatch):
        monkeypatch.setattr(_socket_mod, "decode_token",
                            MagicMock(return_value={"sub": "1"}))
        assert _socket_mod.handle_connect(auth={"token": "tok"}) is False
        assert _SID not in _socket_mod._sockets


# ---------------------------------------------------------------------------
# Tests 8-12: handle_join enforces role and identity
# ---------------------------------------------------------------------------

class TestHandleJoin:

    def test_non_admin_cannot_join_admins_room(self):
        _socket_mod._sockets[_SID] = {"user_id": 10, "role": "Player"}
        _socket_mod.handle_join("admins")
        _socket_mod.disconnect.assert_called_once()
        _socket_mod.join_room.assert_not_called()

    def test_admin_can_join_admins_room(self):
        _socket_mod._sockets[_SID] = {"user_id": 10, "role": "Admin"}
        _socket_mod.handle_join("admins")
        _socket_mod.join_room.assert_called_once_with("admins")
        _socket_mod.disconnect.assert_not_called()

    def test_user_cannot_join_another_users_room(self):
        _socket_mod._sockets[_SID] = {"user_id": 10, "role": "Player"}
        _socket_mod.handle_join("user_20")
        _socket_mod.disconnect.assert_called_once()
        _socket_mod.join_room.assert_not_called()

    def test_user_can_join_own_room(self):
        _socket_mod._sockets[_SID] = {"user_id": 10, "role": "Player"}
        _socket_mod.handle_join("user_10")
        _socket_mod.join_room.assert_called_once_with("user_10")
        _socket_mod.disconnect.assert_not_called()

    @pytest.mark.parametrize("room", ["moderators", "user_abc", "", None])
    def test_unknown_or_malformed_room_rejected(self, room):
        _socket_mod._sockets[_SID] = {"user_id": 10, "role": "Player"}
        _socket_mod.handle_join(room)
        _socket_mod.disconnect.assert_called_once()
        _socket_mod.join_room.assert_not_called()
