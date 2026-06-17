"""
pipeline/feature_engineering/dataset_builder.py

Modul 1 — Data (sesuai direction_model_contract.md).

Menyediakan:
- load_joined()       : inner-join OHLCV + sentiment on Date
- build_dataset()     : split, scale (anti-leakage), windowing → DatasetBundle
- build_latest_window(): window terakhir untuk inference
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------------

STOCK_CSV     = "data/processed/stocks/GSPC_2018_2024.csv"
SENTIMENT_CSV = "data/processed/sentiment/headlines_daily_sentiment.csv"
FEATURE_COLS  = ["Open", "High", "Low", "Close", "Volume", "sentiment_mean"]


# ---------------------------------------------------------------------------
# DatasetBundle
# ---------------------------------------------------------------------------

@dataclass
class DatasetBundle:
    X_train:      np.ndarray   # (N_train, W, 6)  float32
    y_train:      np.ndarray   # (N_train,)        float32 {0, 1}
    X_val:        np.ndarray   # (N_val,   W, 6)  float32
    y_val:        np.ndarray   # (N_val,)          float32
    X_test:       np.ndarray   # (N_test,  W, 6)  float32
    y_test:       np.ndarray   # (N_test,)         float32
    scaler:       MinMaxScaler
    feature_cols: list[str]
    window:       int
    test_dates:   list[str]    # tanggal target tiap sampel test (ISO string)


# ---------------------------------------------------------------------------
# load_joined
# ---------------------------------------------------------------------------

def load_joined() -> pd.DataFrame:
    """
    Inner-join OHLCV + sentimen harian on kolom 'Date', sort ascending.

    Returns
    -------
    DataFrame dengan kolom: Date + FEATURE_COLS
    (Date adalah datetime64, baris sudah di-reset index)
    """
    root = Path(__file__).resolve().parents[2]  # project root

    stock_path     = root / STOCK_CSV
    sentiment_path = root / SENTIMENT_CSV

    if not stock_path.exists():
        raise FileNotFoundError(f"File OHLCV tidak ditemukan: {stock_path}")
    if not sentiment_path.exists():
        raise FileNotFoundError(f"File sentimen tidak ditemukan: {sentiment_path}")

    df_stock = pd.read_csv(stock_path, parse_dates=["Date"])
    df_sent  = pd.read_csv(sentiment_path, parse_dates=["Date"])

    logger.info(
        "Stock loaded: %d rows (%s – %s)",
        len(df_stock),
        df_stock["Date"].min().date(),
        df_stock["Date"].max().date(),
    )
    logger.info(
        "Sentiment loaded: %d rows (%s – %s)",
        len(df_sent),
        df_sent["Date"].min().date(),
        df_sent["Date"].max().date(),
    )

    # Kolom OHLCV yang ada di stock CSV (sentiment_mean tidak ada di sana)
    OHLCV_COLS = ["Open", "High", "Low", "Close", "Volume"]

    # Inner join on Date: stock (OHLCV) + sentiment (sentiment_mean)
    df = pd.merge(
        df_stock[["Date"] + OHLCV_COLS],
        df_sent[["Date", "sentiment_mean"]],
        on="Date",
        how="inner",
    )

    df = df.sort_values("Date").reset_index(drop=True)

    # Pastikan kolom FEATURE_COLS ada
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Kolom fitur tidak tersedia setelah join: {missing}")

    logger.info(
        "Joined dataset: %d rows (%s – %s)",
        len(df),
        df["Date"].min().date(),
        df["Date"].max().date(),
    )
    return df


# ---------------------------------------------------------------------------
# _make_windows  (helper internal)
# ---------------------------------------------------------------------------

def _make_windows(
    features: np.ndarray,
    labels: np.ndarray,
    dates: pd.Series,
    window: int,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Windowing dalam satu split.

    X[i] = features[i : i+window]      shape (window, n_features)
    y[i] = labels[i + window - 1]      label pada hari terakhir window

    'test_dates' = tanggal target (hari setelah window terakhir) —
    hanya relevan untuk split test, tapi fungsi ini mengembalikannya
    sebagai ISO string dari dates[i+window-1] untuk konsistensi.
    """
    n = len(features)
    if n < window:
        return (
            np.empty((0, window, features.shape[1]), dtype=np.float32),
            np.empty((0,), dtype=np.float32),
            [],
        )

    num_samples = n - window + 1
    X = np.stack([features[i : i + window] for i in range(num_samples)]).astype(np.float32)
    y = labels[window - 1 : window - 1 + num_samples].astype(np.float32)
    out_dates = [
        dates.iloc[i + window - 1].strftime("%Y-%m-%d")
        for i in range(num_samples)
    ]
    return X, y, out_dates


