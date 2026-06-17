"""
app/api/v1/routes_feature_engineering.py

Endpoint read-only untuk inspeksi data di data/processed/.
Tidak ada eksekusi pipeline — hanya membaca metadata dan isi file.
"""

from fastapi import APIRouter, Query

from app.core.envelope import EnvelopeRoute
from app.schemas.sentiment import (
    ColumnInfoResponse,
    PreviewResponse,
    ProcessedDataInfo,
)
from app.services import feature_service

router = APIRouter(tags=["Feature Engineering"], route_class=EnvelopeRoute)


@router.get(
    "/feature-engineering/info",
    response_model=ProcessedDataInfo,
    summary="Daftar File di data/processed/",
    description=(
        "Scan seluruh isi data/processed/ dan tampilkan metadata tiap file CSV: "
        "nama file, jumlah baris, kolom, dan rentang tanggal. "
        "Tidak ada eksekusi pipeline."
    ),
    openapi_extra={"x-message": "Daftar file processed berhasil dimuat"},
)
async def fe_info() -> ProcessedDataInfo:
    return await feature_service.get_processed_info()


@router.get(
    "/feature-engineering/columns",
    response_model=ColumnInfoResponse,
    summary="Kolom & Tipe Data Sebuah File",
    description=(
        "Tampilkan nama kolom, tipe data Pandas, dan jumlah missing values "
        "dari satu file CSV di data/processed/. Tidak ada eksekusi pipeline."
    ),
    openapi_extra={"x-message": "Informasi kolom berhasil dimuat"},
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
) -> ColumnInfoResponse:
    return await feature_service.get_columns(source, file)


@router.get(
    "/feature-engineering/preview",
    response_model=PreviewResponse,
    summary="Preview N Baris Pertama Sebuah File",
    description=(
        "Tampilkan N baris pertama dari satu file CSV di data/processed/. "
        "Default n=5, maksimum n=50. Tidak ada eksekusi pipeline."
    ),
    openapi_extra={"x-message": "Preview data berhasil dimuat"},
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
) -> PreviewResponse:
    return await feature_service.get_preview(source, file, n)
