import hmac
from functools import wraps
from typing import Callable, Any

from flask import request, jsonify, current_app


def require_internal(fn: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        token = request.headers.get("X-Internal-Token", "")
        secret = current_app.config.get("INTERNAL_SERVICE_SECRET", "")

        if not secret or not hmac.compare_digest(token, secret):
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        return fn(*args, **kwargs)

    return wrapper
