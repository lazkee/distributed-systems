import io

import cloudinary.uploader
from PIL import Image, UnidentifiedImageError

from app.extensions import db
from app.models.user import User

_MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
_ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


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

        user.profile_picture_url = upload_result["secure_url"]
        user.profile_picture_public_id = upload_result["public_id"]
        db.session.commit()

        return {"url": upload_result["secure_url"]}