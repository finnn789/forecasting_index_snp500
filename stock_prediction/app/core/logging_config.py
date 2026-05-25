"""
app/core/logging_config.py — Konfigurasi logging terpusat.

Komponen dan file log:
  app.*        → logs/app.log          (startup, shutdown, error umum)
  app.api.*    → logs/api/api.log      (request, response, routes)
  pipeline.*   → logs/pipeline/pipeline.log  (ingestion, preprocessing, feature eng.)
  models.*     → logs/models/models.log      (LSTM, FinBERT, ensemble)

Setiap file menggunakan RotatingFileHandler (max 5 MB, 3 backup).
Log juga diteruskan ke console (stdout).
"""

import logging
import logging.handlers
from pathlib import Path

# ---------------------------------------------------------------------------
# Konfigurasi
# ---------------------------------------------------------------------------
LOG_DIR      = Path("logs")
LOG_LEVEL    = logging.INFO
MAX_BYTES    = 5 * 1024 * 1024   # 5 MB
BACKUP_COUNT = 3

LOG_FORMAT  = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Peta: prefix logger → path file log
_COMPONENT_MAP: dict[str, Path] = {
    "app.api":  LOG_DIR / "api"      / "api.log",
    "pipeline": LOG_DIR / "pipeline" / "pipeline.log",
    "models":   LOG_DIR / "models"   / "models.log",
    "app":      LOG_DIR / "app.log",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rotating_handler(path: Path) -> logging.handlers.RotatingFileHandler:
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        filename=path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    return handler


def _console_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    return handler


# ---------------------------------------------------------------------------
# Setup utama — dipanggil sekali saat server startup
# ---------------------------------------------------------------------------

def setup_logging() -> None:
    """
    Inisialisasi sistem logging seluruh aplikasi.
    Wajib dipanggil sebelum komponen lain berjalan.
    """
    # Root logger — tangkap semua, teruskan ke console
    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)

    if not root.handlers:
        root.addHandler(_console_handler())

    # Logger per komponen — tambah file handler khusus
    for prefix, log_path in _COMPONENT_MAP.items():
        logger = logging.getLogger(prefix)
        logger.setLevel(LOG_LEVEL)

        # Hindari duplikat handler jika setup_logging() dipanggil lebih dari sekali
        existing_files = {
            h.baseFilename
            for h in logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
        }
        if str(log_path.resolve()) not in existing_files:
            logger.addHandler(_rotating_handler(log_path))

        # Propagate ke root (agar tetap muncul di console)
        logger.propagate = True

    logging.getLogger(__name__).info(
        "Logging aktif — level: %s | komponen: %s",
        logging.getLevelName(LOG_LEVEL),
        list(_COMPONENT_MAP.keys()),
    )
