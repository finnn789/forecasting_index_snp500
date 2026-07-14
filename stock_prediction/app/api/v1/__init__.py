"""
app/api/v1/__init__.py — Agregasi seluruh router API v1.

Tambahkan router baru di sini saat endpoint baru dibuat.
"""

from fastapi import APIRouter

from app.api.v1.routes_data_analysis import router as data_analysis_router
from app.api.v1.routes_general import router as general_router
from app.api.v1.routes_prediction import router as prediction_router
from app.api.v1.routes_sentiment import router as sentiment_router
from app.api.v1.routes_status import router as status_router
from app.api.v1.routes_training import router as training_router

# Router utama tanpa prefix — prefix ditangani oleh server.py
api_router = APIRouter()

# Route: GET /
api_router.include_router(general_router)

# Routes: GET /api/status, GET /api/health
api_router.include_router(status_router, prefix="/api")

# Routes: POST /api/v1/sentiment/pipeline/run, GET /api/v1/sentiment/...
api_router.include_router(sentiment_router, prefix="/api/v1")

# Routes: POST /api/v1/predict, GET /api/v1/predict/model/status
api_router.include_router(prediction_router, prefix="/api/v1")

# Routes: GET /api/v1/data-analysis/stocks/..., GET /api/v1/data-analysis/sentiment/...
api_router.include_router(data_analysis_router, prefix="/api/v1")

# Routes: POST /api/v1/train/notebook05, GET /api/v1/train/notebook05/grid-search-result
api_router.include_router(training_router, prefix="/api/v1")
