import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "absensi.log")

# Konfigurasi logger utama
logger = logging.getLogger("absensi_logger")
logger.setLevel(logging.INFO)

# Rotasi log (max 2MB x 5 file)
handler = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=5)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

def log_info(message):
    print("ℹ️ ", message)
    logger.info(message)

def log_error(message):
    print("❌", message)
    logger.error(message)

def log_warning(message):
    print("⚠️ ", message)
    logger.warning(message)
