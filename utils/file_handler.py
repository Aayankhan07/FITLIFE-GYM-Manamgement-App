"""FitLife — File Handler Utility"""
import os
import shutil
import logging
from datetime import datetime
from typing import Optional
from config.constants import MAX_PHOTO_SIZE_BYTES, ALLOWED_PHOTO_EXTENSIONS

logger = logging.getLogger(__name__)
PHOTOS_DIR = os.path.join("assets", "photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)


def save_photo(source_path: str, entity_type: str, entity_id: int) -> dict:
    """Copy a photo to the assets directory and return the stored path."""
    try:
        if not os.path.exists(source_path):
            return {"success": False, "message": "Source file not found."}

        ext = os.path.splitext(source_path)[1].lower()
        if ext not in ALLOWED_PHOTO_EXTENSIONS:
            return {"success": False,
                    "message": f"Invalid file type. Allowed: {', '.join(ALLOWED_PHOTO_EXTENSIONS)}"}

        size = os.path.getsize(source_path)
        if size > MAX_PHOTO_SIZE_BYTES:
            mb = MAX_PHOTO_SIZE_BYTES / (1024 * 1024)
            return {"success": False, "message": f"File too large. Max size: {mb:.0f} MB"}

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{entity_type}_{entity_id}_{timestamp}{ext}"
        dest_path = os.path.join(PHOTOS_DIR, filename)
        shutil.copy2(source_path, dest_path)
        logger.info(f"Photo saved: {dest_path}")
        return {"success": True, "path": dest_path}

    except Exception as e:
        logger.error(f"save_photo error: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to save photo: {e}"}


def delete_photo(photo_path: str) -> bool:
    """Delete a photo file."""
    try:
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)
            logger.info(f"Photo deleted: {photo_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"delete_photo error: {e}")
        return False


def get_photo_path(stored_path: Optional[str]) -> Optional[str]:
    """Return the photo path if it exists on disk."""
    if not stored_path:
        return None
    if os.path.exists(stored_path):
        return stored_path
    return None


def ensure_dir(path: str) -> str:
    """Create directory if it doesn't exist, return path."""
    os.makedirs(path, exist_ok=True)
    return path


def get_report_path(filename: str) -> str:
    """Return full path for a report file."""
    reports_dir = ensure_dir("reports")
    return os.path.join(reports_dir, filename)


def open_file(path: str) -> bool:
    """Open a file with the default system application."""
    try:
        import subprocess
        subprocess.Popen(["explorer", path], shell=True)
        return True
    except Exception as e:
        logger.error(f"open_file error: {e}")
        return False
