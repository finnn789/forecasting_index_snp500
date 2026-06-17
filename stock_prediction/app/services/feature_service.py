"""Business logic untuk feature engineering dan inspeksi data processed."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from app.core.exceptions import NotFoundError
from app.helpers.csv_inspector import (
    PROCESSED_DIR,
    SOURCE_DIR_MAP,
    build_file_info,
    resolve_csv_path,
)
from app.helpers.serialization import to_json_safe_records
from app.schemas.sentiment import (
    ColumnInfoResponse,
    PreviewResponse,
    ProcessedDataInfo,
    ProcessedFileInfo,
)

logger = logging.getLogger(__name__)


async def get_processed_info() -> ProcessedDataInfo:
    """Scan data/processed/ dan kembalikan metadata semua file CSV yang tersedia."""
    logger.info("[FE-Info] Scan data/processed/ dimulai...")

    if not PROCESSED_DIR.exists():
        raise NotFoundError(
            "Direktori data/processed/ belum tersedia.",
            code="PROCESSED_DIR_NOT_FOUND",
        )

    stocks_info: list[ProcessedFileInfo] = []
    sentiment_info: list[ProcessedFileInfo] = []

    for source, subdir in SOURCE_DIR_MAP.items():
        if not subdir.exists():
            logger.warning("[FE-Info] Subdirektori tidak ditemukan: %s", subdir)
            continue

        csv_files = sorted(
            
            f for f in subdir.iterdir() if f.is_file() and f.suffix == ".csv"
        )
        logger.info("[FE-Info] '%s' — %d file CSV ditemukan", source, len(csv_files))

        for csv_path in csv_files:
            try:
                info = build_file_info(csv_path)
                if source == "stocks":
                    stocks_info.append(info)
                else:
                    sentiment_info.append(info)
                logger.info(
                    "[FE-Info] %s/%s — %d baris | %d kolom",
                    source,
                    csv_path.name,
                    info.total_rows,
                    len(info.columns),
                )
            except Exception as exc:
                logger.warning("[FE-Info] Gagal membaca %s: %s", csv_path.name, exc)

    total = len(stocks_info) + len(sentiment_info)
    logger.info("[FE-Info] Scan selesai — total %d file.", total)

    return ProcessedDataInfo(
        stocks=stocks_info,
        sentiment=sentiment_info,
        total_files=total,
    )


async def get_columns(source: str, file: str) -> ColumnInfoResponse:
    """Baca kolom, tipe data, dan missing values dari satu file CSV di data/processed/."""
    path = resolve_csv_path(source, file)
    logger.info("[FE-Columns] Membaca kolom dari: %s", path)

    df = pd.read_csv(path)
    missing = df.isnull().sum().to_dict()

    logger.info(
        "[FE-Columns] %s — %d baris | %d kolom",
        path.name,
        len(df),
        len(df.columns),
    )

    return ColumnInfoResponse(
        source=source,
        filename=path.name,
        total_rows=len(df),
        columns=df.columns.tolist(),
        dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
        missing_values={k: int(v) for k, v in missing.items()},
    )


async def get_preview(source: str, file: str, n: int = 5) -> PreviewResponse:
    """Kembalikan N baris pertama dari satu file CSV di data/processed/."""
    path = resolve_csv_path(source, file)
    logger.info("[FE-Preview] Membaca %d baris dari: %s", n, path)

    df_full = pd.read_csv(path)
    total_rows = len(df_full)

    rows = to_json_safe_records(df_full, n)

    logger.info(
        "[FE-Preview] %s — preview %d/%d baris", path.name, len(rows), total_rows
    )

    return PreviewResponse(
        source=source,
        filename=path.name,
        total_rows=total_rows,
        columns=df_full.columns.tolist(),
        rows=rows,
    )
