import io
from urllib.parse import urlparse

import cloudinary.uploader
from PIL import Image, UnidentifiedImageError

from app.extensions import db
from app.models.user import User

_MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
_ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
_ALLOWED_RESPONSE_FORMATS = {"jpg", "jpeg", "png", "webp"}
_INVALID_UPLOAD_RESPONSE_MESSAGE = "Invalid image storage response."


def _validate_and_sanitize(file_storage) -> io.BytesIO:
    # --- size check ---
    file_storage.seek(0, 2)
    size = file_storage.tell()
    file_storage.seek(0)
    if size > _MAX_SIZE_BYTES:
        raise ValueError("Image must be smaller than 5 MB.")

    # --- decode with Pillow (validates actual bytes) ---
    try:
        img = Image.open(file_storage)
        img.load()  # fully decode pixels — catches truncation and corruption
    except UnidentifiedImageError:
        raise ValueError("File is not a valid image.")
    except Exception:
        raise ValueError("Image could not be decoded.")

    # --- format allowlist ---
    if img.format not in _ALLOWED_FORMATS:
        raise ValueError("Image format not allowed. Accepted formats: JPEG, PNG, WEBP.")

    # --- re-encode into a clean buffer  ---
    buf = io.BytesIO()
    if img.format == "JPEG":
        img.convert("RGB").save(buf, format="JPEG")
    else:
        img.save(buf, format=img.format)
    buf.seek(0)
    return buf


def _validate_upload_response(upload_result: dict) -> dict:
    if not isinstance(upload_result, dict):
        raise ValueError(_INVALID_UPLOAD_RESPONSE_MESSAGE)

    secure_url = upload_result.get("secure_url")
    if not isinstance(secure_url, str) or not secure_url.startswith("https://"):
        raise ValueError(_INVALID_UPLOAD_RESPONSE_MESSAGE)

    parsed_url = urlparse(secure_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ValueError(_INVALID_UPLOAD_RESPONSE_MESSAGE)

    public_id = upload_result.get("public_id")
    if not isinstance(public_id, str) or not public_id.strip():
        raise ValueError(_INVALID_UPLOAD_RESPONSE_MESSAGE)

    resource_type = upload_result.get("resource_type")
    if resource_type is not None and resource_type != "image":
        raise ValueError(_INVALID_UPLOAD_RESPONSE_MESSAGE)

    image_format = upload_result.get("format")
    if image_format is not None:
        if not isinstance(image_format, str) or image_format.lower() not in _ALLOWED_RESPONSE_FORMATS:
            raise ValueError(_INVALID_UPLOAD_RESPONSE_MESSAGE)

    return {
        "secure_url": secure_url,
        "public_id": public_id,
    }


class CloudinaryService:

    @staticmethod
    def upload_profile_picture(user_id, image):
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")

        sanitized = _validate_and_sanitize(image)

        upload_result = cloudinary.uploader.upload(
            sanitized,
            folder="drs_profile_pictures",
            public_id=f"user_{user_id}",
            overwrite=True,
            resource_type="image"
        )

        validated_upload = _validate_upload_response(upload_result)

        user.profile_picture_url = validated_upload["secure_url"]
        user.profile_picture_public_id = validated_upload["public_id"]
        db.session.commit()

        return {"url": validated_upload["secure_url"]}

    @staticmethod
    def delete_profile_picture(public_id: str) -> None:
        cloudinary.uploader.destroy(public_id, resource_type="image")
