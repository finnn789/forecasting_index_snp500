"""
app/core/state.py — Shared application state.

Menyimpan waktu startup server agar uptime bisa dihitung
dari semua modul tanpa circular import.
"""

import time

_startup_time: float = 0.0


def record_startup() -> None:
    """Dipanggil saat FastAPI startup event."""
    global _startup_time
    _startup_time = time.time()


def get_uptime() -> float:
    """Return uptime server dalam detik."""
    if _startup_time == 0.0:
        return 0.0
    return round(time.time() - _startup_time, 2)
