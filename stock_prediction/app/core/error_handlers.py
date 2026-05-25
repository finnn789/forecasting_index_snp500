"""
app/core/error_handlers.py — Global exception handlers untuk FastAPI.

Daftarkan ke app via: register_exception_handlers(app)
"""

from __future__ import annotations

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import DomainError
from app.core.settings import settings
from app.schemas.base import ErrorDetail, ErrorResponse

logger = logging.getLogger("app")


def _error_response(
    code: str,
    message: str,
    detail: str | None = None,
    status_code: int = 500,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorDetail(code=code, message=message, detail=detail)
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Daftarkan semua global exception handler ke instance FastAPI."""

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        if exc.http_status >= 500:
            logger.error(
                "DomainError [%s] %s — path=%s detail=%s",
                exc.code,
                exc.message,
                request.url.path,
                exc.detail,
            )
        return _error_response(
            code=exc.code,
            message=exc.message,
            detail=exc.detail,
            status_code=exc.http_status,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Ringkas error pydantic menjadi string singkat
        errors = exc.errors()
        detail = "; ".join(
            f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}"
            for e in errors[:5]  # Batasi 5 error pertama
        )
        return _error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            detail=detail,
            status_code=422,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = f"HTTP_{exc.status_code}"
        message = str(exc.detail) if exc.detail else "HTTP error"
        if exc.status_code >= 500:
            logger.error(
                "HTTPException [%s] %s — path=%s",
                exc.status_code,
                message,
                request.url.path,
            )
        return _error_response(
            code=code,
            message=message,
            status_code=exc.status_code,
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "Unhandled exception — path=%s type=%s msg=%s",
            request.url.path,
            type(exc).__name__,
            str(exc),
            exc_info=True,
        )
        detail: str | None = None
        if settings.debug:
            detail = traceback.format_exc()
        return _error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            detail=detail,
            status_code=500,
        )
