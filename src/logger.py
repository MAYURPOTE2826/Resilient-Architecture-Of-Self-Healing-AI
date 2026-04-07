import logging
import os
from logging.handlers import RotatingFileHandler

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_LOG_DIR = os.path.join(_BASE_DIR, "logs")
os.makedirs(_LOG_DIR, exist_ok=True)

_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

# Rotate at 10 MB, keep 5 backups — prevents unbounded log growth
_file_handler = RotatingFileHandler(
    os.path.join(_LOG_DIR, "system.log"),
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
)
_file_handler.setFormatter(_formatter)

_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_formatter)

logger = logging.getLogger("self_healing_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # prevent duplicate output if root logger is configured
logger.addHandler(_file_handler)
logger.addHandler(_stream_handler)
