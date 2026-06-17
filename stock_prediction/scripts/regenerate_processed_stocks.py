"""
Script regenerasi dataset processed saham S&P 500.

Alur:
  data/raw/stocks/GSPC_2018_2024.csv
  → hitung fitur teknikal (Daily_Return, HL_Spread, OC_Spread,
                            MA_20, MA_50, MA_200, Volatility_30)
  → simpan ke data/processed/stocks/GSPC_2018_2024.csv

Penggunaan:
  uv run python scripts/regenerate_processed_stocks.py
  # atau dari root repo:
  python scripts/regenerate_processed_stocks.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Konfigurasi path
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
RAW_PATH       = ROOT / "data" / "raw"    / "stocks" / "GSPC_2018_2024.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "stocks" / "GSPC_2018_2024.csv"

# Kolom raw yang tidak diperlukan di dataset processed
KOLOM_HAPUS = ["Dividends", "Stock Splits"]

# Urutan kolom akhir — pastikan konsisten dengan kontrak API dan notebook
URUTAN_KOLOM = [
    "Date",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "Daily_Return",
    "HL_Spread",
    "OC_Spread",
    "MA_20",
    "MA_50",
    "MA_200",
    "Volatility_30",
]


def load_raw(path: Path) -> pd.DataFrame:
    """Load raw CSV saham dan urutkan berdasarkan tanggal."""
    df = pd.read_csv(path, parse_dates=["Date"])
    df.sort_values("Date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def tambah_fitur(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hitung semua fitur teknikal dan kembalikan DataFrame dengan kolom lengkap.

    Catatan:
    - Daily_Return dalam PERSEN (×100), konsisten dengan versi sebelumnya.
    - MA_20, MA_50, MA_200 menggunakan Close.rolling(window).mean().
    - Baris awal yang belum cukup window dibiarkan NaN.
    - Volatility_30 = std rolling 30 hari dari Daily_Return (dalam persen).
    """
    df = df.copy()

    # Hapus kolom yang tidak relevan jika ada
    kolom_ada = [k for k in KOLOM_HAPUS if k in df.columns]
    if kolom_ada:
        df.drop(columns=kolom_ada, inplace=True)

    # Return harian dalam persen (baris pertama = NaN)
    df["Daily_Return"] = df["Close"].pct_change() * 100

    # Spread intraday dan open-to-close
    df["HL_Spread"] = df["High"] - df["Low"]
    df["OC_Spread"] = df["Close"] - df["Open"]

    # Moving average sederhana (Simple Moving Average)
    df["MA_20"]  = df["Close"].rolling(window=20).mean()
    df["MA_50"]  = df["Close"].rolling(window=50).mean()
    df["MA_200"] = df["Close"].rolling(window=200).mean()

    # Volatilitas rolling 30 hari (std dari Daily_Return %)
    df["Volatility_30"] = df["Daily_Return"].rolling(window=30).std()

    return df


def simpan_processed(df: pd.DataFrame, path: Path) -> None:
    """Pastikan direktori ada, lalu simpan CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def cetak_ringkasan(df: pd.DataFrame) -> None:
    """Cetak ringkasan dataset yang sudah diproses."""
    print(f"\nShape        : {df.shape}")
    print(f"Kolom        : {df.columns.tolist()}")
    print(f"\nMissing vals :\n{df.isnull().sum()}")
    print(f"\nCuplikan (5 baris pertama):\n{df.head()}")
    print(f"\nCuplikan baris ke-60 (MA_50 mulai terisi):\n{df.iloc[59:61]}")
    print(f"\nCuplikan baris ke-210 (MA_200 mulai terisi):\n{df.iloc[209:211]}")


def main() -> int:
    print(f"Raw path       : {RAW_PATH}")
    print(f"Processed path : {PROCESSED_PATH}")

    # 1. Validasi file raw ada
    if not RAW_PATH.exists():
        print(f"ERROR: File raw tidak ditemukan: {RAW_PATH}", file=sys.stderr)
        return 1

    # 2. Load
    print("\nMemuat data raw ...")
    df_raw = load_raw(RAW_PATH)
    print(f"  Loaded {len(df_raw)} baris, kolom: {df_raw.columns.tolist()}")

    # 3. Hitung fitur
    print("Menghitung fitur teknikal ...")
    df_processed = tambah_fitur(df_raw)

    # 4. Reorder kolom sesuai urutan yang telah ditentukan
    kolom_tersedia = [k for k in URUTAN_KOLOM if k in df_processed.columns]
    df_processed = df_processed[kolom_tersedia]

    # 5. Cetak ringkasan sebelum simpan
    cetak_ringkasan(df_processed)

    # 6. Simpan
    print(f"\nMenyimpan ke {PROCESSED_PATH} ...")
    simpan_processed(df_processed, PROCESSED_PATH)
    print(f"Selesai. File disimpan: {PROCESSED_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
