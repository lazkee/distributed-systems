"""
Security tests for profile-picture upload validation.

Proves that CloudinaryService.upload_profile_picture rejects invalid inputs
*before* any Cloudinary API call or database commit is made.

No real Cloudinary call, no real database, no Flask app startup.
"""
import sys
import os
import io
import types
import importlib.util
from unittest.mock import MagicMock

import pytest
from PIL import Image

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_SERVER_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _load_real_module(dotted_name: str, rel_path: str):
    full_path = os.path.join(_SERVER_ROOT, rel_path)
    spec = importlib.util.spec_from_file_location(dotted_name, full_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[dotted_name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# sys.modules stubs — installed before the real service module is loaded
# ---------------------------------------------------------------------------

def _install_stubs() -> None:
    sys.modules.setdefault("app", types.ModuleType("app"))

    if "app.extensions" not in sys.modules:
        ext = types.ModuleType("app.extensions")
        ext.db  = MagicMock()
        ext.jwt = MagicMock()
        sys.modules["app.extensions"] = ext

    sys.modules.setdefault("app.models", types.ModuleType("app.models"))
    if "app.models.user" not in sys.modules:
        user_mod = types.ModuleType("app.models.user")
        user_mod.User = MagicMock()
        sys.modules["app.models.user"] = user_mod

    # Stub cloudinary.uploader so no real API call can escape
    cloudinary_stub = sys.modules.get("cloudinary") or types.ModuleType("cloudinary")
    uploader_stub = types.ModuleType("cloudinary.uploader")
    uploader_stub.upload  = MagicMock()
    uploader_stub.destroy = MagicMock()
    cloudinary_stub.uploader = uploader_stub
    sys.modules["cloudinary"]          = cloudinary_stub
    sys.modules["cloudinary.uploader"] = uploader_stub


_install_stubs()

_svc_mod = _load_real_module(
    "app.services.cloudinary_service",
    "app/services/cloudinary_service.py",
)

CloudinaryService = _svc_mod.CloudinaryService

# Stable references to the mocks the service captured at import time
_db       = sys.modules["app.extensions"].db
_UserMock = sys.modules["app.models.user"].User
_upload   = sys.modules["cloudinary.uploader"].upload

# ---------------------------------------------------------------------------
# Input builders
# ---------------------------------------------------------------------------

def _make_image_bytes(fmt: str) -> io.BytesIO:
    """Return a valid, fully encoded image in *fmt* as an in-memory BytesIO."""
    img = Image.new("RGB", (4, 4), color=(10, 20, 30))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf


def _make_oversized() -> io.BytesIO:
    """BytesIO that exceeds the 5 MB limit (content does not need to be a valid image)."""
    return io.BytesIO(b"\x00" * (5 * 1024 * 1024 + 1))


def _make_truncated_jpeg() -> io.BytesIO:
    """JPEG SOI header present, but data cut short so img.load() fails."""
    full = io.BytesIO()
    Image.new("RGB", (8, 8)).save(full, format="JPEG")
    return io.BytesIO(full.getvalue()[:24])   # header only, no pixel data


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

class _FakeUser:
    profile_picture_url       = None
    profile_picture_public_id = None


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mock state and provide a valid default user before each test."""
    _db.reset_mock()
    _UserMock.reset_mock()
    _upload.reset_mock()
    # Default: user exists — so validation tests reach _validate_and_sanitize
    _UserMock.query.get.return_value = _FakeUser()
    yield


# ---------------------------------------------------------------------------
# 1. Oversized upload
# ---------------------------------------------------------------------------

class TestOversizedUploadRejected:

    def test_raises_value_error(self):
        with pytest.raises(ValueError):
            CloudinaryService.upload_profile_picture(user_id=1, image=_make_oversized())

    def test_upload_not_called(self):
        with pytest.raises(ValueError):
            CloudinaryService.upload_profile_picture(user_id=1, image=_make_oversized())
        _upload.assert_not_called()

    def test_commit_not_called(self):
        with pytest.raises(ValueError):
            CloudinaryService.upload_profile_picture(user_id=1, image=_make_oversized())
        _db.session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# 2. Non-image bytes
# ---------------------------------------------------------------------------

class TestNonImageBytesRejected:

    def test_plain_text_raises_value_error(self):
        garbage = io.BytesIO(b"Not an image. Just plain ASCII text.")
        with pytest.raises(ValueError):
            CloudinaryService.upload_profile_picture(user_id=1, image=garbage)

    def test_plain_text_upload_not_called(self):
        garbage = io.BytesIO(b"Not an image. Just plain ASCII text.")
        with pytest.raises(ValueError):
            CloudinaryService.upload_profile_picture(user_id=1, image=garbage)
        _upload.assert_not_called()

    def test_executable_bytes_raises_value_error(self):
        elf = io.BytesIO(b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 56)
        with pytest.raises(ValueError):
            CloudinaryService.upload_profile_picture(user_id=1, image=elf)

    def test_executable_bytes_upload_not_called(self):
        elf = io.BytesIO(b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 56)
        with pytest.raises(ValueError):
            CloudinaryService.upload_profile_picture(user_id=1, image=elf)
        _upload.assert_not_called()

    def test_non_image_commit_not_called(self):
        garbage = io.BytesIO(b"<script>alert(1)</script>")
        with pytest.raises(ValueError):
            CloudinaryService.upload_profile_picture(user_id=1, image=garbage)
        _db.session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# 3. Corrupt / truncated image bytes
# ---------------------------------------------------------------------------

class TestCorruptImageRejected:

    def test_truncated_jpeg_raises_value_error(self):
        with pytest.raises(ValueError):
            CloudinaryService.upload_profile_picture(user_id=1, image=_make_truncated_jpeg())

    def test_truncated_jpeg_upload_not_called(self):
        with pytest.raises(ValueError):
            CloudinaryService.upload_profile_picture(user_id=1, image=_make_truncated_jpeg())
        _upload.assert_not_called()

    def test_truncated_jpeg_commit_not_called(self):
        with pytest.raises(ValueError):
            CloudinaryService.upload_profile_picture(user_id=1, image=_make_truncated_jpeg())
        _db.session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# 4. Unsupported image format (GIF)
# ---------------------------------------------------------------------------

class TestUnsupportedFormatRejected:

    def test_gif_raises_value_error(self):
        with pytest.raises(ValueError, match="not allowed"):
            CloudinaryService.upload_profile_picture(user_id=1, image=_make_image_bytes("GIF"))

    def test_gif_upload_not_called(self):
        with pytest.raises(ValueError):
            CloudinaryService.upload_profile_picture(user_id=1, image=_make_image_bytes("GIF"))
        _upload.assert_not_called()

    def test_gif_commit_not_called(self):
        with pytest.raises(ValueError):
            CloudinaryService.upload_profile_picture(user_id=1, image=_make_image_bytes("GIF"))
        _db.session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# 5. Missing user
# ---------------------------------------------------------------------------

class TestMissingUserRejected:

    def test_user_not_found_raises_value_error(self):
        _UserMock.query.get.return_value = None
        with pytest.raises(ValueError, match="User not found"):
            CloudinaryService.upload_profile_picture(user_id=999, image=_make_image_bytes("JPEG"))

    def test_user_not_found_upload_not_called(self):
        _UserMock.query.get.return_value = None
        with pytest.raises(ValueError):
            CloudinaryService.upload_profile_picture(user_id=999, image=_make_image_bytes("JPEG"))
        _upload.assert_not_called()

    def test_user_not_found_commit_not_called(self):
        _UserMock.query.get.return_value = None
        with pytest.raises(ValueError):
            CloudinaryService.upload_profile_picture(user_id=999, image=_make_image_bytes("JPEG"))
        _db.session.commit.assert_not_called()
