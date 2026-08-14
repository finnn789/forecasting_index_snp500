"""Preprocessing pipeline (isolated, TIDAK menimpa artefak resmi project) untuk
data baru user: D:/scrapping_news_headline/data/{sp500_headlines,sp500_ohlcv}.csv

Tahapan (reuse komponen project, bukan reimplement):
  1. FinBERT Scoring   -> pipeline.preprocessing.text_preprocessor.TextPreprocessor
  2. Aggregate harian  -> logic sama dgn scripts/regenerate_sentiment_weighted.py
  3. Clean OHLCV       -> pipeline.preprocessing.stock_preprocessor.StockPreprocessor
  4. Merge (inner join on Date)
  5. Stasioner-kan     -> pct_change (sama dgn dataset_builder.load_return_features)

Output disimpan ke scripts/new_data_output/ (terpisah), BUKAN ke data/processed/
resmi project — supaya tidak bentrok dengan dataset training resmi.

STATUS (2026-07-31): 14 baris final (setelah stasioner) vs window=20 skripsi-
scoped -> 0 sampel windowed. TIDAK CUKUP untuk training/inference LSTM sendirian.
Ada gap ~2.3 tahun antara akhir data historis resmi (2024-03-04) dan awal data
baru ini (2026-07-10). User memutuskan (2026-07-31): SIMPAN dulu, tunggu diminta
lagi nanti ("baca memory") sebelum lanjut ke opsi appending/prediksi.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("E:/forecasting_index_snp500/stock_prediction")
sys.path.insert(0, str(ROOT))
import os

os.chdir(ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("process_new_data")

NEW_HEADLINES_CSV = Path("D:/scrapping_news_headline/data/sp500_headlines.csv")
NEW_OHLCV_CSV = Path("D:/scrapping_news_headline/data/sp500_ohlcv.csv")

OUT_DIR = Path(__file__).resolve().parent / "new_data_output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FINBERT_PATH = str(ROOT / "models/finbert/models--ProsusAI--finbert")
NEUTRAL_BAND = 0.05
WINDOW = 20  # sama dengan skripsi-scoped (notebook07_trainer.WINDOW)


def clean_headlines(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Title"] = df["Title"].astype(str).str.strip()
    before = len(df)
    df = df[df["Title"].notna() & (df["Title"] != "") & (df["Title"] != "nan")]
    logger.info("Drop kosong: %d -> %d", before, len(df))
    before = len(df)
    df = df.drop_duplicates(subset=["Title", "Date"])
    logger.info("Drop duplikat: %d -> %d", before, len(df))
    before = len(df)
    df = df[df["Title"].str.split().str.len() >= 3]
    logger.info("Filter <3 kata: %d -> %d", before, len(df))
    return df.reset_index(drop=True)


def aggregate_daily(df_scored: pd.DataFrame, neutral_band: float = NEUTRAL_BAND) -> pd.DataFrame:
    df = df_scored.copy()
    df["signed_score"] = df["sentiment_numeric"] * df["sentiment_score"]
    grp = df.groupby("Date")
    daily = pd.DataFrame()
    daily["headline_count"] = grp["Title"].count()
    daily["sentiment_mean"] = grp["signed_score"].mean().round(6)

    def prop(g, label):
        return (g == label).sum() / len(g) if len(g) > 0 else 0.0

    daily["sentiment_pos"] = grp["sentiment_label"].apply(lambda g: prop(g, "positive")).round(6)
    daily["sentiment_neg"] = grp["sentiment_label"].apply(lambda g: prop(g, "negative")).round(6)
    daily["sentiment_neu"] = grp["sentiment_label"].apply(lambda g: prop(g, "neutral")).round(6)
    daily["sentiment_label"] = daily["sentiment_mean"].apply(
        lambda v: "neutral" if abs(v) < neutral_band else ("positive" if v > 0 else "negative")
    )
    daily = daily.reset_index()
    daily["Date"] = pd.to_datetime(daily["Date"]).dt.strftime("%Y-%m-%d")
    return daily


def main() -> None:
    import torch
    from pipeline.preprocessing.stock_preprocessor import StockPreprocessor
    from pipeline.preprocessing.text_preprocessor import TextPreprocessor

    device = 0 if torch.cuda.is_available() else -1

    # =====================================================================
    # STEP 1+2: FinBERT Scoring + Aggregate Harian (headline)
    # =====================================================================
    logger.info("=" * 70)
    logger.info("STEP 1: Muat + Clean headline mentah")
    logger.info("=" * 70)
    df_raw = pd.read_csv(NEW_HEADLINES_CSV)
    logger.info("Raw headlines: %d baris", len(df_raw))
    df_clean = clean_headlines(df_raw)

    logger.info("=" * 70)
    logger.info("STEP 2: FinBERT Scoring (%d headline, device=%s)", len(df_clean), "GPU" if device == 0 else "CPU")
    logger.info("=" * 70)
    preprocessor = TextPreprocessor(model_path=FINBERT_PATH, batch_size=32, device=device)
    df_scored = preprocessor.extract_sentiment_scores(df_clean, text_column="Title")
    logger.info("Distribusi label: %s", df_scored["sentiment_label"].value_counts().to_dict())

    logger.info("=" * 70)
    logger.info("STEP 3: Agregasi Harian (probability-weighted)")
    logger.info("=" * 70)
    df_daily = aggregate_daily(df_scored)
    daily_path = OUT_DIR / "new_headlines_daily_sentiment.csv"
    df_daily.to_csv(daily_path, index=False)
    logger.info("Tersimpan: %s (%d hari unik)", daily_path, len(df_daily))
    print(df_daily.to_string(index=False))

    # =====================================================================
    # STEP 4: Clean OHLCV baru
    # =====================================================================
    logger.info("=" * 70)
    logger.info("STEP 4: Clean OHLCV baru (StockPreprocessor, reuse produksi)")
    logger.info("=" * 70)
    sp = StockPreprocessor()
    df_ohlcv_raw = sp.load_csv(NEW_OHLCV_CSV)
    df_ohlcv_clean = sp.clean(df_ohlcv_raw)

    # =====================================================================
    # STEP 5: Merge (inner join on Date)
    # =====================================================================
    logger.info("=" * 70)
    logger.info("STEP 5: Merge OHLCV + Sentimen Harian (inner join on Date)")
    logger.info("=" * 70)
    df_daily["Date"] = pd.to_datetime(df_daily["Date"])
    df_joined = pd.merge(
        df_ohlcv_clean[["Date", "Open", "High", "Low", "Close", "Volume"]],
        df_daily[["Date", "sentiment_mean"]],
        on="Date",
        how="inner",
    ).sort_values("Date").reset_index(drop=True)
    logger.info(
        "Joined: %d baris (%s s/d %s)",
        len(df_joined), df_joined["Date"].min().date(), df_joined["Date"].max().date(),
    )
    joined_path = OUT_DIR / "new_joined_ohlcv_sentiment.csv"
    df_joined.to_csv(joined_path, index=False)
    print(df_joined.to_string(index=False))

    # =====================================================================
    # STEP 6: Stasioner-kan (return features, pct_change) — sama persis
    # load_return_features() produksi
    # =====================================================================
    logger.info("=" * 70)
    logger.info("STEP 6: Stasioner-kan (pct_change -> return features)")
    logger.info("=" * 70)
    df_ret = df_joined.copy()
    df_ret["ret_open"] = df_ret["Open"].pct_change()
    df_ret["ret_high"] = df_ret["High"].pct_change()
    df_ret["ret_low"] = df_ret["Low"].pct_change()
    df_ret["ret_close"] = df_ret["Close"].pct_change()
    df_ret["ret_volume"] = df_ret["Volume"].pct_change()
    ret_cols = ["ret_open", "ret_high", "ret_low", "ret_close", "ret_volume"]
    df_ret[ret_cols] = df_ret[ret_cols].replace([np.inf, -np.inf], np.nan)
    df_ret = df_ret.dropna(subset=ret_cols).reset_index(drop=True)
    df_ret_out = df_ret[["Date", *ret_cols, "sentiment_mean", "Close"]]
    ret_path = OUT_DIR / "new_return_features_stationary.csv"
    df_ret_out.to_csv(ret_path, index=False)
    logger.info("Stasioner: %d baris (%s s/d %s)", len(df_ret_out), df_ret_out["Date"].min().date(), df_ret_out["Date"].max().date())
    print(df_ret_out.to_string(index=False))

    # =====================================================================
    # STEP 7: Cek kelayakan windowing utk LSTM (window=20, skripsi-scoped)
    # =====================================================================
    logger.info("=" * 70)
    logger.info("STEP 7: Cek kelayakan windowing (window=%d)", WINDOW)
    logger.info("=" * 70)
    n_rows = len(df_ret_out)
    n_samples = max(0, n_rows - WINDOW + 1)
    print(f"\nJumlah baris final (setelah stasioner + inner join): {n_rows}")
    print(f"Window size (skripsi-scoped): {WINDOW}")
    print(f"Jumlah SAMPEL windowed yang bisa dibentuk: {n_samples}")
    if n_samples <= 0:
        print("\n>>> TIDAK CUKUP DATA untuk membentuk 1 sampel windowed pun.")
        print(">>> Training/prediksi LSTM (window=20) TIDAK BISA dijalankan pada dataset ini saja.")


if __name__ == "__main__":
    main()
