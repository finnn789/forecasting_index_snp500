"""
app/schemas/base.py — Base response schemas untuk semua API endpoint.

Semua endpoint WAJIB menggunakan SuccessResponse / ErrorResponse / PaginatedResponse.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class ResponseMeta(BaseModel):
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    version: str = "1.0"
    pagination: PaginationMeta | None = None


class BaseResponse(BaseModel, Generic[T]):
    success: bool
    message: str = ""
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class SuccessResponse(BaseResponse[T], Generic[T]):
    success: bool = True
    data: T


class ErrorDetail(BaseModel):
    code: str
    message: str
    detail: str | None = None


class ErrorResponse(BaseResponse[None]):
    success: bool = False
    error: ErrorDetail


class PaginatedResponse(BaseModel, Generic[T]):
    """Response untuk collection/list dengan pagination info di meta."""

    success: bool = True
    data: list[T]
    message: str = ""
    meta: ResponseMeta = Field(default_factory=ResponseMeta)

    @classmethod
    def create(
        cls,
        data: list[T],
        page: int,
        page_size: int,
        total_items: int,
        message: str = "",
    ) -> "PaginatedResponse[T]":
        total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0
        pagination = PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )
        meta = ResponseMeta(pagination=pagination)
        return cls(data=data, message=message, meta=meta)
