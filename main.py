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
 
# ── Patch QScrollArea.setStyleSheet to prevent broad QWidget style overrides ──
from PyQt6.QtWidgets import QScrollArea
_orig_scroll_set_stylesheet = QScrollArea.setStyleSheet
 
def _safe_scroll_set_stylesheet(self, style: str):
    cleaned = style.strip().replace(" ", "").replace("\n", "").replace("\r", "")
    if "QWidget{border:none;background:transparent" in cleaned:
        style = "QScrollArea { border: none; background: transparent; }"
    _orig_scroll_set_stylesheet(self, style)
 
QScrollArea.setStyleSheet = _safe_scroll_set_stylesheet


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

    # ── Load premium application fonts ────────────────────────────────────────
    from PyQt6.QtGui import QFontDatabase, QFont, QIcon, QPixmap, QPainter, QRadialGradient, QColor
    reg_path = ROOT / "assets" / "fonts" / "Inter-Regular.ttf"
    bold_path = ROOT / "assets" / "fonts" / "Inter-Bold.ttf"
    if reg_path.exists():
        QFontDatabase.addApplicationFont(str(reg_path))
    if bold_path.exists():
        QFontDatabase.addApplicationFont(str(bold_path))
    
    app.setFont(QFont("Inter", 10))

    # ── Custom App Icon ───────────────────────────────────────────────────────
    def create_app_icon():
        pixmap = QPixmap(128, 128)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Soft glowing circular gradient background
        grad = QRadialGradient(64, 64, 60)
        grad.setColorAt(0.0, QColor("#0066FF"))  # Blue primary
        grad.setColorAt(1.0, QColor("#0A0E2A"))  # Dark body
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(4, 4, 120, 120, 28, 28)
        
        # Icon emoji centered
        font = QFont("Inter", 54)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "💪")
        painter.end()
        return QIcon(pixmap)

    app.setWindowIcon(create_app_icon())

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
