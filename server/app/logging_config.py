import logging
import structlog


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


audit_log = structlog.get_logger("audit")


def get_request_ip() -> str:
    from flask import request
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def get_user_agent() -> str:
    from flask import request
    return request.headers.get("User-Agent", "") or ""
