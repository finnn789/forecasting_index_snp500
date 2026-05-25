"""
app/api/v1/routes_feature_engineering.py

Endpoint read-only untuk inspeksi data di data/processed/.
Tidak ada eksekusi pipeline — hanya membaca metadata dan isi file.
"""

import logging
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.schemas.base import SuccessResponse
from app.schemas.sentiment import (
    ColumnInfoResponse,
    PreviewResponse,
    ProcessedDataInfo,
    ProcessedFileInfo,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Feature Engineering"])

PROCESSED_DIR = Path("data/processed")
STOCKS_DIR    = PROCESSED_DIR / "stocks"
SENTIMENT_DIR = PROCESSED_DIR / "sentiment"

_VALID_SOURCES = {"stocks", "sentiment"}
_SOURCE_DIR_MAP = {
    "stocks":    STOCKS_DIR,
    "sentiment": SENTIMENT_DIR,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_file_info(path: Path) -> ProcessedFileInfo:
    """Baca metadata satu file CSV tanpa memuat seluruh data ke memori."""
    df = pd.read_csv(path, nrows=0)          # baca header saja untuk kolom
    total_rows = sum(1 for _ in open(path)) - 1  # hitung baris tanpa load ke memori

    date_start = date_end = None
    if "Date" in df.columns:
        df_date = pd.read_csv(path, usecols=["Date"], parse_dates=["Date"])
        date_start = str(df_date["Date"].min().date())
        date_end   = str(df_date["Date"].max().date())

    return ProcessedFileInfo(
        filename=path.name,
        path=str(path),
        total_rows=total_rows,
        columns=df.columns.tolist(),
        date_start=date_start,
        date_end=date_end,
    )


def _get_csv_path(source: str, file: str) -> Path:
    """Resolve path file CSV dari source + nama file (dengan atau tanpa .csv)."""
    filename = file if file.endswith(".csv") else f"{file}.csv"
    path = _SOURCE_DIR_MAP[source] / filename
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"File '{filename}' tidak ditemukan di data/processed/{source}/. "
                f"Jalankan pipeline preprocessing terlebih dahulu."
            ),
        )
    return path


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/feature-engineering/info",
    response_model=SuccessResponse[ProcessedDataInfo],
    summary="Daftar File di data/processed/",
    description=(
        "Scan seluruh isi data/processed/ dan tampilkan metadata tiap file CSV: "
        "nama file, jumlah baris, kolom, dan rentang tanggal. "
        "Tidak ada eksekusi pipeline."
    ),
)
async def fe_info() -> SuccessResponse[ProcessedDataInfo]:
    logger.info("[FE-Info] Scan data/processed/ dimulai...")

    if not PROCESSED_DIR.exists():
        raise HTTPException(
            status_code=503,
            detail="Direktori data/processed/ belum tersedia.",
        )

    stocks_info:    list[ProcessedFileInfo] = []
    sentiment_info: list[ProcessedFileInfo] = []

    for source, subdir in _SOURCE_DIR_MAP.items():
        if not subdir.exists():
            logger.warning("[FE-Info] Subdirektori tidak ditemukan: %s", subdir)
            continue

        csv_files = sorted(f for f in subdir.iterdir() if f.is_file() and f.suffix == ".csv")
        logger.info("[FE-Info] '%s' — %d file CSV ditemukan", source, len(csv_files))

        for csv_path in csv_files:
            try:
                info = _build_file_info(csv_path)
                if source == "stocks":
                    stocks_info.append(info)
                else:
                    sentiment_info.append(info)
                logger.info(
                    "[FE-Info] %s/%s — %d baris | %d kolom",
                    source, csv_path.name, info.total_rows, len(info.columns),
                )
            except Exception as exc:
                logger.warning("[FE-Info] Gagal membaca %s: %s", csv_path.name, exc)

    total = len(stocks_info) + len(sentiment_info)
    logger.info("[FE-Info] Scan selesai — total %d file.", total)

    result = ProcessedDataInfo(
        stocks=stocks_info,
        sentiment=sentiment_info,
        total_files=total,
    )
    return SuccessResponse[ProcessedDataInfo](data=result, message="Daftar file processed berhasil dimuat")


