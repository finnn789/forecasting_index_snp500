"""
app/core/exceptions.py — Hierarchy custom domain exceptions.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base exception untuk semua domain error aplikasi."""

    code: str = "DOMAIN_ERROR"
    http_status: int = 500

    def __init__(
        self,
        message: str,
        code: str | None = None,
        detail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code if code is not None else self.__class__.code
        self.detail = detail


class NotFoundError(DomainError):
    code = "NOT_FOUND"
    http_status = 404


class ValidationError(DomainError):
    code = "VALIDATION_ERROR"
    http_status = 422


class ModelNotLoadedError(DomainError):
    code = "MODEL_NOT_LOADED"
    http_status = 503


class PipelineError(DomainError):
    code = "PIPELINE_ERROR"
    http_status = 500


class ExternalServiceError(DomainError):
    code = "EXTERNAL_SERVICE_ERROR"
    http_status = 502
