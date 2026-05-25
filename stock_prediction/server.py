"""
server.py — Entry point runtime FastAPI
Stock Market Price Prediction System

Swagger UI  : http://localhost:8000/docs
ReDoc       : http://localhost:8000/redoc
"""

import logging
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.v1 import api_router
from app.config import (
    APP_CONTACT,
    APP_DESCRIPTION,
    APP_LICENSE,
    APP_TITLE,
    APP_VERSION,
)
from app.core.error_handlers import register_exception_handlers
from app.core.logging_config import setup_logging
from app.core.state import record_startup

# Inisialisasi logging sebelum komponen lain berjalan
setup_logging()
logger = logging.getLogger("app")

# ---------------------------------------------------------------------------
# Inisialisasi Aplikasi FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    contact=APP_CONTACT,
    license_info=APP_LICENSE,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Ganti ke domain spesifik di production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------
register_exception_handlers(app)

# ---------------------------------------------------------------------------
# Lifecycle Events
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    record_startup()
    logger.info("Server started — %s v%s", APP_TITLE, APP_VERSION)
    logger.info("Swagger UI  : http://localhost:8000/docs")
    logger.info("ReDoc       : http://localhost:8000/redoc")
    logger.info("Status      : http://localhost:8000/api/status")
    logger.info("Health      : http://localhost:8000/api/health")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("Server shutting down — %s", datetime.now(timezone.utc).isoformat())

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
app.include_router(api_router)

# ---------------------------------------------------------------------------
# Custom OpenAPI Schema (Swagger branding + server definitions)
# ---------------------------------------------------------------------------
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=APP_TITLE,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
        contact=APP_CONTACT,
        license_info=APP_LICENSE,
        routes=app.routes,
    )
    schema["servers"] = [
        {"url": "http://localhost:8000", "description": "Local Development"},
        {"url": "http://0.0.0.0:8000",  "description": "Network Access"},
    ]
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]

# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
