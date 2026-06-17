"""
pipeline/feature_engineering/data_alignment.py

Modul Data Alignment — menyelaraskan data dari berbagai sumber di data/processed/
sebelum digabungkan untuk training model.

Data yang tersedia di data/processed/:
  stocks/    → data OHLCV bersih per ticker  (output stock_preprocessor.py)
  sentiment/ → headlines_clean.csv
               headlines_daily_count.csv
               headlines_daily_sentiment.csv

Aturan alignment akan ditambahkan di sesi berikutnya.
"""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

PROCESSED_DIR   = Path("data/processed")
STOCKS_DIR      = PROCESSED_DIR / "stocks"
SENTIMENT_DIR   = PROCESSED_DIR / "sentiment"


class DataAligner:
    """
    Menyelaraskan data saham dan sentimen dari data/processed/
    sebelum diteruskan ke feature engineering.
    """

    def __init__(self, processed_dir: Path = PROCESSED_DIR) -> None:
        self._processed_dir = Path(processed_dir)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def scan_processed_dir(self) -> dict[str, list[Path]]:
        """
        Pindai seluruh isi data/processed/ dan kembalikan daftar file
        per subdirektori.

        Returns
        -------
        dict dengan key = nama subdirektori, value = list Path file CSV
        """
        if not self._processed_dir.exists():
            raise FileNotFoundError(
                f"Direktori processed tidak ditemukan: {self._processed_dir}"
            )

        result: dict[str, list[Path]] = {}

        for subdir in sorted(self._processed_dir.iterdir()):
            if not subdir.is_dir():
                continue
            files = sorted(
                f for f in subdir.iterdir()
                if f.is_file() and f.suffix == ".csv"
            )
            result[subdir.name] = files
            logger.info(
                "Subdirektori '%s' — %d file CSV ditemukan: %s",
                subdir.name,
                len(files),
                [f.name for f in files],
            )

        total = sum(len(v) for v in result.values())
        logger.info("Scan selesai — total %d file CSV di %d subdirektori.", total, len(result))
        return result

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------

    def load_stock(self, ticker: str) -> pd.DataFrame:
        """
        Muat data saham bersih dari data/processed/stocks/{ticker}_clean.csv.

        Parameters
        ----------
        ticker : nama ticker, misal 'GSPC'
        """
        path = STOCKS_DIR / f"{ticker}_clean.csv"
        if not path.exists():
            raise FileNotFoundError(f"File saham tidak ditemukan: {path}")

        logger.info("Memuat data saham: %s", path)
        df = pd.read_csv(path, parse_dates=["Date"])
        logger.info(
            "Data saham dimuat — ticker: %s | %d baris | rentang: %s s/d %s",
            ticker, len(df),
            df["Date"].min().date(),
            df["Date"].max().date(),
        )
        return df

    def load_sentiment(
        self,
        kind: str = "daily_sentiment",
    ) -> pd.DataFrame:
        """
        Muat data sentimen dari data/processed/sentiment/.

        Parameters
        ----------
        kind : nama file tanpa ekstensi. Pilihan yang tersedia:
               'headlines_clean'         → per-headline + skor FinBERT
               'headlines_daily_count'   → jumlah headline per hari
               'headlines_daily_sentiment' → agregasi sentimen harian (default)
        """
        path = SENTIMENT_DIR / f"{kind}.csv"
        if not path.exists():
            raise FileNotFoundError(f"File sentimen tidak ditemukan: {path}")

        logger.info("Memuat data sentimen: %s", path)
        df = pd.read_csv(path, parse_dates=["Date"])
        logger.info(
            "Data sentimen dimuat — kind: %s | %d baris | rentang: %s s/d %s",
            kind, len(df),
            df["Date"].min().date(),
            df["Date"].max().date(),
        )
        return df

    # ------------------------------------------------------------------
    # Alignment (rules akan ditambahkan kemudian)
    # ------------------------------------------------------------------

    def align(
        self,
        df_stock: pd.DataFrame,
        df_sentiment: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Selaraskan DataFrame saham dan sentimen.

        Aturan alignment belum diimplementasikan — akan ditambahkan
        pada sesi berikutnya sesuai instruksi.

        Parameters
        ----------
        df_stock     : DataFrame OHLCV bersih (output load_stock)
        df_sentiment : DataFrame sentimen harian (output load_sentiment)

        Returns
        -------
        DataFrame hasil alignment (belum diimplementasikan)
        """
        logger.info(
            "align() dipanggil — stock: %d baris | sentiment: %d baris",
            len(df_stock), len(df_sentiment),
        )

        # Inner join on Date — hanya hari yang data saham DAN sentimen tersedia
        df_aligned = pd.merge(
            df_stock,
            df_sentiment[["Date", "sentiment_mean"]],
            on="Date",
            how="inner",
        )
        df_aligned = df_aligned.sort_values("Date").reset_index(drop=True)

        logger.info(
            "align() selesai — %d baris hasil join (%s – %s)",
            len(df_aligned),
            df_aligned["Date"].min().date(),
            df_aligned["Date"].max().date(),
        )
        return df_aligned

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------

    def run(
        self,
        ticker: str,
        sentiment_kind: str = "headlines_daily_sentiment",
    ) -> pd.DataFrame:
        """
        Orchestrator: scan → load → align.

        Parameters
        ----------
        ticker         : nama ticker saham, misal 'GSPC'
        sentiment_kind : jenis file sentimen yang akan digunakan
        """
        logger.info("DataAligner.run() dimulai — ticker: %s", ticker)

        self.scan_processed_dir()
        df_stock     = self.load_stock(ticker)
        df_sentiment = self.load_sentiment(sentiment_kind)
        df_aligned   = self.align(df_stock, df_sentiment)

        logger.info("DataAligner.run() selesai — ticker: %s", ticker)
        return df_aligned
