"""
FitLife — Entry Point (Phase 9 Final)
Initialises logging, crash handler, high-DPI scaling, then starts the app.
"""
import sys
import os
import logging
from pathlib import Path

# ── Ensure project root is in sys.path ────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Logging ───────────────────────────────────────────────────────────────────
from utils.logging_config import setup_logging
setup_logging(log_dir=str(ROOT / "logs"))
logger = logging.getLogger(__name__)

# ── High-DPI environment var (must be before QApplication) ───────────────────
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def main():
    logger.info("=" * 60)
    logger.info("FitLife v1.0.0 starting")
    logger.info("=" * 60)
    # ── QApplication ──────────────────────────────────────────────────────────
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Base; QSS overrides everything
    try:
        app.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass

    # ── Global crash handler ──────────────────────────────────────────────────
    from utils.error_handler import CrashHandler
    CrashHandler.install()

    # ── Launch ────────────────────────────────────────────────────────────────
    from app import FitLifeApp
    fitlife = FitLifeApp()
    fitlife.app = app
    sys.exit(fitlife.run())


if __name__ == "__main__":
    main()
