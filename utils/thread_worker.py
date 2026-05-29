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
    result   = pyqtSignal(object)
    error    = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.result.emit(result)
        except Exception as e:
            logger.error(f"Worker error in {self._fn.__name__}: {e}", exc_info=True)
            self.error.emit(str(e))
