import hmac
from functools import wraps
from typing import Callable, Any

from flask import request, jsonify, current_app

from app.logging_config import audit_log, get_request_ip, get_user_agent


def require_internal(fn: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        token = request.headers.get("X-Internal-Token", "")
        secret = current_app.config.get("INTERNAL_SERVICE_SECRET", "")

        if not secret or not hmac.compare_digest(token, secret):
            audit_log.warning(
                "internal_auth_failed",
                path=request.path,
                method=request.method,
                ip=get_request_ip(),
                user_agent=get_user_agent(),
            )
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        return fn(*args, **kwargs)

    return wrapper
