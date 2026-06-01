import os

from app.logging_config import audit_log


def start_scheduler(app):
    if not app.config.get("ENABLE_RETENTION_JOBS"):
        return

    
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    from apscheduler.schedulers.background import BackgroundScheduler
    from app.services.quiz_attempts_service import AttemptsService

    retention_days = app.config.get("QUIZ_ATTEMPT_RETENTION_DAYS", 730)

    def _run_cleanup():
        with app.app_context():
            try:
                deleted = AttemptsService.cleanup_old_attempts(retention_days)
                audit_log.info(
                    "retention_cleanup_completed",
                    deleted=deleted,
                    retention_days=retention_days,
                )
            except Exception:
                audit_log.warning("retention_cleanup_failed", retention_days=retention_days)

    scheduler = BackgroundScheduler()
    scheduler.add_job(_run_cleanup, "cron", hour=2, minute=0)
    scheduler.start()
    audit_log.info("retention_scheduler_started", schedule="daily at 02:00 UTC")
