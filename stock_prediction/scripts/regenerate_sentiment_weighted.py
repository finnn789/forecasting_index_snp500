"""
scripts/regenerate_sentiment_weighted.py

Regenerasi penuh pipeline sentimen dengan metodologi probability-weighted:
  1. Muat CSV mentah (2008-2024, 19k headline)
  2. Cleaning ringan + filter
  3. FinBERT scoring via TextPreprocessor (batch=32, CPU)
  4. Hitung signed_score = sentiment_numeric * sentiment_score (weighted)
  5. Agregasi harian → headlines_clean.csv & headlines_daily_sentiment.csv

Jalankan:
  uv run python scripts/regenerate_sentiment_weighted.py
"""

import logging
import sys
from pathlib import Path

import pandas as pd

# Tambahkan root project ke sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Auto-detect GPU: pakai CUDA (device=0) jika tersedia, jika tidak CPU (device=-1)
try:
    import torch
    DEVICE = 0 if torch.cuda.is_available() else -1
except ImportError:
    DEVICE = -1

from pipeline.preprocessing.text_preprocessor import TextPreprocessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ============================================================
# Konfigurasi path
# ============================================================
RAW_CSV = ROOT / "data/raw/news/sp500_headlines_2008_2024.csv"
CLEAN_CSV = ROOT / "data/processed/sentiment/headlines_clean.csv"
DAILY_CSV = ROOT / "data/processed/sentiment/headlines_daily_sentiment.csv"
FINBERT_PATH = str(
    ROOT / "models/finbert/models--ProsusAI--finbert/snapshots/4556d13015211d73dccd3fdd39d39232506f3e43"
)

NEUTRAL_BAND = 0.05   # |sentiment_mean| < 0.05 → neutral harian
BATCH_SIZE   = 32


