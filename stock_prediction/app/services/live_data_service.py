"""
app/services/live_data_service.py — Fetch data live (OHLCV + headline S&P 500)
via yfinance untuk fitur "Prediksi Live" di Dashboard, lalu preprocessing
(cleaning, FinBERT scoring, agregasi sentimen harian, return features) supaya
siap dipakai `models/lstm/notebook07_common.py::predict_live_notebook07()`.

Sumber data:
- OHLCV: `yfinance.Ticker("^GSPC").history()` — ticker sama dengan CSV historis
  (`data/raw/stocks/GSPC_*.csv`).
- Berita: `yfinance.Ticker("^GSPC").get_news()` — TANPA API key, TAPI cakupan
  hanya ~1-2 hari kalender terakhir (dikonfirmasi smoke test manual: `count=50`
  tetap cuma 2 hari unik — yfinance mengembalikan berita TERKINI, bukan arsip
  per-tanggal).

**Akumulasi lintas-fetch (SQLite, `app/repositories/live_data_repository.py`,
keputusan user):** supaya cakupan sentimen harian tidak cuma 1-2 hari tiap
kali fetch, setiap OHLCV/headline yang berhasil di-fetch di-*upsert* ke
`LiveDataRepository` (keyed by date / (title,date)) — jadi tiap kali Dashboard
dibuka atau prediksi dijalankan, hari-hari yang PERNAH punya liputan berita
tetap tersimpan dan ikut diagregasi, bukan hilang begitu yfinance berhenti
mengembalikannya di `.get_news()`. `build_live_return_features()` tetap pakai
LEFT JOIN + neutral-fill (`sentiment_mean=0`, `sentiment_is_live=False`) untuk
hari yang MEMANG belum pernah punya liputan berita sama sekali di histori
akumulasi.

`sentiment_mean` dihitung dengan formula PERSIS `sentiment_service._aggregate_daily()`
(rata-rata sederhana `sentiment_numeric`) — reuse langsung, BUKAN reimplement —
supaya konsisten dengan data yang dipakai melatih model (bukan metode
probability-weighted `signed_score` di `scripts/process_new_scraped_data.py`).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf

from app.core.exceptions import ExternalServiceError
from app.repositories.provider import get_repositories
from app.services.sentiment_service import _aggregate_daily, _resolve_model_path
from pipeline.preprocessing.stock_preprocessor import StockPreprocessor
from pipeline.preprocessing.text_preprocessor import TextPreprocessor

logger = logging.getLogger(__name__)

TICKER = "^GSPC"
RETURN_COLS = ["ret_open", "ret_high", "ret_low", "ret_close", "ret_volume"]


def fetched_at_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_live_ohlcv(period: str = "90d") -> pd.DataFrame:
    """Fetch OHLCV live via yfinance, bersihkan lewat `StockPreprocessor` (reuse
    produksi), upsert ke `LiveDataRepository` (akumulasi, keyed by date — fetch
    terbaru menimpa nilai lama), lalu return SELURUH histori akumulasi (bukan
    cuma batch yang baru di-fetch) supaya histori live tumbuh dari waktu ke
    waktu, tidak terbatas ke window `period` yfinance."""
    try:
        raw = yf.Ticker(TICKER).history(period=period)
    except Exception as e:  # noqa: BLE001 — jaringan/yfinance, wajib dilaporkan apa adanya
        raise ExternalServiceError(f"Gagal fetch OHLCV live dari yfinance: {e}") from e

    if raw is None or raw.empty:
        raise ExternalServiceError("yfinance mengembalikan data OHLCV kosong.")

    df = raw.reset_index()
    date_col = "Date" if "Date" in df.columns else "Datetime"
    df = df.rename(columns={date_col: "Date"})
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.normalize()
    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
    df_clean = StockPreprocessor().clean(df)

    repo = get_repositories()["live_data"]
    repo.upsert_ohlcv(df_clean, fetched_at=fetched_at_iso())
    return repo.load_ohlcv()


def fetch_live_headlines() -> pd.DataFrame:
    """Fetch headline berita live via yfinance `.get_news()` (TANPA API key).
    Return DataFrame kolom Title/Date/PublishedAt — `Date` = tanggal kalender
    publikasi (dinormalisasi ke tengah malam, dipakai untuk JOIN harian ke
    OHLCV), `PublishedAt` = timestamp ASLI publikasi dari `pubDate` (TIDAK
    dinormalisasi, dipakai untuk mengurutkan daftar headline terbaru — lihat
    catatan bug di `app/repositories/live_data_repository.py`). Sudah
    difilter judul kosong/duplikat/<3 kata (pola sama
    `scripts/process_new_scraped_data.py::clean_headlines`). BELUM di-score/
    di-akumulasi — lihat `fetch_score_and_accumulate_headlines()`."""
    try:
        items = yf.Ticker(TICKER).get_news(count=50)
    except Exception as e:  # noqa: BLE001
        raise ExternalServiceError(f"Gagal fetch berita live dari yfinance: {e}") from e

    rows = []
    for item in items or []:
        content = item.get("content", {})
        title = (content.get("title") or "").strip()
        pub_date = content.get("pubDate")
        if not title or not pub_date:
            continue
        published_at = pd.to_datetime(pub_date).tz_localize(None)
        rows.append({"Title": title, "Date": published_at.normalize(), "PublishedAt": published_at})

    df = pd.DataFrame(rows, columns=["Title", "Date", "PublishedAt"])
    if df.empty:
        return df

    df = df.drop_duplicates(subset=["Title", "Date"]).reset_index(drop=True)
    df = df[df["Title"].str.split().str.len() >= 3].reset_index(drop=True)
    return df


def score_headlines_live(df_headlines: pd.DataFrame) -> pd.DataFrame:
    """FinBERT scoring per headline (reuse `TextPreprocessor`, path resolve sama
    dengan `sentiment_service._resolve_model_path()`)."""
    if df_headlines.empty:
        return df_headlines.assign(sentiment_label=[], sentiment_score=[], sentiment_numeric=[])

    preprocessor = TextPreprocessor(
        model_path=_resolve_model_path(),
        batch_size=32,
        device=int(os.environ.get("FINBERT_DEVICE", 0)),
    )
    return preprocessor.extract_sentiment_scores(df_headlines, text_column="Title")


def fetch_score_and_accumulate_headlines() -> pd.DataFrame:
    """Fetch headline live terbaru, score HANYA yang benar-benar baru (skip
    (title,date) yang sudah pernah di-score & tersimpan — hindari FinBERT
    berulang untuk headline yang sama yang masih muncul di `.get_news()`),
    upsert ke `LiveDataRepository`, lalu return SELURUH histori akumulasi
    (bukan cuma batch baru) — dipakai `aggregate_daily_live()` supaya cakupan
    sentimen harian bertambah tiap kali Dashboard dibuka/prediksi dijalankan,
    bukan cuma dari fetch hari ini saja (keputusan user)."""
    df_new_raw = fetch_live_headlines()
    repo = get_repositories()["live_data"]

    if not df_new_raw.empty:
        existing_keys = repo.existing_headline_keys()
        if existing_keys:
            new_keys = list(zip(df_new_raw["Title"], df_new_raw["Date"].dt.strftime("%Y-%m-%d")))
            is_new = [key not in existing_keys for key in new_keys]
            df_to_score = df_new_raw[is_new].reset_index(drop=True)
        else:
            df_to_score = df_new_raw

        if not df_to_score.empty:
            df_scored_new = score_headlines_live(df_to_score)
            repo.upsert_headlines(df_scored_new, fetched_at=fetched_at_iso())

    return repo.load_headlines()


def aggregate_daily_live(df_scored: pd.DataFrame) -> pd.DataFrame:
    """Agregasi harian — reuse formula PERSIS `sentiment_service._aggregate_daily()`
    (rata-rata sederhana `sentiment_numeric`), supaya konsisten dengan data yang
    dipakai melatih model."""
    if df_scored.empty:
        return pd.DataFrame(
            columns=[
                "Date", "headline_count", "sentiment_mean",
                "sentiment_pos", "sentiment_neg", "sentiment_neu", "sentiment_label",
            ]
        )
    return _aggregate_daily(df_scored)


def build_live_return_features(
    df_ohlcv_clean: pd.DataFrame, df_daily_sentiment: pd.DataFrame
) -> pd.DataFrame:
    """LEFT JOIN OHLCV (semua hari bursa live) + sentimen harian live on Date —
    BEDA dari `dataset_builder.load_return_features()` statis (inner join),
    karena cakupan berita live yfinance cuma ~1-2 hari (lihat docstring modul).
    Hari tanpa liputan berita diisi `sentiment_mean=0` (netral) +
    `sentiment_is_live=False`, supaya window=20 tetap bisa terbentuk (keputusan
    user, lihat CLAUDE.md log fitur Prediksi Live)."""
    df = df_ohlcv_clean.copy()
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()

    if df_daily_sentiment.empty:
        df["sentiment_mean"] = 0.0
        df["sentiment_is_live"] = False
    else:
        sent = df_daily_sentiment[["Date", "sentiment_mean"]].copy()
        sent["Date"] = pd.to_datetime(sent["Date"]).dt.normalize()
        sent["sentiment_is_live"] = True
        df = df.merge(sent, on="Date", how="left")
        df["sentiment_is_live"] = df["sentiment_is_live"].fillna(False)
        df["sentiment_mean"] = df["sentiment_mean"].fillna(0.0)

    df = df.sort_values("Date").reset_index(drop=True)

    df["ret_open"] = df["Open"].pct_change()
    df["ret_high"] = df["High"].pct_change()
    df["ret_low"] = df["Low"].pct_change()
    df["ret_close"] = df["Close"].pct_change()
    df["ret_volume"] = df["Volume"].pct_change()
    df[RETURN_COLS] = df[RETURN_COLS].replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=RETURN_COLS).reset_index(drop=True)

    return df[["Date", *RETURN_COLS, "sentiment_mean", "sentiment_is_live", "Close"]]


# ---------------------------------------------------------------------------
# Service-level — dipakai langsung oleh app/api/v1/routes_live.py (GET
# endpoints, non-SSE). Orkestrasi predict SSE ada di live_prediction_service.py.
# ---------------------------------------------------------------------------

def get_live_stock_latest(n: int = 30) -> dict:
    df = fetch_live_ohlcv().sort_values("Date").reset_index(drop=True)
    tail = df.tail(n).reset_index(drop=True)
    tail_json = tail.copy()
    tail_json["Date"] = tail_json["Date"].dt.strftime("%Y-%m-%d")
    last_row = tail.iloc[-1]
    return {
        "columns": tail_json.columns.tolist(),
        "n": len(tail_json),
        "rows": tail_json.to_dict(orient="records"),
        "latest_date": last_row["Date"].strftime("%Y-%m-%d"),
        "latest_close": float(last_row["Close"]),
        "fetched_at": fetched_at_iso(),
    }


def get_live_news_latest(n: int = 10) -> dict:
    df_scored = fetch_score_and_accumulate_headlines()
    df_daily = aggregate_daily_live(df_scored)

    headlines_tail = df_scored.head(n)  # sudah terurut PublishedAt DESC (load_headlines())
    headlines = [
        {
            "title": row["Title"],
            "date": row["Date"].strftime("%Y-%m-%d"),
            "sentiment_label": row["sentiment_label"],
            "sentiment_score": float(row["sentiment_score"]),
        }
        for _, row in headlines_tail.iterrows()
    ]

    daily_sentiment = [
        {
            "date": row["Date"].strftime("%Y-%m-%d"),
            "headline_count": int(row["headline_count"]),
            "sentiment_mean": float(row["sentiment_mean"]),
            "sentiment_label": row["sentiment_label"],
        }
        for _, row in df_daily.sort_values("Date", ascending=False).iterrows()
    ]

    return {
        "headlines": headlines,
        "daily_sentiment": daily_sentiment,
        "accumulated_days": len(daily_sentiment),
        "fetched_at": fetched_at_iso(),
    }
