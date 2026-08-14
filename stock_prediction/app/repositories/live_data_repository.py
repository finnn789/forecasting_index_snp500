"""
app/repositories/live_data_repository.py — Penyimpanan akumulasi data live
(OHLCV + headline berita) untuk fitur "Prediksi Live" di Dashboard.

Beda dari `StockRepository`/`NewsRepository` (CSV statis, data latih resmi
2018-2024): repository ini SQLite (stdlib `sqlite3`, tanpa dependency baru),
dipilih karena data live datang bertahap tiap kali user fetch (buka Dashboard/
klik prediksi) dan perlu di-*upsert* + dedup lintas waktu — cocok untuk primary
key + INSERT OR REPLACE, bukan rewrite CSV penuh tiap kali.

Tabel:
  - ohlcv(date TEXT PRIMARY KEY, open, high, low, close, volume, fetched_at)
  - headlines(title TEXT, date TEXT, published_at TEXT, sentiment_label,
    sentiment_score, sentiment_numeric, fetched_at, PRIMARY KEY (title, date))

`date` = tanggal kalender (YYYY-MM-DD, dinormalisasi ke tengah malam) — dipakai
untuk JOIN harian ke OHLCV (`build_live_return_features`). `published_at` =
timestamp ASLI publikasi (ISO datetime, TIDAK dinormalisasi) — dipakai KHUSUS
untuk mengurutkan daftar "headline terbaru" (`get_live_news_latest`). Bug yang
diperbaiki: sebelum `published_at` ada, urutan disortir cuma per-`date` (grain
harian) — begitu satu hari terakumulasi banyak headline (>10), 10 teratas yang
ditampilkan jadi tidak benar-benar yang terbaru (tie-break SQLite arbitrer,
bukan kronologis), sehingga daftar berita terlihat "tidak fetching berita
baru" walau di baliknya akumulasi berjalan normal.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ohlcv (
    date TEXT PRIMARY KEY,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS headlines (
    title TEXT NOT NULL,
    date TEXT NOT NULL,
    published_at TEXT NOT NULL,
    sentiment_label TEXT NOT NULL,
    sentiment_score REAL NOT NULL,
    sentiment_numeric INTEGER NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (title, date)
);
"""


class LiveDataRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)
            self._migrate_published_at(conn)

    @staticmethod
    def _migrate_published_at(conn: sqlite3.Connection) -> None:
        """Migrasi DB lama (sebelum kolom `published_at` ada): tambah kolom +
        backfill dari `date` (tengah hari, perkiraan terbaik — data lama tidak
        punya jam publikasi asli)."""
        cols = {row[1] for row in conn.execute("PRAGMA table_info(headlines)")}
        if "published_at" not in cols:
            conn.execute("ALTER TABLE headlines ADD COLUMN published_at TEXT")
            conn.execute(
                "UPDATE headlines SET published_at = date || 'T12:00:00Z' "
                "WHERE published_at IS NULL"
            )

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # OHLCV
    # ------------------------------------------------------------------

    def upsert_ohlcv(self, df: pd.DataFrame, fetched_at: str) -> None:
        """`df` wajib punya kolom Date/Open/High/Low/Close/Volume — Date
        di-`.strftime('%Y-%m-%d')` sebelum disimpan. INSERT OR REPLACE keyed
        by date — fetch terbaru menimpa nilai lama (harga bisa direvisi
        sepanjang hari bursa berjalan)."""
        if df.empty:
            return
        rows = [
            (
                d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d),
                float(o), float(h), float(low_), float(c), float(v), fetched_at,
            )
            for d, o, h, low_, c, v in zip(
                df["Date"], df["Open"], df["High"], df["Low"], df["Close"], df["Volume"], strict=True
            )
        ]
        with self._connect() as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO ohlcv (date, open, high, low, close, volume, fetched_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                rows,
            )

    def load_ohlcv(self) -> pd.DataFrame:
        with self._connect() as conn:
            df = pd.read_sql_query(
                "SELECT date AS Date, open AS Open, high AS High, low AS Low, "
                "close AS Close, volume AS Volume FROM ohlcv ORDER BY date ASC",
                conn,
            )
        df["Date"] = pd.to_datetime(df["Date"])
        return df

    # ------------------------------------------------------------------
    # Headlines
    # ------------------------------------------------------------------

    def existing_headline_keys(self) -> set[tuple[str, str]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT title, date FROM headlines").fetchall()
        return {(t, d) for t, d in rows}

    def upsert_headlines(self, df: pd.DataFrame, fetched_at: str) -> None:
        """`df` wajib punya kolom Title/Date/PublishedAt/sentiment_label/
        sentiment_score/sentiment_numeric — sudah di-score FinBERT (lihat
        `score_headlines_live`)."""
        if df.empty:
            return
        rows = [
            (
                str(t),
                d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d),
                p.isoformat() if hasattr(p, "isoformat") else str(p),
                str(lbl), float(score), int(num), fetched_at,
            )
            for t, d, p, lbl, score, num in zip(
                df["Title"], df["Date"], df["PublishedAt"], df["sentiment_label"],
                df["sentiment_score"], df["sentiment_numeric"], strict=True
            )
        ]
        with self._connect() as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO headlines "
                "(title, date, published_at, sentiment_label, sentiment_score, sentiment_numeric, fetched_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                rows,
            )

    def load_headlines(self) -> pd.DataFrame:
        """Terurut `published_at` DESC (kronologis sungguhan) — BUKAN cuma
        `date` DESC (grain harian, lihat catatan bug di docstring modul)."""
        with self._connect() as conn:
            df = pd.read_sql_query(
                "SELECT title AS Title, date AS Date, published_at AS PublishedAt, "
                "sentiment_label, sentiment_score, sentiment_numeric "
                "FROM headlines ORDER BY published_at DESC",
                conn,
            )
        df["Date"] = pd.to_datetime(df["Date"])
        # format="mixed": baris lama (migrasi, backfill "...T12:00:00Z") dan
        # baris baru (Timestamp.isoformat() tz-naive, TANPA "Z") tersimpan
        # dalam format string yang beda persis — pd.to_datetime tanpa
        # format="mixed" gagal total (ValueError) begitu 1 kolom berisi
        # campuran keduanya, bukan cuma parse baris yg salah format.
        # utc=True: format="mixed" saja masih gagal ("Mixed timezones
        # detected") begitu sebagian baris tz-aware ("...Z") dan sebagian
        # tz-naive dalam 1 kolom yg sama — paksa semua ke UTC lalu buang tz
        # (kolom lain di modul ini konsisten tz-naive).
        df["PublishedAt"] = pd.to_datetime(df["PublishedAt"], format="mixed", utc=True).dt.tz_localize(None)
        return df
