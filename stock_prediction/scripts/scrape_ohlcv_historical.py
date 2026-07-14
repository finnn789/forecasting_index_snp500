"""
Script scraping data OHLCV historis S&P 500 menggunakan yfinance.
Rentang data: 2008-01-02 s/d 2024-03-04
Output: data/raw/stocks/GSPC_2008_2024.csv
"""

import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

# ── Konfigurasi ──────────────────────────────────────────────────────────────
TICKER      = "^GSPC"
START_DATE  = "2008-01-02"
END_DATE    = "2024-03-05"   # yfinance: end bersifat eksklusif → +1 hari agar 2024-03-04 ikut

ROOT_DIR    = Path(__file__).resolve().parents[1]
RAW_DIR     = ROOT_DIR / "data" / "raw" / "stocks"
OUTPUT_FILE = RAW_DIR / "GSPC_2008_2024.csv"

# ── Helper ────────────────────────────────────────────────────────────────────
def download_ohlcv(ticker: str, start: str, end: str) -> pd.DataFrame:
    print(f"[INFO] Mengunduh {ticker}  |  {start} → {end} ...")
    df = yf.download(
        tickers=ticker,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=False,   # simpan Dividends + Stock Splits, konsisten dgn data lama
        progress=True,
    )
    if df.empty:
        print("[ERROR] Data kosong — periksa koneksi internet atau ticker.")
        sys.exit(1)

    # yfinance v0.2+ bisa mengembalikan MultiIndex jika multi-ticker;
    # pastikan kolom flat untuk satu ticker
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df


def clean_and_format(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Pastikan index bernama 'Date' & bertipe datetime
    df.index.name = "Date"
    df.index = pd.to_datetime(df.index)

    # Kolom yang dipertahankan (sesuai format GSPC_2018_2024.csv)
    keep_cols = ["Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"]
    missing = [c for c in keep_cols if c not in df.columns]
    if missing:
        # yfinance kadang tidak mengembalikan Dividends/Stock Splits untuk index
        for c in missing:
            df[c] = 0.0
        print(f"[WARN] Kolom tidak ada di download, diisi 0: {missing}")

    df = df[keep_cols]

    # Buang baris NaN (hari libur/data hilang)
    before = len(df)
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    dropped = before - len(df)
    if dropped:
        print(f"[WARN] {dropped} baris dihapus karena NaN pada OHLC.")

    # Potong tanggal agar tidak melebihi batas yang diminta
    df = df.loc["2008-01-02":"2024-03-04"]

    return df


def save(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=True, float_format="%.10f")
    print(f"[OK]  Tersimpan → {path}")
    print(f"      Total baris : {len(df):,}")
    print(f"      Rentang     : {df.index[0].date()} s/d {df.index[-1].date()}")


def print_summary(df: pd.DataFrame) -> None:
    print("\n── Ringkasan Data ──────────────────────────────────────────")
    print(df.describe())
    print(f"\nCek NaN per kolom:\n{df.isnull().sum()}")
    print("────────────────────────────────────────────────────────────\n")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    raw_df   = download_ohlcv(TICKER, START_DATE, END_DATE)
    clean_df = clean_and_format(raw_df)
    print_summary(clean_df)
    save(clean_df, OUTPUT_FILE)
    print("[DONE] Scraping selesai.")


if __name__ == "__main__":
    main()