def clean_headlines(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleaning ringan:
    - Strip whitespace Title
    - Drop baris Title kosong / NaN
    - Drop duplikat (Title+Date)
    - Filter headline < 3 kata
    """
    logger.info("Cleaning %d baris mentah...", len(df))

    df = df.copy()
    df["Title"] = df["Title"].astype(str).str.strip()

    # Drop kosong/null
    before = len(df)
    df = df[df["Title"].notna() & (df["Title"] != "") & (df["Title"] != "nan")]
    logger.info("Drop kosong: %d → %d", before, len(df))

    # Drop duplikat Title+Date
    before = len(df)
    df = df.drop_duplicates(subset=["Title", "Date"])
    logger.info("Drop duplikat (Title+Date): %d → %d", before, len(df))

    # Filter < 3 kata
    before = len(df)
    df = df[df["Title"].str.split().str.len() >= 3]
    logger.info("Filter <3 kata: %d → %d", before, len(df))

    return df.reset_index(drop=True)


def aggregate_daily(df_scored: pd.DataFrame, neutral_band: float = NEUTRAL_BAND) -> pd.DataFrame:
    """
    Agregasi harian probability-weighted:
      signed_score = sentiment_numeric * sentiment_score
      sentiment_mean per hari = mean(signed_score)
    """
    logger.info("Menghitung signed_score = sentiment_numeric * sentiment_score...")
    df = df_scored.copy()
    df["signed_score"] = df["sentiment_numeric"] * df["sentiment_score"]

    logger.info("Agregasi groupby Date...")
    grp = df.groupby("Date")

    daily = pd.DataFrame()
    daily["headline_count"] = grp["Title"].count()
    daily["sentiment_mean"] = grp["signed_score"].mean().round(6)

    # Proporsi label
    def prop(g, label):
        return (g == label).sum() / len(g) if len(g) > 0 else 0.0

    daily["sentiment_pos"] = grp["sentiment_label"].apply(lambda g: prop(g, "positive")).round(6)
    daily["sentiment_neg"] = grp["sentiment_label"].apply(lambda g: prop(g, "negative")).round(6)
    daily["sentiment_neu"] = grp["sentiment_label"].apply(lambda g: prop(g, "neutral")).round(6)

    # Label harian berdasarkan tanda + neutral band
    daily["sentiment_label"] = daily["sentiment_mean"].apply(
        lambda v: "neutral" if abs(v) < neutral_band else ("positive" if v > 0 else "negative")
    )

    daily = daily.reset_index()  # Date menjadi kolom
    daily["Date"] = pd.to_datetime(daily["Date"]).dt.strftime("%Y-%m-%d")

    logger.info(
        "Agregasi selesai — %d hari unik | sentiment_mean range: [%.4f, %.4f]",
        len(daily),
        daily["sentiment_mean"].min(),
        daily["sentiment_mean"].max(),
    )
    return daily


def main():
    # ------------------------------------------------------------------
    # 1. Muat CSV mentah
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STEP 1: Muat CSV mentah")
    logger.info("=" * 60)
    df_raw = pd.read_csv(RAW_CSV)
    logger.info("Raw shape: %s", df_raw.shape)

    # ------------------------------------------------------------------
    # 2. Cleaning
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STEP 2: Cleaning headline")
    logger.info("=" * 60)
    df_clean = clean_headlines(df_raw)

    # ------------------------------------------------------------------
    # 3. FinBERT scoring
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STEP 3: FinBERT scoring (%d headline, batch=%d, CPU)", len(df_clean), BATCH_SIZE)
    logger.info("Estimasi waktu: beberapa menit di CPU — harap tunggu...")
    logger.info("=" * 60)

    logger.info("Device FinBERT: %s", "GPU (cuda:0)" if DEVICE == 0 else "CPU")
    preprocessor = TextPreprocessor(
        model_path=FINBERT_PATH,
        batch_size=BATCH_SIZE,
        device=DEVICE,
    )

    def progress_cb(batch_num, total_batches, processed):
        if batch_num % 50 == 0 or batch_num == total_batches:
            pct = 100 * batch_num / total_batches
            logger.info("  Batch %d/%d (%.1f%%) — %d headline diproses", batch_num, total_batches, pct, processed)

    df_scored = preprocessor.extract_sentiment_scores(
        df_clean,
        text_column="Title",
        on_batch=progress_cb,
    )

    logger.info(
        "Scoring selesai — distribusi label: %s",
        df_scored["sentiment_label"].value_counts().to_dict(),
    )
    logger.info(
        "sentiment_score stats — mean=%.4f, std=%.4f, min=%.4f, max=%.4f",
        df_scored["sentiment_score"].mean(),
        df_scored["sentiment_score"].std(),
        df_scored["sentiment_score"].min(),
        df_scored["sentiment_score"].max(),
    )

    # ------------------------------------------------------------------
    # 4. Simpan headlines_clean.csv
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STEP 4: Simpan headlines_clean.csv")
    logger.info("=" * 60)

    # Skema kolom kompatibel dengan file lama:
    # Title, Date, sentiment_label, sentiment_score, sentiment_numeric
    cols_clean = ["Title", "Date", "sentiment_label", "sentiment_score", "sentiment_numeric"]
    df_out_clean = df_scored[cols_clean].copy()

    CLEAN_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_out_clean.to_csv(CLEAN_CSV, index=False)
    logger.info("Tersimpan: %s (%d baris)", CLEAN_CSV, len(df_out_clean))

    # ------------------------------------------------------------------
    # 5. Agregasi harian + simpan headlines_daily_sentiment.csv
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STEP 5: Agregasi harian probability-weighted")
    logger.info("=" * 60)

    df_daily = aggregate_daily(df_scored)

    # Pastikan urutan kolom persis sama dgn skema downstream
    cols_daily = [
        "Date", "headline_count",
        "sentiment_mean", "sentiment_pos", "sentiment_neg", "sentiment_neu",
        "sentiment_label",
    ]
    df_daily = df_daily[cols_daily]

    DAILY_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_daily.to_csv(DAILY_CSV, index=False)
    logger.info("Tersimpan: %s (%d hari)", DAILY_CSV, len(df_daily))

    # ------------------------------------------------------------------
    # 6. Ringkasan statistik
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("RINGKASAN AKHIR")
    logger.info("=" * 60)
    logger.info("Headlines mentah: %d", len(df_raw))
    logger.info("Headlines setelah cleaning: %d (%.1f%%)", len(df_clean), 100 * len(df_clean) / len(df_raw))
    logger.info(
        "Distribusi label headline: %s",
        df_scored["sentiment_label"].value_counts().to_dict(),
    )
    logger.info("Hari unik dalam data harian: %d", len(df_daily))
    logger.info(
        "sentiment_mean harian — mean=%.4f | std=%.4f | min=%.4f | max=%.4f",
        df_daily["sentiment_mean"].mean(),
        df_daily["sentiment_mean"].std(),
        df_daily["sentiment_mean"].min(),
        df_daily["sentiment_mean"].max(),
    )
    logger.info(
        "Distribusi label harian: %s",
        df_daily["sentiment_label"].value_counts().to_dict(),
    )
    logger.info("=" * 60)
    logger.info("SELESAI. Semua artefak berhasil di-overwrite.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
