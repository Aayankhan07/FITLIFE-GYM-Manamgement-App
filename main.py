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
 
 
# ── Global Emoji Purger for clean professional design ────────────────────────
def strip_emojis(text: str) -> str:
    if not isinstance(text, str):
        return text
    chars = []
    for char in text:
        ord_c = ord(char)
        if (0x2600 <= ord_c <= 0x27BF) or (0x1F000 <= ord_c <= 0x1F9FF) or (0x1F600 <= ord_c <= 0x1F6FF) or (0x1F1E0 <= ord_c <= 0x1F1FF):
            continue
        if ord_c in (0x2139, 0x23F3, 0x23F0, 0x23E9, 0x23EA, 0x23EB, 0x23EC, 0x25B6, 0x25C0, 0x2705, 0xFE0F, 0x200D):
            continue
        chars.append(char)
    return "".join(chars).strip()
 
from PyQt6.QtWidgets import QLabel, QPushButton, QTabWidget, QTabBar
 
_orig_label_init = QLabel.__init__
_orig_label_set_text = QLabel.setText
 
def _safe_label_init(self, *args, **kwargs):
    if args and isinstance(args[0], str):
        args = (strip_emojis(args[0]),) + args[1:]
    elif "text" in kwargs and isinstance(kwargs["text"], str):
        kwargs["text"] = strip_emojis(kwargs["text"])
    _orig_label_init(self, *args, **kwargs)
 
def _safe_label_set_text(self, text: str):
    _orig_label_set_text(self, strip_emojis(text))
 
QLabel.__init__ = _safe_label_init
QLabel.setText = _safe_label_set_text
 
_orig_btn_init = QPushButton.__init__
_orig_btn_set_text = QPushButton.setText
 
def _safe_btn_init(self, *args, **kwargs):
    if args and isinstance(args[0], str):
        args = (strip_emojis(args[0]),) + args[1:]
    elif "text" in kwargs and isinstance(kwargs["text"], str):
        kwargs["text"] = strip_emojis(kwargs["text"])
    _orig_btn_init(self, *args, **kwargs)
 
def _safe_btn_set_text(self, text: str):
    _orig_btn_set_text(self, strip_emojis(text))
 
QPushButton.__init__ = _safe_btn_init
QPushButton.setText = _safe_btn_set_text
 
_orig_tab_add = QTabWidget.addTab
_orig_tab_insert = QTabWidget.insertTab
 
def _safe_tab_add(self, widget, label: str):
    return _orig_tab_add(self, widget, strip_emojis(label))
 
def _safe_tab_insert(self, index, widget, label: str):
    return _orig_tab_insert(self, index, widget, strip_emojis(label))
 
QTabWidget.addTab = _safe_tab_add
QTabWidget.insertTab = _safe_tab_insert
 
_orig_tabbar_set_text = QTabBar.setTabText
 
def _safe_tabbar_set_text(self, index, text: str):
    _orig_tabbar_set_text(self, index, strip_emojis(text))
 
QTabBar.setTabText = _safe_tabbar_set_text


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
