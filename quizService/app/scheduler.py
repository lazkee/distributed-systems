import logging
import os

logger = logging.getLogger(__name__)


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
                logger.info(
                    "Retention cleanup: deleted %d quiz attempt(s) older than %d days",
                    deleted,
                    retention_days,
                )
            except Exception:
                logger.exception("Retention cleanup failed")

    scheduler = BackgroundScheduler()
    scheduler.add_job(_run_cleanup, "cron", hour=2, minute=0)
    scheduler.start()
    logger.info("Retention scheduler started (runs daily at 02:00 UTC)")
