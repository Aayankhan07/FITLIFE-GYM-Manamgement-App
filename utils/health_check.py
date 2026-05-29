"""FitLife — Startup Health Check (Phase 8)
Run before showing the main window to verify all dependencies are satisfied.
"""
import sys
import logging
import importlib
from database.connection import test_connection

logger = logging.getLogger(__name__)

REQUIRED_PACKAGES = [
    ("PyQt6",       "PyQt6"),
    ("pyodbc",      "pyodbc"),
    ("bcrypt",      "bcrypt"),
]

REQUIRED_SERVICES = [
    "services.auth_service",
    "services.member_service",
    "services.trainer_service",
    "services.branch_service",
    "services.billing_service",
    "services.attendance_service",
    "services.equipment_service",
    "services.schedule_service",
    "services.staff_service",
    "services.analytics_service",
    "services.reports_service",
    "services.settings_service",
]


def check_packages() -> list[str]:
    """Returns list of missing package names."""
    missing = []
    for display_name, import_name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(display_name)
            logger.error(f"Missing package: {display_name}")
    return missing


def check_services() -> list[str]:
    """Returns list of service modules that failed to import."""
    failed = []
    for mod_name in REQUIRED_SERVICES:
        try:
            importlib.import_module(mod_name)
        except Exception as e:
            failed.append(mod_name)
            logger.error(f"Service import failed [{mod_name}]: {e}")
    return failed


def check_database() -> tuple[bool, str]:
    """Returns (ok, message)."""
    try:
        ok, msg = test_connection()
        return ok, msg
    except Exception as e:
        return False, str(e)


def run_health_check(skip_db: bool = False) -> dict:
    """
    Runs all startup checks.
    Returns {
        "ok": bool,
        "missing_packages": [...],
        "failed_services": [...],
        "db_ok": bool,
        "db_message": str,
    }
    """
    missing_pkgs = check_packages()
    failed_svcs  = check_services()
    db_ok, db_msg = (True, "Skipped") if skip_db else check_database()

    all_ok = not missing_pkgs and not failed_svcs and db_ok

    result = {
        "ok": all_ok,
        "missing_packages": missing_pkgs,
        "failed_services": failed_svcs,
        "db_ok": db_ok,
        "db_message": db_msg,
    }

    if all_ok:
        logger.info("Startup health check PASSED.")
    else:
        logger.warning(f"Startup health check FAILED: {result}")

    return result
