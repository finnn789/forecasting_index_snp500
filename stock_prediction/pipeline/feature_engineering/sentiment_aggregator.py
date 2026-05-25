"""
pipeline/feature_engineering/sentiment_aggregator.py

Menggabungkan skor sentimen harian (output notebook 02) ke DataFrame OHLCV,
kemudian mengekstrak fitur siap pakai untuk training LSTM.

Input files:
  - data/processed/sentiment/headlines_daily_sentiment.csv
  - DataFrame OHLCV + indikator teknikal (dari technical_indicators.py)

Output:
  - DataFrame gabungan + fitur lag/rolling/target
  - Array numpy (X, y) berbentuk sliding window untuk LSTM
  - data/processed/stocks/features.csv
"""

import logging
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_SENTIMENT_PATH = Path("data/processed/sentiment/headlines_daily_sentiment.csv")

# Kolom sentimen yang akan diambil dari file harian
SENTIMENT_COLS = [
    "headline_count",
    "sentiment_mean",
    "sentiment_pos",
    "sentiment_neg",
    "sentiment_neu",
    "sentiment_label",
]


def load_daily_sentiment(path: Path = DEFAULT_SENTIMENT_PATH) -> pd.DataFrame:
    """
    Muat file agregasi sentimen harian.
    Kolom output: Date, headline_count, sentiment_mean,
                  sentiment_pos, sentiment_neg, sentiment_neu, sentiment_label
    """
    logger.info("Memuat data sentimen harian dari: %s", path)

    if not path.exists():
        raise FileNotFoundError(f"File sentimen tidak ditemukan: {path}")

    df = pd.read_csv(path, parse_dates=["Date"])
    logger.info("Data sentimen dimuat — %d baris, rentang: %s s/d %s",
                len(df),
                df["Date"].min().date(),
                df["Date"].max().date())
    return df


def merge_sentiment(
    df_ohlcv: pd.DataFrame,
    df_sentiment: pd.DataFrame | None = None,
    sentiment_path: Path = DEFAULT_SENTIMENT_PATH,
    fill_missing: bool = True,
) -> pd.DataFrame:
    """
    Gabungkan skor sentimen harian ke DataFrame OHLCV.

    Parameters
    ----------
    df_ohlcv : DataFrame dengan kolom Date + OHLCV (+indikator teknikal opsional)
    df_sentiment : DataFrame sentimen harian (opsional — jika None, dimuat dari file)
    sentiment_path : path file sentimen (digunakan jika df_sentiment=None)
    fill_missing : jika True, hari tanpa berita diisi dengan 0.0 / 'neutral'

    Returns
    -------
    DataFrame gabungan (left join OHLCV ← sentiment)
    """
    logger.info("Memulai penggabungan data sentimen ke OHLCV...")

    if df_sentiment is None:
        df_sentiment = load_daily_sentiment(sentiment_path)

    df_ohlcv = df_ohlcv.copy()
    df_ohlcv["Date"] = pd.to_datetime(df_ohlcv["Date"])
    df_sentiment["Date"] = pd.to_datetime(df_sentiment["Date"])

    logger.info("OHLCV: %d baris | Sentimen: %d baris", len(df_ohlcv), len(df_sentiment))

    df_merged = df_ohlcv.merge(
        df_sentiment[["Date"] + SENTIMENT_COLS],
        on="Date",
        how="left",
    )

    missing_days = df_merged["sentiment_mean"].isnull().sum()
    logger.info(
        "Penggabungan selesai — %d hari tanpa data sentimen (%.1f%%)",
        missing_days,
        100 * missing_days / len(df_merged) if len(df_merged) else 0,
    )

    if fill_missing and missing_days > 0:
        logger.info("Mengisi hari tanpa sentimen: numerik→0.0, label→'neutral', count→0")
        num_cols = ["sentiment_mean", "sentiment_pos", "sentiment_neg", "sentiment_neu"]
        df_merged[num_cols] = df_merged[num_cols].fillna(0.0)
        df_merged["sentiment_label"]  = df_merged["sentiment_label"].fillna("neutral")
        df_merged["headline_count"]   = df_merged["headline_count"].fillna(0).astype(int)

    logger.info(
        "Dataset akhir: %d baris, %d kolom",
        len(df_merged),
        len(df_merged.columns),
    )
    return df_merged


# ---------------------------------------------------------------------------
# Feature Extraction
# ---------------------------------------------------------------------------

SENTIMENT_LABEL_MAP = {"positive": 1, "neutral": 0, "negative": -1}

DEFAULT_LAG_COLS   = ["Close", "sentiment_mean", "rsi_14", "macd", "daily_return"]
DEFAULT_LAGS       = [1, 3, 5]
DEFAULT_ROLL_WINS  = [3, 7]
DEFAULT_WINDOW     = 20          # jumlah hari per sequence LSTM
DEFAULT_FEATURES_PATH = Path("data/processed/stocks/features.csv")


