"""
pipeline/preprocessing/stock_preprocessor.py

Membersihkan data OHLCV mentah dari CSV ke DataFrame siap pakai.
Sumber data: data/raw/stocks/GSPC_2018_2024.csv

Tanggung jawab modul ini:
  1. Muat CSV mentah
  2. Hapus kolom tidak relevan (Dividends, Stock Splits)
  3. Validasi kolom OHLCV wajib
  4. Sort berdasarkan Date (ascending)
  5. Hapus duplikat tanggal
  6. Tangani nilai NaN (forward-fill → backward-fill)
  7. Validasi nilai (harga > 0, volume >= 0)
  8. Simpan hasil ke data/processed/stocks/

Output:
  data/processed/stocks/{ticker}_clean.csv
"""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

OHLCV_COLS = ["Open", "High", "Low", "Close", "Volume"]
DROP_COLS   = ["Dividends", "Stock Splits"]
DEFAULT_OUTPUT_DIR = Path("data/processed/stocks")


class StockPreprocessor:
    """Membersihkan data OHLCV mentah dari file CSV."""

    def __init__(self, output_dir: Path = DEFAULT_OUTPUT_DIR) -> None:
        self._output_dir = Path(output_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_csv(self, path: str | Path) -> pd.DataFrame:
        """
        Muat raw CSV OHLCV.
        Kolom Date di-parse sebagai datetime dan tetap sebagai kolom biasa.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File CSV tidak ditemukan: {path}")

        logger.info("Memuat CSV dari: %s", path)
        df = pd.read_csv(path, parse_dates=["Date"])
        logger.info(
            "CSV dimuat — %d baris | %d kolom | rentang: %s s/d %s",
            len(df),
            len(df.columns),
            df["Date"].min().date(),
            df["Date"].max().date(),
        )
        return df

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Jalankan seluruh proses cleaning secara berurutan:
          1. Hapus kolom tidak relevan
          2. Validasi kolom wajib
          3. Sort berdasarkan Date
          4. Hapus duplikat tanggal
          5. Handle NaN
          6. Validasi nilai OHLCV
        """
        logger.info("=" * 60)
        logger.info("MULAI CLEANING — %d baris input", len(df))
        logger.info("=" * 60)

        df = self._drop_irrelevant_columns(df)
        self._validate_columns(df)
        df = self._sort_by_date(df)
        df = self._drop_duplicates(df)
        df = self._handle_nan(df)
        df = self._validate_values(df)

        logger.info(
            "CLEANING SELESAI — %d baris | %d kolom | rentang: %s s/d %s",
            len(df),
            len(df.columns),
            df["Date"].min().date(),
            df["Date"].max().date(),
        )
        logger.info("=" * 60)
        return df

    def save_processed(self, df: pd.DataFrame, ticker: str) -> Path:
        """
        Simpan DataFrame bersih ke data/processed/stocks/{ticker}_clean.csv.
        Folder dibuat otomatis jika belum ada.
        """
        self._output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self._output_dir / f"{ticker}_clean.csv"

        df.to_csv(output_path, index=False)
        size_kb = output_path.stat().st_size / 1024
        logger.info(
            "Data bersih disimpan ke: %s | %d baris | %.1f KB",
            output_path, len(df), size_kb,
        )
        return output_path

    def run(self, csv_path: str | Path, ticker: str) -> pd.DataFrame:
        """
        Orchestrator: muat → bersihkan → simpan.

        Parameters
        ----------
        csv_path : path ke file CSV mentah
        ticker   : nama ticker (digunakan sebagai nama file output, misal 'GSPC')

        Returns
        -------
        DataFrame OHLCV yang sudah bersih
        """
        logger.info("StockPreprocessor.run() dimulai — ticker: %s", ticker)
        df_raw   = self.load_csv(csv_path)
        df_clean = self.clean(df_raw)
        self.save_processed(df_clean, ticker)
        logger.info("StockPreprocessor.run() selesai — ticker: %s", ticker)
        return df_clean

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _drop_irrelevant_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Hapus kolom yang tidak diperlukan model (Dividends, Stock Splits)."""
        cols_to_drop = [c for c in DROP_COLS if c in df.columns]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
            logger.info("Kolom dihapus: %s", cols_to_drop)
        return df

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Pastikan semua kolom OHLCV wajib tersedia."""
        required = {"Date"} | set(OHLCV_COLS)
        missing  = required - set(df.columns)
        if missing:
            raise ValueError(f"Kolom wajib tidak ditemukan: {missing}")
        logger.info("Validasi kolom OHLCV: OK — %s", OHLCV_COLS)

    def _sort_by_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Urutkan data ascending berdasarkan Date."""
        df = df.sort_values("Date").reset_index(drop=True)
        logger.info("Data diurutkan berdasarkan Date (ascending).")
        return df

    def _drop_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Hapus baris dengan tanggal duplikat, pertahankan kemunculan pertama."""
        before  = len(df)
        df      = df.drop_duplicates(subset=["Date"], keep="first").reset_index(drop=True)
        dropped = before - len(df)
        if dropped:
            logger.warning("Duplikat tanggal dihapus: %d baris", dropped)
        else:
            logger.info("Tidak ada duplikat tanggal ditemukan.")
        return df

    def _handle_nan(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Tangani NaN pada kolom OHLCV:
          - Forward-fill: pakai nilai hari sebelumnya (cocok untuk data pasar)
          - Backward-fill: fallback untuk baris paling awal jika masih NaN
        """
        nan_before = df[OHLCV_COLS].isnull().sum().sum()
        if nan_before == 0:
            logger.info("Tidak ada NaN pada kolom OHLCV.")
            return df

        logger.info("NaN sebelum fill: %d", nan_before)
        df = df.copy()
        df[OHLCV_COLS] = df[OHLCV_COLS].ffill().bfill()
        nan_after = df[OHLCV_COLS].isnull().sum().sum()
        logger.info("NaN setelah fill: %d", nan_after)
        return df

    def _validate_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Drop baris tidak valid:
          - Harga (Open, High, Low, Close) harus > 0
          - Volume harus >= 0
        """
        price_cols   = ["Open", "High", "Low", "Close"]
        mask_invalid = (df[price_cols] <= 0).any(axis=1) | (df["Volume"] < 0)
        n_invalid    = mask_invalid.sum()

        if n_invalid:
            logger.warning(
                "Baris tidak valid (harga ≤ 0 atau volume < 0): %d — di-drop.",
                n_invalid,
            )
            df = df[~mask_invalid].reset_index(drop=True)
        else:
            logger.info("Validasi nilai OHLCV: semua %d baris valid.", len(df))
        return df
