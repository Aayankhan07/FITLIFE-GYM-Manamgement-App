"""
FitLife — APScheduler Background Job Scheduler
Runs automated daily/monthly jobs.
Graceful fallback if APScheduler not installed.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
_scheduler = None


def start_scheduler() -> bool:
    """Initialize and start the APScheduler background scheduler."""
    global _scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        _scheduler = BackgroundScheduler(timezone="Asia/Karachi")

        # Daily at 1:00 AM — mark expired memberships
        _scheduler.add_job(
            _job_expire_memberships,
            CronTrigger(hour=1, minute=0),
            id="expire_memberships",
            replace_existing=True,
        )

        # Daily at 1:05 AM — mark overdue payments
        _scheduler.add_job(
            _job_overdue_payments,
            CronTrigger(hour=1, minute=5),
            id="overdue_payments",
            replace_existing=True,
        )

        # Daily at 1:10 AM — check equipment maintenance
        _scheduler.add_job(
            _job_equipment_maintenance,
            CronTrigger(hour=1, minute=10),
            id="equipment_maintenance",
            replace_existing=True,
        )

        # Daily at 9:00 AM — renewal notifications (7-day warning)
        _scheduler.add_job(
            _job_renewal_notifications,
            CronTrigger(hour=9, minute=0),
            id="renewal_notifications",
            replace_existing=True,
        )

        # 27th of each month at 10:00 AM — auto invoice job
        _scheduler.add_job(
            _job_auto_invoices,
            CronTrigger(day=27, hour=10, minute=0),
            id="auto_invoices",
            replace_existing=True,
        )

        # 10th of each month at 9:00 AM — overdue alert
        _scheduler.add_job(
            _job_overdue_alerts,
            CronTrigger(day=10, hour=9, minute=0),
            id="overdue_alerts",
            replace_existing=True,
        )

        _scheduler.start()
        logger.info("APScheduler started. Jobs registered.")
        return True

    except ImportError:
        logger.warning("APScheduler not installed. Background jobs disabled. "
                       "Run: pip install APScheduler")
        return False
    except Exception as e:
        logger.error(f"Scheduler start error: {e}", exc_info=True)
        return False


def stop_scheduler() -> None:
    """Gracefully stop the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        try:
            _scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped.")
        except Exception as e:
            logger.error(f"Scheduler stop error: {e}")


def is_running() -> bool:
    return _scheduler is not None and _scheduler.running


# ── Job Implementations ────────────────────────────────────────────────────────

def _job_expire_memberships():
    try:
        from services.member_service import update_expired_memberships
        count = update_expired_memberships()
        logger.info(f"[Scheduler] Expired {count} memberships.")
    except Exception as e:
        logger.error(f"[Scheduler] expire_memberships error: {e}")


def _job_overdue_payments():
    try:
        from services.billing_service import mark_overdue_payments
        count = mark_overdue_payments()
        logger.info(f"[Scheduler] Marked {count} overdue payments.")
    except Exception as e:
        logger.error(f"[Scheduler] overdue_payments error: {e}")


def _job_equipment_maintenance():
    try:
        from services.equipment_service import get_maintenance_due
        items = get_maintenance_due(days=7)
        if items:
            from services.notification_service import push_notification
            for item in items:
                push_notification(
                    user_id=1,
                    title="Equipment Maintenance Due",
                    message=f"{item[1]} ({item[6]}) due for maintenance by {item[9]}.",
                    notif_type="warning"
                )
        logger.info(f"[Scheduler] Equipment check: {len(items)} items due.")
    except Exception as e:
        logger.error(f"[Scheduler] equipment_maintenance error: {e}")


def _job_renewal_notifications():
    try:
        from services.notification_service import notify_expiring_memberships
        count = notify_expiring_memberships(days=7)
        logger.info(f"[Scheduler] Renewal notifications: {count} members.")
    except Exception as e:
        logger.error(f"[Scheduler] renewal_notifications error: {e}")


def _job_auto_invoices():
    try:
        logger.info("[Scheduler] Auto invoice job triggered (27th of month).")
        from services.notification_service import push_notification
        push_notification(
            user_id=1,
            title="Monthly Invoice Job",
            message="Auto invoice generation triggered for the month.",
            notif_type="info"
        )
    except Exception as e:
        logger.error(f"[Scheduler] auto_invoices error: {e}")


def _job_overdue_alerts():
    try:
        from services.notification_service import notify_overdue_payments
        count = notify_overdue_payments()
        logger.info(f"[Scheduler] Overdue alerts: {count} payments.")
    except Exception as e:
        logger.error(f"[Scheduler] overdue_alerts error: {e}")
