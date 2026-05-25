"""
app/schemas/status.py — Pydantic response schemas untuk status endpoint.
"""

from pydantic import BaseModel


class APIInfo(BaseModel):
    """Schema respons untuk endpoint root `/`."""

    name: str
    version: str
    description: str
    docs_url: str
    redoc_url: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Stock Market Prediction API",
                "version": "0.1.0",
                "description": "FastAPI backend for stock market price prediction",
                "docs_url": "/docs",
                "redoc_url": "/redoc",
            }
        }
    }


class ServiceStatus(BaseModel):
    """Schema respons untuk endpoint `/api/status`."""

    status: str
    uptime_seconds: float
    timestamp: str
    python_version: str
    platform: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "uptime_seconds": 42.5,
                "timestamp": "2026-04-23T08:00:00+00:00",
                "python_version": "3.11.0",
                "platform": "Linux-5.15.0-x86_64",
            }
        }
    }


class HealthCheck(BaseModel):
    """Schema respons untuk endpoint `/api/health`."""

    status: str
    message: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok",
                "message": "Service is running normally.",
            }
        }
    }
