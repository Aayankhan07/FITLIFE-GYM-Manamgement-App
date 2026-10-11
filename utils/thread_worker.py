"""FitLife — Thread Worker Utility"""
from PyQt6.QtCore import QThread, pyqtSignal
import logging

logger = logging.getLogger(__name__)


class Worker(QThread):
    """
    Generic QThread worker for running heavy tasks off the main thread.
    Usage:
        worker = Worker(my_function, arg1, arg2)
        worker.result.connect(lambda data: ...)
        worker.error.connect(lambda msg: ...)
        worker.finished.connect(lambda: ...)
        worker.start()
    """
    result       = pyqtSignal(object)
    token_result = pyqtSignal(int, object)
    error        = pyqtSignal(str)
    progress     = pyqtSignal(int)

    def __init__(self, fn, *args, token: int = 0, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.token = token
        self._is_cancelled = False

    def cancel(self):
        """Mark worker as superseded so results can be ignored."""
        self._is_cancelled = True

    def run(self):
        if self._is_cancelled:
            return
        try:
            result = self._fn(*self._args, **self._kwargs)
            if not self._is_cancelled:
                self.result.emit(result)
                self.token_result.emit(self.token, result)
        except Exception as e:
            if not self._is_cancelled:
                logger.error(f"Worker error in {self._fn.__name__}: {e}", exc_info=True)
                self.error.emit(str(e))