def encode_sentiment_label(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode kolom `sentiment_label` (string) menjadi `sentiment_label_enc` (int):
      positive →  1 | neutral → 0 | negative → -1
    """
    logger.info("Encoding sentiment_label → numerik...")

    if "sentiment_label" not in df.columns:
        logger.warning("Kolom 'sentiment_label' tidak ditemukan, skip encoding.")
        return df

    df = df.copy()
    df["sentiment_label_enc"] = (
        df["sentiment_label"].str.lower().map(SENTIMENT_LABEL_MAP).fillna(0).astype(int)
    )
    dist = df["sentiment_label_enc"].value_counts().to_dict()
    logger.info("Encoding selesai — distribusi: %s", dist)
    return df


def add_lag_features(
    df: pd.DataFrame,
    cols: list[str] | None = None,
    lags: list[int] | None = None,
) -> pd.DataFrame:
    """
    Tambahkan kolom lag untuk fitur time-series.
    Contoh output: Close_lag1, sentiment_mean_lag3, rsi_14_lag5, ...
    """
    cols = cols or DEFAULT_LAG_COLS
    lags = lags or DEFAULT_LAGS

    # Hanya proses kolom yang benar-benar ada
    available = [c for c in cols if c in df.columns]
    skipped   = set(cols) - set(available)
    if skipped:
        logger.warning("Kolom lag tidak ditemukan, dilewati: %s", skipped)

    logger.info("Membuat lag features — kolom: %s | lag: %s", available, lags)

    df = df.copy()
    added = []
    for col in available:
        for lag in lags:
            name = f"{col}_lag{lag}"
            df[name] = df[col].shift(lag)
            added.append(name)

    logger.info("Lag features selesai — %d kolom baru ditambahkan", len(added))
    return df


def add_rolling_sentiment(
    df: pd.DataFrame,
    windows: list[int] | None = None,
) -> pd.DataFrame:
    """
    Tambahkan rolling mean & std skor sentimen harian.
    Contoh output: sentiment_mean_roll3, sentiment_mean_roll7,
                   sentiment_std_roll3, sentiment_std_roll7
    """
    windows = windows or DEFAULT_ROLL_WINS

    if "sentiment_mean" not in df.columns:
        logger.warning("Kolom 'sentiment_mean' tidak ditemukan, skip rolling sentiment.")
        return df

    logger.info("Membuat rolling sentiment — windows: %s", windows)

    df = df.copy()
    added = []
    for w in windows:
        df[f"sentiment_mean_roll{w}"] = df["sentiment_mean"].rolling(w, min_periods=1).mean()
        df[f"sentiment_std_roll{w}"]  = df["sentiment_mean"].rolling(w, min_periods=1).std().fillna(0)
        added.extend([f"sentiment_mean_roll{w}", f"sentiment_std_roll{w}"])

    logger.info("Rolling sentiment selesai — %d kolom baru: %s", len(added), added)
    return df


def create_target(
    df: pd.DataFrame,
    horizon: int = 1,
    mode: Literal["return", "direction"] = "return",
) -> pd.DataFrame:
    """
    Buat kolom `target` untuk supervised learning.

    Parameters
    ----------
    horizon : jumlah hari ke depan yang diprediksi (default 1 = besok)
    mode    :
      'return'    → % perubahan harga: (Close[t+h] - Close[t]) / Close[t]
      'direction' → 1 jika harga naik, 0 jika turun/flat
    """
    if "Close" not in df.columns:
        raise ValueError("Kolom 'Close' diperlukan untuk membuat target.")

    logger.info("Membuat kolom target — horizon: %d hari | mode: %s", horizon, mode)

    df = df.copy()
    future_close = df["Close"].shift(-horizon)

    if mode == "return":
        df["target"] = (future_close - df["Close"]) / df["Close"]
        logger.info(
            "Target 'return' dibuat — mean=%.4f, std=%.4f",
            df["target"].mean(),
            df["target"].std(),
        )
    else:
        df["target"] = (future_close > df["Close"]).astype(int)
        dist = df["target"].value_counts().to_dict()
        logger.info("Target 'direction' dibuat — distribusi: %s", dist)

    # Baris terakhir tidak punya future → drop agar tidak ada NaN di target
    before = len(df)
    df = df.dropna(subset=["target"]).copy()
    logger.info("Baris tanpa target di-drop: %d → %d", before, len(df))
    return df


def extract_features(
    df: pd.DataFrame,
    lag_cols: list[str] | None = None,
    lags: list[int] | None = None,
    roll_windows: list[int] | None = None,
    target_horizon: int = 1,
    target_mode: Literal["return", "direction"] = "return",
) -> pd.DataFrame:
    """
    Fungsi utama ekstraksi fitur dari DataFrame gabungan (hasil merge_sentiment).

    Urutan langkah:
      1. Encode sentiment_label → numerik
      2. Tambah lag features
      3. Tambah rolling sentiment
      4. Buat kolom target
      5. Drop baris NaN awal (akibat lag & rolling)
      6. Reset index

    Returns DataFrame siap pakai untuk build_lstm_sequences().
    """
    logger.info("=" * 60)
    logger.info("MULAI FEATURE EXTRACTION — %d baris input", len(df))
    logger.info("=" * 60)

    # Langkah 1
    logger.info("[1/4] Encoding label sentimen...")
    df = encode_sentiment_label(df)

    # Langkah 2
    logger.info("[2/4] Membuat lag features...")
    df = add_lag_features(df, cols=lag_cols, lags=lags)

    # Langkah 3
    logger.info("[3/4] Membuat rolling sentiment features...")
    df = add_rolling_sentiment(df, windows=roll_windows)

    # Langkah 4
    logger.info("[4/4] Membuat kolom target...")
    df = create_target(df, horizon=target_horizon, mode=target_mode)

    # Drop NaN dari lag/rolling di awal seri
    before = len(df)
    df = df.dropna().reset_index(drop=True)
    dropped = before - len(df)
    logger.info("Drop NaN setelah ekstraksi: %d baris → %d baris (dropped: %d)", before, len(df), dropped)

    logger.info("=" * 60)
    logger.info(
        "FEATURE EXTRACTION SELESAI — %d baris | %d kolom | fitur: %s",
        len(df),
        len(df.columns),
        [c for c in df.columns if c not in ("Date", "sentiment_label")],
    )
    logger.info("=" * 60)
    return df


def build_lstm_sequences(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "target",
    window_size: int = DEFAULT_WINDOW,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Buat sliding window sequences untuk input LSTM.

    Parameters
    ----------
    df           : DataFrame hasil extract_features()
    feature_cols : daftar kolom fitur input
    target_col   : nama kolom target
    window_size  : jumlah timestep per sequence

    Returns
    -------
    X : np.ndarray shape (samples, window_size, n_features)
    y : np.ndarray shape (samples,)
    """
    missing = [c for c in feature_cols + [target_col] if c not in df.columns]
    if missing:
        raise ValueError(f"Kolom tidak ditemukan di DataFrame: {missing}")

    logger.info(
        "Membangun LSTM sequences — window: %d | fitur: %d | target: %s",
        window_size, len(feature_cols), target_col,
    )

    data   = df[feature_cols].to_numpy(dtype=np.float32)
    target = df[target_col].to_numpy(dtype=np.float32)

    X, y = [], []
    for i in range(len(data) - window_size):
        X.append(data[i : i + window_size])
        y.append(target[i + window_size])

    X_arr = np.array(X, dtype=np.float32)
    y_arr = np.array(y, dtype=np.float32)

    logger.info(
        "Sequences selesai — X: %s | y: %s",
        X_arr.shape, y_arr.shape,
    )
    return X_arr, y_arr


def split_dataset(
    df: pd.DataFrame,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Bagi dataset berdasarkan urutan waktu (bukan random shuffle).

    Returns (df_train, df_val, df_test)
    """
    n = len(df)
    i_train = int(n * train_ratio)
    i_val   = int(n * (train_ratio + val_ratio))

    df_train = df.iloc[:i_train].copy()
    df_val   = df.iloc[i_train:i_val].copy()
    df_test  = df.iloc[i_val:].copy()

    logger.info(
        "Dataset split (time-based) — train: %d (%.0f%%) | val: %d (%.0f%%) | test: %d (%.0f%%)",
        len(df_train), 100 * train_ratio,
        len(df_val),   100 * val_ratio,
        len(df_test),  100 * (1 - train_ratio - val_ratio),
    )

    if "Date" in df.columns:
        logger.info(
            "Rentang — train: %s→%s | val: %s→%s | test: %s→%s",
            df_train["Date"].min().date(), df_train["Date"].max().date(),
            df_val["Date"].min().date(),   df_val["Date"].max().date(),
            df_test["Date"].min().date(),  df_test["Date"].max().date(),
        )

    return df_train, df_val, df_test


def save_features(
    df: pd.DataFrame,
    path: Path = DEFAULT_FEATURES_PATH,
) -> Path:
    """
    Simpan DataFrame hasil ekstraksi fitur ke CSV.
    Folder dibuat otomatis jika belum ada.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Menyimpan features ke: %s", path)
    df.to_csv(path, index=False)
    size_kb = path.stat().st_size / 1024
    logger.info("File tersimpan — %d baris | %.1f KB", len(df), size_kb)
    return path


def get_feature_summary(df: pd.DataFrame) -> dict:
    """
    Kembalikan ringkasan statistik dataset hasil feature engineering sebagai dict
    (siap di-serialize ke JSON untuk response API).
    """
    logger.info("Membuat ringkasan fitur dataset...")

    num_cols = df.select_dtypes(include="number").columns.tolist()
    stats = df[num_cols].describe().round(4).to_dict()

    sentiment_dist: dict = {}
    if "sentiment_label" in df.columns:
        sentiment_dist = df["sentiment_label"].value_counts().to_dict()

    summary = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": df.columns.tolist(),
        "date_range": {
            "start": str(df["Date"].min().date()) if "Date" in df.columns else None,
            "end":   str(df["Date"].max().date()) if "Date" in df.columns else None,
        },
        "missing_values": df.isnull().sum().to_dict(),
        "statistics": stats,
        "sentiment_distribution": sentiment_dist,
    }

    logger.info("Ringkasan fitur selesai dibuat.")
    return summary
