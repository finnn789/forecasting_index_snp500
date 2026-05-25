"""
app/api/v1/routes_status.py — Endpoint status dan health check.
"""

import platform
from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.state import get_uptime
from app.schemas.base import SuccessResponse
from app.schemas.status import HealthCheck, ServiceStatus

router = APIRouter(tags=["Status"])


@router.get(
    "/status",
    response_model=SuccessResponse[ServiceStatus],
    summary="Service Status",
    description=(
        "Menampilkan status lengkap layanan, termasuk uptime server, "
        "waktu saat ini (UTC), versi Python, dan informasi platform OS."
    ),
)
async def get_status() -> SuccessResponse[ServiceStatus]:
    data = ServiceStatus(
        status="healthy",
        uptime_seconds=get_uptime(),
        timestamp=datetime.now(timezone.utc).isoformat(),
        python_version=platform.python_version(),
        platform=platform.platform(),
    )
    return SuccessResponse[ServiceStatus](data=data, message="Service status retrieved")


@router.get(
    "/health",
    response_model=SuccessResponse[HealthCheck],
    summary="Health Check",
    description=(
        "Endpoint ringan untuk liveness probe. "
        "Cocok digunakan oleh Docker health check atau Kubernetes readiness probe."
    ),
)
async def health_check() -> SuccessResponse[HealthCheck]:
    data = HealthCheck(
        status="ok",
        message="Service is running normally.",
    )
    return SuccessResponse[HealthCheck](data=data, message="Service is healthy")
