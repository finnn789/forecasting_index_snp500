"""
app/services/sentiment_service.py — Business logic untuk sentiment pipeline.
"""

import os
import time
from collections.abc import Callable
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from pipeline.preprocessing.text_preprocessor import TextPreprocessor
from app.core.exceptions import NotFoundError
from app.repositories import NewsRepository, SentimentRepository
from app.repositories.provider import get_repositories
from app.schemas.sentiment import PreviewResponse

load_dotenv()


_REQUIRED_MODEL_FILES = [
    "config.json",
    "pytorch_model.bin",
    "tokenizer_config.json",
    "vocab.txt",
]


def _resolve_model_path() -> str:
    """
    Resolve FINBERT_MODEL_NAME ke path yang bisa dibaca AutoTokenizer/AutoModel.
    Jika path adalah HF cache format (ada snapshots/ + refs/main), kembalikan path snapshot aktif.
    Jika path adalah direktori biasa atau HF Hub name, kembalikan apa adanya.
    """
    raw = os.environ["FINBERT_MODEL_NAME"]
    p = Path(raw)
    refs_main = p / "refs" / "main"
    snapshots_dir = p / "snapshots"
    if refs_main.exists() and snapshots_dir.exists():
        commit = refs_main.read_text().strip()
        return str(snapshots_dir / commit)
    return raw


# Path artefak sentiment kini bersumber tunggal dari repository (lihat
# app/repositories/) — bukan lagi dari os.environ, agar konsisten dengan
# layer akses data lain. Default repository == nilai .env.example.
def _raw_csv() -> Path:
    return get_repositories()["news"].raw_headlines_path()


def _clean_csv() -> Path:
    return get_repositories()["news"].clean_headlines_path()


def _daily_csv() -> Path:
    return get_repositories()["sentiment"].daily_sentiment_path()


