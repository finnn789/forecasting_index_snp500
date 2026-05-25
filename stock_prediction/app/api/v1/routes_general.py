"""
app/api/v1/routes_general.py — Route umum (root endpoint).
"""

from fastapi import APIRouter

from app.config import APP_TITLE, APP_VERSION
from app.schemas.base import SuccessResponse
from app.schemas.status import APIInfo

router = APIRouter(tags=["General"])


@router.get(
    "/",
    response_model=SuccessResponse[APIInfo],
    summary="API Information",
    description="Menampilkan informasi dasar tentang API dan tautan ke halaman dokumentasi.",
)
async def root() -> SuccessResponse[APIInfo]:
    data = APIInfo(
        name=APP_TITLE,
        version=APP_VERSION,
        description="FastAPI backend for stock market price prediction using FinBERT + LSTM (TensorFlow).",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    return SuccessResponse[APIInfo](data=data, message="API information retrieved")
