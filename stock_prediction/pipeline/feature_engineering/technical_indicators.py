"""
pipeline/feature_engineering/technical_indicators.py

Menghitung indikator teknikal dari data OHLCV:
  - EMA-20, EMA-50
  - RSI-14
  - MACD (12, 26, 9)
  - Bollinger Bands (20, 2σ)
  - Daily Return & Volatility-20
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def compute_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menerima DataFrame OHLCV dengan kolom minimal:
      Date, Open, High, Low, Close, Volume

    Mengembalikan DataFrame yang sama dengan tambahan kolom indikator teknikal.
    DataFrame di-sort berdasarkan Date secara ascending sebelum perhitungan.
    """
    required = {"Date", "Open", "High", "Low", "Close", "Volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Kolom OHLCV tidak lengkap, kurang: {missing}")

    logger.info("Memulai perhitungan indikator teknikal — %d baris data", len(df))

    df = df.sort_values("Date").reset_index(drop=True).copy()
    close = df["Close"]

    # ------------------------------------------------------------------ EMA
    logger.info("Menghitung EMA-20 dan EMA-50...")
    df["ema_20"] = _ema(close, 20)
    df["ema_50"] = _ema(close, 50)
    logger.info("EMA-20 dan EMA-50 selesai.")

    # ------------------------------------------------------------------ RSI
    logger.info("Menghitung RSI-14...")
    df["rsi_14"] = _rsi(close, 14)
    logger.info("RSI-14 selesai.")

    # ------------------------------------------------------------------ MACD
    logger.info("Menghitung MACD (12, 26, 9)...")
    ema12 = _ema(close, 12)
    ema26 = _ema(close, 26)
    df["macd"]        = ema12 - ema26
    df["macd_signal"] = _ema(df["macd"], 9)
    df["macd_hist"]   = df["macd"] - df["macd_signal"]
    logger.info("MACD selesai.")

    # ---------------------------------------------------- Bollinger Bands
    logger.info("Menghitung Bollinger Bands (20, 2σ)...")
    bb_mid             = close.rolling(20).mean()
    bb_std             = close.rolling(20).std(ddof=0)
    df["bb_mid"]       = bb_mid
    df["bb_upper"]     = bb_mid + 2 * bb_std
    df["bb_lower"]     = bb_mid - 2 * bb_std
    df["bb_bandwidth"] = (df["bb_upper"] - df["bb_lower"]) / bb_mid
    logger.info("Bollinger Bands selesai.")

    # ------------------------------------------------- Daily Return & Vol
    logger.info("Menghitung Daily Return dan Volatilitas-20...")
    df["daily_return"]   = close.pct_change()
    df["volatility_20"]  = df["daily_return"].rolling(20).std()
    logger.info("Daily Return dan Volatilitas-20 selesai.")

    new_cols = [
        "ema_20", "ema_50", "rsi_14",
        "macd", "macd_signal", "macd_hist",
        "bb_mid", "bb_upper", "bb_lower", "bb_bandwidth",
        "daily_return", "volatility_20",
    ]
    nan_counts = df[new_cols].isnull().sum().to_dict()
    logger.info(
        "Perhitungan indikator teknikal selesai. "
        "Kolom baru: %d | NaN (wajar di awal seri): %s",
        len(new_cols),
        nan_counts,
    )

    return df