def run_preprocessing_pipeline_stream(
    start_date: str | None,
    end_date: str | None,
    batch_size: int,
    emit: Callable[[dict], None],
) -> None:
    """
    Jalankan sentiment pipeline di thread terpisah dan kirim progress via emit().
    Dipanggil dari endpoint SSE — jangan raise HTTPException, gunakan emit error.
    """
    t_start = time.time()

    try:
        # ------------------------------------------------------------------
        # [1] Baca CSV
        # ------------------------------------------------------------------
        emit({"step": "loading_data", "pct": 5, "msg": "Membaca raw CSV..."})
        raw_csv = _raw_csv()
        if not raw_csv.exists():
            emit({"step": "error", "pct": 5, "msg": f"Raw CSV tidak ditemukan: {raw_csv}"})
            return

        try:
            df_raw = pd.read_csv(raw_csv, usecols=["Title", "Date"])
        except ValueError as e:
            emit({"step": "error", "pct": 5, "msg": f"Kolom wajib tidak lengkap: {e}"})
            return

        total_raw = len(df_raw)
        emit({"step": "loading_data", "pct": 8, "msg": f"{total_raw:,} headlines dimuat."})

        # ------------------------------------------------------------------
        # [2] Filter tanggal
        # ------------------------------------------------------------------
        df_raw["Date"] = pd.to_datetime(df_raw["Date"], errors="coerce")
        emit({"step": "filtering", "pct": 10, "msg": "Memfilter rentang tanggal..."})
        try:
            if start_date:
                df_raw = df_raw[df_raw["Date"] >= pd.Timestamp(start_date)]
            if end_date:
                df_raw = df_raw[df_raw["Date"] <= pd.Timestamp(end_date)]
        except Exception as e:
            emit({"step": "error", "pct": 10, "msg": f"Format tanggal tidak valid: {e}"})
            return

        if df_raw.empty:
            emit({"step": "error", "pct": 10, "msg": "Tidak ada data pada rentang tanggal tersebut."})
            return

        emit({"step": "filtering", "pct": 12, "msg": f"{len(df_raw):,} headlines setelah filter."})

        # ------------------------------------------------------------------
        # [3] Load FinBERT
        # ------------------------------------------------------------------
        emit({"step": "loading_model", "pct": 15, "msg": "Memuat FinBERT model..."})
        try:
            preprocessor = TextPreprocessor(
                model_path=_resolve_model_path(),
                batch_size=batch_size,
                device=int(os.environ.get("FINBERT_DEVICE", -1)),
            )
            preprocessor._load_pipeline()
        except Exception as e:
            emit({"step": "error", "pct": 15, "msg": f"Gagal memuat model: {e}"})
            return

        emit({"step": "model_ready", "pct": 20, "msg": "FinBERT siap. Mulai inferensi..."})

        # ------------------------------------------------------------------
        # [4] Inference per batch
        # ------------------------------------------------------------------
        def on_batch(batch_num: int, total_batches: int, processed: int) -> None:
            pct = 20 + int(65 * batch_num / total_batches)
            emit({
                "step": "inference",
                "pct": pct,
                "msg": f"Batch {batch_num}/{total_batches} — {processed:,} headline diproses",
                "batch": batch_num,
                "total_batches": total_batches,
                "processed": processed,
            })

        try:
            df_no_cp = preprocessor.drop_cp_column(df_raw)
            df_clean = preprocessor.extract_sentiment_scores(df_no_cp, on_batch=on_batch)
        except Exception as e:
            emit({"step": "error", "pct": 50, "msg": f"Inferensi gagal: {e}"})
            return

        # ------------------------------------------------------------------
        # [5] Agregasi & Simpan
        # ------------------------------------------------------------------
        emit({"step": "aggregating", "pct": 87, "msg": "Mengagregasi sentimen harian..."})
        df_daily = _aggregate_daily(df_clean)

        emit({"step": "saving", "pct": 95, "msg": "Menyimpan file output..."})
        try:
            repos = get_repositories()
            clean_csv = repos["news"].save_clean_headlines(df_clean)
            daily_csv = repos["sentiment"].save_daily_sentiment(df_daily)
        except OSError as e:
            emit({"step": "error", "pct": 95, "msg": f"Gagal menyimpan file: {e}"})
            return

        # ------------------------------------------------------------------
        # [6] Done
        # ------------------------------------------------------------------
        duration = round(time.time() - t_start, 2)
        actual_dates = df_daily["Date"]
        date_range = {
            "start": str(actual_dates.min().date()) if len(df_daily) else None,
            "end": str(actual_dates.max().date()) if len(df_daily) else None,
        }
        sample_df = df_daily.head(5).copy()
        sample_df["Date"] = sample_df["Date"].astype(str)

        emit({
            "step": "done",
            "pct": 100,
            "msg": f"Pipeline selesai dalam {duration}s",
            "result": {
                "status": "success",
                "total_headlines": len(df_clean),
                "total_days": len(df_daily),
                "output_path": str(daily_csv),
                "date_range": date_range,
                "duration_seconds": duration,
                "sample": sample_df.to_dict(orient="records"),
            },
        })

    except Exception as e:
        emit({"step": "error", "pct": 0, "msg": f"Error tidak terduga: {e}"})


def _aggregate_daily(df_clean: pd.DataFrame) -> pd.DataFrame:
    df = df_clean.copy()
    df["Date"] = pd.to_datetime(df["Date"])

    agg = df.groupby("Date").agg(
        headline_count=("sentiment_numeric", "count"),
        sentiment_mean=("sentiment_numeric", "mean"),
        sentiment_pos=("sentiment_label", lambda x: (x == "positive").mean()),
        sentiment_neg=("sentiment_label", lambda x: (x == "negative").mean()),
        sentiment_neu=("sentiment_label", lambda x: (x == "neutral").mean()),
        sentiment_label=("sentiment_label", lambda x: x.value_counts().index[0]),
    ).reset_index()

    return agg


