from typing import Optional

from flask import current_app


def make_internal_headers(
    user_id: Optional[int | str] = None,
    user_role: Optional[str] = None,
) -> dict:
    headers = {
        "X-Internal-Token": current_app.config.get("INTERNAL_SERVICE_SECRET", "")
    }

    if user_id is not None:
        headers["X-User-Id"] = str(user_id)

    if user_role is not None:
        headers["X-User-Role"] = user_role

    return headers
