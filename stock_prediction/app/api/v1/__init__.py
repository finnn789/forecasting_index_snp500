"""
app/api/v1/__init__.py — Agregasi seluruh router API v1.

Tambahkan router baru di sini saat endpoint baru dibuat.
"""

from fastapi import APIRouter

from app.api.v1.routes_data import router as data_router
from app.api.v1.routes_feature_engineering import router as fe_router
from app.api.v1.routes_general import router as general_router
from app.api.v1.routes_status import router as status_router

# Router utama tanpa prefix — prefix ditangani oleh server.py
api_router = APIRouter()

# Route: GET /
api_router.include_router(general_router)

# Routes: GET /api/status, GET /api/health
api_router.include_router(status_router, prefix="/api")

# Routes: GET /api/v1/data/...
api_router.include_router(data_router, prefix="/api/v1")

# Routes: GET /api/v1/feature-engineering/...
api_router.include_router(fe_router, prefix="/api/v1")

from app.api.v1.routes_sentiment import router as sentiment_router

# Routes: POST /api/v1/sentiment/pipeline/run, GET /api/v1/sentiment/...
api_router.include_router(sentiment_router, prefix="/api/v1")

from app.api.v1.routes_prediction import router as prediction_router

# Routes: POST /api/v1/predict, GET /api/v1/predict/model/status
api_router.include_router(prediction_router, prefix="/api/v1")
