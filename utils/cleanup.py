# cleanup.py - Temp file cleanup utilities

import os
import time
import logging

from config import TEMP_DIRECTORY

logger = logging.getLogger(__name__)


def cleanup_temp_directory():
    """Remove files older than 1 hour from temp directory."""
    if not os.path.exists(TEMP_DIRECTORY):
        return

    now = time.time()
    removed = 0
    for f in os.listdir(TEMP_DIRECTORY):
        path = os.path.join(TEMP_DIRECTORY, f)
        try:
            if os.path.isfile(path) and (now - os.path.getmtime(path)) > 3600:
                os.unlink(path)
                removed += 1
        except Exception as e:
            logger.warning(f"Failed to remove temp file {path}: {e}")

    if removed:
        logger.info(f"Cleaned up {removed} old temp files")