def get_pipeline_status() -> dict:
    repos = get_repositories()
    news_repo: NewsRepository = repos["news"]
    sentiment_repo: SentimentRepository = repos["sentiment"]

    clean_csv = _clean_csv()
    daily_csv = _daily_csv()
    clean_exists = clean_csv.exists()
    daily_exists = daily_csv.exists()

    total_headlines = None
    total_days = None
    date_range = {"start": None, "end": None}

    if clean_exists:
        try:
            df_clean = news_repo.load_clean_headlines()
            total_headlines = len(df_clean)
        except Exception:
            df_clean = pd.read_csv(clean_csv)
            total_headlines = len(df_clean)

    if daily_exists:
        try:
            df_daily = sentiment_repo.load_daily_sentiment()
            total_days = len(df_daily)
            if total_days > 0:
                date_range["start"] = str(df_daily["Date"].min().date())
                date_range["end"] = str(df_daily["Date"].max().date())
        except Exception:
            df_daily = pd.read_csv(daily_csv, parse_dates=["Date"])
            total_days = len(df_daily)
            if total_days > 0:
                date_range["start"] = str(df_daily["Date"].min().date())
                date_range["end"] = str(df_daily["Date"].max().date())

    return {
        "clean_file_exists": clean_exists,
        "daily_file_exists": daily_exists,
        "total_headlines": total_headlines,
        "total_days": total_days,
        "date_range": date_range,
    }


def get_daily_preview(page: int = 1, page_size: int = 20) -> PreviewResponse:
    """
    Kembalikan halaman dari `headlines_daily_sentiment.csv` (output pipeline sentimen).

    Berbeda dengan `/feature-engineering/preview` (generic, N baris pertama dari
    file apa saja di data/processed/): endpoint ini khusus hasil pipeline sentimen
    dan mendukung pagination (`page`/`page_size`) alih-alih N baris pertama.
    """
    repos = get_repositories()
    sentiment_repo: SentimentRepository = repos["sentiment"]

    daily_csv = _daily_csv()
    if not daily_csv.exists():
        raise NotFoundError(
            "Pipeline belum dijalankan. Jalankan POST /sentiment/pipeline/run terlebih dahulu.",
        )

    try:
        df = sentiment_repo.load_daily_sentiment()
    except Exception:
        df = pd.read_csv(daily_csv)

    total_rows = len(df)
    start = (page - 1) * page_size
    end = start + page_size
    rows = df.iloc[start:end].to_dict(orient="records")

    return PreviewResponse(
        source="sentiment",
        filename="headlines_daily_sentiment.csv",
        total_rows=total_rows,
        columns=list(df.columns),
        rows=rows,
    )


def get_model_status() -> dict:
    model_path_str = os.environ["FINBERT_MODEL_NAME"]
    model_path = Path(model_path_str)

    # Deteksi apakah path adalah HuggingFace cache format (ada subdir snapshots/)
    snapshots_dir = model_path / "snapshots"
    refs_main = model_path / "refs" / "main"

    snapshot_path: Path | None = None
    source: str

    if snapshots_dir.exists() and refs_main.exists():
        # HF cache format — baca commit hash aktif dari refs/main
        commit_hash = refs_main.read_text().strip()
        snapshot_path = snapshots_dir / commit_hash
        source = "local_snapshot"
    elif model_path.is_dir():
        # Direktori model biasa (bukan HF cache)
        snapshot_path = model_path
        source = "local_dir"
    else:
        # Asumsi HuggingFace Hub (string seperti "ProsusAI/finbert")
        source = "huggingface_hub"

    # Verifikasi keberadaan file wajib
    check_dir = snapshot_path if snapshot_path else None
    required_files: dict[str, bool] = {
        f: (check_dir / f).exists() if check_dir else False
        for f in _REQUIRED_MODEL_FILES
    }

    is_available = check_dir is not None and check_dir.exists() and all(required_files.values())

    # Hitung total ukuran file di snapshot dir (MB)
    model_size_mb: float | None = None
    if check_dir and check_dir.exists():
        total_bytes = sum(f.stat().st_size for f in check_dir.iterdir() if f.is_file())
        model_size_mb = round(total_bytes / (1024 ** 2), 2)

    return {
        "is_available": is_available,
        "model_path": model_path_str,
        "source": source,
        "snapshot_path": str(snapshot_path) if snapshot_path else None,
        "required_files": required_files,
        "model_size_mb": model_size_mb,
    }
