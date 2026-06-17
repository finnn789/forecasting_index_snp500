"""
app/repositories/provider.py — Penyedia tunggal instance repository.

Menggantikan pola global `_repos` + `_get_repos()` yang sebelumnya
diduplikasi di tiap service. Pakai lru_cache supaya repositories
dibuat sekali (lazy) dan dipakai ulang.
"""

from __future__ import annotations

from functools import lru_cache

from app.repositories import Repositories, get_default_repositories


@lru_cache(maxsize=1)
def get_repositories() -> Repositories:
    """Kembalikan dict repositories yang sudah dikonfigurasi (cached)."""
    return get_default_repositories()  # type: ignore[return-value]
