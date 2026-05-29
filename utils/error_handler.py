"""FitLife — Global Error Handler (Phase 8)
Catches all unhandled exceptions, shows crash dialog, writes log.
"""
import sys, traceback, logging
from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


class CrashHandler:
    """Install as sys.excepthook to catch all unhandled exceptions."""

    @staticmethod
    def handle(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb); return

        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logger.critical(f"UNHANDLED EXCEPTION:\n{tb_str}")

        app = QApplication.instance()
        if app:
            dlg = QMessageBox()
            dlg.setWindowTitle("FitLife — Unexpected Error")
            dlg.setIcon(QMessageBox.Icon.Critical)
            dlg.setText("<b>An unexpected error occurred.</b>")
            dlg.setInformativeText(
                "The application encountered an error.\n"
                "Your data has been preserved. Please restart FitLife.\n\n"
                f"Error: {exc_type.__name__}: {exc_value}"
            )
            dlg.setDetailedText(tb_str)
            dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
            dlg.exec()

    @staticmethod
    def install():
        sys.excepthook = CrashHandler.handle
        logger.info("Global crash handler installed.")