@router.get(
    "/feature-engineering/columns",
    response_model=SuccessResponse[ColumnInfoResponse],
    summary="Kolom & Tipe Data Sebuah File",
    description=(
        "Tampilkan nama kolom, tipe data Pandas, dan jumlah missing values "
        "dari satu file CSV di data/processed/. Tidak ada eksekusi pipeline."
    ),
)
async def fe_columns(
    source: str = Query(
        ...,
        description="Subdirektori sumber: 'stocks' atau 'sentiment'",
        examples=["stocks", "sentiment"],
    ),
    file: str = Query(
        ...,
        description="Nama file tanpa ekstensi, misal 'GSPC_2018_2024' atau 'headlines_daily_sentiment'",
        examples=["GSPC_2018_2024", "headlines_daily_sentiment"],
    ),
) -> SuccessResponse[ColumnInfoResponse]:
    if source not in _VALID_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Parameter 'source' tidak valid: '{source}'. Pilihan: {sorted(_VALID_SOURCES)}",
        )

    path = _get_csv_path(source, file)
    logger.info("[FE-Columns] Membaca kolom dari: %s", path)

    df = pd.read_csv(path)
    missing = df.isnull().sum().to_dict()

    logger.info(
        "[FE-Columns] %s — %d baris | %d kolom",
        path.name, len(df), len(df.columns),
    )

    result = ColumnInfoResponse(
        source=source,
        filename=path.name,
        total_rows=len(df),
        columns=df.columns.tolist(),
        dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
        missing_values={k: int(v) for k, v in missing.items()},
    )
    return SuccessResponse[ColumnInfoResponse](data=result, message="Informasi kolom berhasil dimuat")


@router.get(
    "/feature-engineering/preview",
    response_model=SuccessResponse[PreviewResponse],
    summary="Preview N Baris Pertama Sebuah File",
    description=(
        "Tampilkan N baris pertama dari satu file CSV di data/processed/. "
        "Default n=5, maksimum n=50. Tidak ada eksekusi pipeline."
    ),
)
async def fe_preview(
    source: str = Query(
        ...,
        description="Subdirektori sumber: 'stocks' atau 'sentiment'",
        examples=["stocks", "sentiment"],
    ),
    file: str = Query(
        ...,
        description="Nama file tanpa ekstensi",
        examples=["GSPC_2018_2024", "headlines_daily_sentiment"],
    ),
    n: int = Query(
        default=5,
        ge=1,
        le=50,
        description="Jumlah baris yang ditampilkan (1–50)",
    ),
) -> SuccessResponse[PreviewResponse]:
    if source not in _VALID_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Parameter 'source' tidak valid: '{source}'. Pilihan: {sorted(_VALID_SOURCES)}",
        )

    path = _get_csv_path(source, file)
    logger.info("[FE-Preview] Membaca %d baris dari: %s", n, path)

    df_full    = pd.read_csv(path)
    total_rows = len(df_full)
    df_preview = df_full.head(n)

    # Serialisasi aman ke JSON
    rows = []
    for record in df_preview.to_dict(orient="records"):
        cleaned = {}
        for k, v in record.items():
            if hasattr(v, "item"):
                cleaned[k] = v.item()
            elif isinstance(v, float) and v != v:   # NaN check
                cleaned[k] = None
            elif hasattr(v, "isoformat"):
                cleaned[k] = str(v)
            else:
                cleaned[k] = v
        rows.append(cleaned)

    logger.info("[FE-Preview] %s — preview %d/%d baris", path.name, len(rows), total_rows)

    result = PreviewResponse(
        source=source,
        filename=path.name,
        total_rows=total_rows,
        columns=df_full.columns.tolist(),
        rows=rows,
    )
    return SuccessResponse[PreviewResponse](data=result, message="Preview data berhasil dimuat")