# ---------------------------------------------------------------------------
# build_dataset
# ---------------------------------------------------------------------------

def build_dataset(
    window: int = 20,
    train_end: str = "2022-12-31",
    val_end: str = "2023-12-31",
) -> DatasetBundle:
    """
    Bangun DatasetBundle lengkap.

    Langkah:
    1. load_joined()
    2. Hitung label = (Close.shift(-1) > Close).astype(int)
       Hapus baris terakhir (label NaN karena shift)
    3. Split berdasarkan Date (train / val / test) SEBELUM scaling
    4. MinMaxScaler.fit HANYA di train → transform semua split (anti-leakage)
    5. Windowing per-split (tidak melintasi batas split)
    """
    df = load_joined()

    # 1. Label
    df["label"] = (df["Close"].shift(-1) > df["Close"]).astype("float32")
    df = df.iloc[:-1].copy()   # drop baris terakhir (label NaN)
    df = df.reset_index(drop=True)

    # 2. Split by Date
    train_end_ts = pd.Timestamp(train_end)
    val_end_ts   = pd.Timestamp(val_end)

    mask_train = df["Date"] <= train_end_ts
    mask_val   = (df["Date"] > train_end_ts) & (df["Date"] <= val_end_ts)
    mask_test  = df["Date"] > val_end_ts

    df_train = df[mask_train].reset_index(drop=True)
    df_val   = df[mask_val].reset_index(drop=True)
    df_test  = df[mask_test].reset_index(drop=True)

    logger.info(
        "Split sizes (rows before windowing) — train: %d | val: %d | test: %d",
        len(df_train), len(df_val), len(df_test),
    )

    # 3. Scaling — fit HANYA di train
    scaler = MinMaxScaler()
    train_feat = scaler.fit_transform(df_train[FEATURE_COLS].values.astype(np.float64))
    val_feat   = scaler.transform(df_val[FEATURE_COLS].values.astype(np.float64))
    test_feat  = scaler.transform(df_test[FEATURE_COLS].values.astype(np.float64))

    train_labels = df_train["label"].values
    val_labels   = df_val["label"].values
    test_labels  = df_test["label"].values

    # 4. Windowing per-split
    X_train, y_train, _            = _make_windows(train_feat, train_labels, df_train["Date"], window)
    X_val,   y_val,   _            = _make_windows(val_feat,   val_labels,   df_val["Date"],   window)
    X_test,  y_test,  test_dates   = _make_windows(test_feat,  test_labels,  df_test["Date"],  window)

    logger.info(
        "DatasetBundle built — X_train: %s | X_val: %s | X_test: %s",
        X_train.shape, X_val.shape, X_test.shape,
    )
    logger.info(
        "Label balance — mean y_train: %.4f | mean y_val: %.4f | mean y_test: %.4f",
        y_train.mean() if len(y_train) else float("nan"),
        y_val.mean()   if len(y_val)   else float("nan"),
        y_test.mean()  if len(y_test)  else float("nan"),
    )

    return DatasetBundle(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        scaler=scaler,
        feature_cols=FEATURE_COLS,
        window=window,
        test_dates=test_dates,
    )


# ---------------------------------------------------------------------------
# build_latest_window
# ---------------------------------------------------------------------------

def build_latest_window(
    window: int,
    scaler: MinMaxScaler,
) -> tuple[np.ndarray, str]:
    """
    Untuk inference: ambil `window` baris TERAKHIR dari load_joined(),
    transform dengan scaler, kembalikan (X[1,W,6] float32, as_of_date_iso).

    target_date = as_of_date + 1 hari kalender (string ISO).
    """
    df = load_joined()

    if len(df) < window:
        raise ValueError(
            f"Dataset hanya punya {len(df)} baris, butuh minimal {window} baris."
        )

    df_latest = df.iloc[-window:].reset_index(drop=True)
    feat = scaler.transform(df_latest[FEATURE_COLS].values.astype(np.float64))

    X = feat[np.newaxis, :, :].astype(np.float32)   # (1, W, 6)

    as_of_date = df_latest["Date"].iloc[-1]
    as_of_str  = as_of_date.strftime("%Y-%m-%d")

    # Target = hari kalender berikutnya (cukup +1 hari, bukan next trading day)
    target_str = (as_of_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    logger.info(
        "build_latest_window — as_of: %s | target: %s | X.shape: %s",
        as_of_str, target_str, X.shape,
    )
    return X, as_of_str
