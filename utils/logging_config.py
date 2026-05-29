"""FitLife — Logging Configuration (Phase 8)
Call setup_logging() once at app startup.
"""
import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging(log_dir: str = "logs", level: int = logging.INFO) -> None:
    """Configure rotating file + console logging."""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = os.path.join(log_dir, "fitlife.log")

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # ── Rotating file handler (10 MB × 5 backups) ─────────────────────────────
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(level)

    # ── Console handler ───────────────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        "%(levelname)-8s | %(name)s | %(message)s"
    ))
    console_handler.setLevel(logging.WARNING)

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers on reload
    if not root.handlers:
        root.addHandler(file_handler)
        root.addHandler(console_handler)

    # Silence noisy third-party loggers
    for noisy in ["pyodbc", "urllib3", "PIL"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).info("Logging initialised — output: %s", log_file)
