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


# ── Distributed Lock Helper ────────────────────────────────────────────────────
import socket
import os

_LOCK_HOLDER_ID = f"{socket.gethostname()}:{os.getpid()}"

def _acquire_job_lock(job_name: str, lock_duration_minutes: int = 15) -> bool:
    """
    Attempt to acquire distributed job lock.
    Ensures only ONE running client instance executes scheduled maintenance.
    """
    try:
        from database.connection import DatabaseConnection
        with DatabaseConnection() as (conn, cursor):
            # 1. Clean up any expired locks
            cursor.execute("DELETE FROM sys_job_locks WHERE expires_at < CURRENT_TIMESTAMP")
            
            # 2. Try inserting our lock
            try:
                cursor.execute(
                    """
                    INSERT INTO sys_job_locks (job_name, locked_by, locked_at, expires_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP, DATEADD(day, 0, CURRENT_TIMESTAMP))
                    """,
                    (job_name, _LOCK_HOLDER_ID)
                )
                return True
            except Exception:
                # Primary key collision: another terminal holds active lock
                return False
    except Exception as e:
        logger.warning(f"[Scheduler] Could not verify job lock for '{job_name}': {e}. Proceeding locally.")
        return True


def _release_job_lock(job_name: str):
    """Release our lock after completion."""
    try:
        from database.connection import DatabaseConnection
        with DatabaseConnection() as (conn, cursor):
            cursor.execute("DELETE FROM sys_job_locks WHERE job_name = ? AND locked_by = ?",
                           (job_name, _LOCK_HOLDER_ID))
    except Exception as e:
        logger.debug(f"[Scheduler] Error releasing lock for '{job_name}': {e}")


# ── Job Implementations ────────────────────────────────────────────────────────

def _job_expire_memberships():
    if not _acquire_job_lock("expire_memberships"):
        logger.info("[Scheduler] 'expire_memberships' locked by another instance. Skipping.")
        return
    try:
        from services.member_service import update_expired_memberships
        count = update_expired_memberships()
        logger.info(f"[Scheduler] Expired {count} memberships.")
    except Exception as e:
        logger.error(f"[Scheduler] expire_memberships error: {e}")
    finally:
        _release_job_lock("expire_memberships")


def _job_overdue_payments():
    if not _acquire_job_lock("overdue_payments"):
        logger.info("[Scheduler] 'overdue_payments' locked by another instance. Skipping.")
        return
    try:
        from services.billing_service import mark_overdue_payments
        count = mark_overdue_payments()
        logger.info(f"[Scheduler] Marked {count} overdue payments.")
    except Exception as e:
        logger.error(f"[Scheduler] overdue_payments error: {e}")
    finally:
        _release_job_lock("overdue_payments")


def _job_equipment_maintenance():
    if not _acquire_job_lock("equipment_maintenance"):
        logger.info("[Scheduler] 'equipment_maintenance' locked by another instance. Skipping.")
        return
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
    finally:
        _release_job_lock("equipment_maintenance")


def _job_renewal_notifications():
    if not _acquire_job_lock("renewal_notifications"):
        logger.info("[Scheduler] 'renewal_notifications' locked by another instance. Skipping.")
        return
    try:
        from services.notification_service import notify_expiring_memberships
        count = notify_expiring_memberships(days=7)
        logger.info(f"[Scheduler] Renewal notifications: {count} members.")
    except Exception as e:
        logger.error(f"[Scheduler] renewal_notifications error: {e}")
    finally:
        _release_job_lock("renewal_notifications")


def _job_auto_invoices():
    if not _acquire_job_lock("auto_invoices"):
        logger.info("[Scheduler] 'auto_invoices' locked by another instance. Skipping.")
        return
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
    finally:
        _release_job_lock("auto_invoices")


def _job_overdue_alerts():
    if not _acquire_job_lock("overdue_alerts"):
        logger.info("[Scheduler] 'overdue_alerts' locked by another instance. Skipping.")
        return
    try:
        from services.notification_service import notify_overdue_payments
        count = notify_overdue_payments()
        logger.info(f"[Scheduler] Overdue alerts: {count} payments.")
    except Exception as e:
        logger.error(f"[Scheduler] overdue_alerts error: {e}")
    finally:
        _release_job_lock("overdue_alerts")
