"""
tests/test_schemas/test_base.py — Unit tests untuk app/schemas/base.py
"""

from datetime import datetime, timezone
import pytest
from app.schemas.base import (
    BaseResponse,
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    PaginationMeta,
    ResponseMeta,
    SuccessResponse,
)


class TestSuccessResponse:
    """Test SuccessResponse schema."""

    def test_success_response_basic(self):
        """Test SuccessResponse dengan data sederhana."""
        response = SuccessResponse[dict](data={"x": 1})
        assert response.success is True
        assert response.data["x"] == 1
        assert isinstance(response.meta.timestamp, datetime)
        assert response.meta.timestamp.tzinfo is not None
        assert response.meta.version == "1.0"

    def test_success_response_with_message(self):
        """Test SuccessResponse dengan message."""
        response = SuccessResponse[dict](data={"y": 2}, message="Success")
        assert response.success is True
        assert response.message == "Success"
        assert response.data["y"] == 2

    def test_success_response_default_message(self):
        """Test SuccessResponse dengan default message kosong."""
        response = SuccessResponse[dict](data={"z": 3})
        assert response.message == ""


class TestErrorResponse:
    """Test ErrorResponse schema."""

    def test_error_response_basic(self):
        """Test ErrorResponse dengan ErrorDetail."""
        error_detail = ErrorDetail(code="NOT_FOUND", message="Resource not found")
        response = ErrorResponse(error=error_detail)
        assert response.success is False
        assert response.error.code == "NOT_FOUND"
        assert response.error.message == "Resource not found"

    def test_error_response_meta_exists(self):
        """Test ErrorResponse memiliki meta."""
        error_detail = ErrorDetail(code="ERROR", message="msg")
        response = ErrorResponse(error=error_detail)
        assert isinstance(response.meta, ResponseMeta)
        assert response.meta.version == "1.0"


class TestErrorDetail:
    """Test ErrorDetail schema."""

    def test_error_detail_with_detail(self):
        """Test ErrorDetail dengan detail field."""
        error = ErrorDetail(code="VALIDATION_ERROR", message="Bad input", detail="Field 'x' is required")
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Bad input"
        assert error.detail == "Field 'x' is required"

    def test_error_detail_optional_detail(self):
        """Test ErrorDetail tanpa detail field."""
        error = ErrorDetail(code="ERROR", message="msg")
        assert error.detail is None


class TestPaginatedResponse:
    """Test PaginatedResponse schema."""

    def test_paginated_response_basic(self):
        """Test PaginatedResponse dengan data dan pagination."""
        pagination = PaginationMeta(page=1, page_size=10, total_items=100, total_pages=10)
        meta = ResponseMeta(pagination=pagination)
        response = PaginatedResponse[dict](data=[{"a": 1}], meta=meta)
        assert response.success is True
        assert len(response.data) == 1
        assert response.data[0]["a"] == 1
        assert response.meta.pagination.total_pages == 10

    def test_paginated_response_create_method(self):
        """Test PaginatedResponse.create() helper method."""
        response = PaginatedResponse.create(
            data=[{"item": 1}, {"item": 2}],
            page=1,
            page_size=20,
            total_items=45,
            message="Items retrieved",
        )
        assert response.success is True
        assert len(response.data) == 2
        assert response.message == "Items retrieved"
        assert response.meta.pagination.page == 1
        assert response.meta.pagination.page_size == 20
        assert response.meta.pagination.total_items == 45
        # (45 + 20 - 1) // 20 = 3
        assert response.meta.pagination.total_pages == 3


class TestResponseMeta:
    """Test ResponseMeta schema."""

    def test_response_meta_default_timestamp(self):
        """Test ResponseMeta memiliki timestamp UTC default."""
        meta1 = ResponseMeta()
        meta2 = ResponseMeta()
        assert isinstance(meta1.timestamp, datetime)
        assert isinstance(meta2.timestamp, datetime)
        assert meta1.timestamp.tzinfo is not None
        assert meta2.timestamp.tzinfo is not None

    def test_response_meta_version(self):
        """Test ResponseMeta version default."""
        meta = ResponseMeta()
        assert meta.version == "1.0"

    def test_response_meta_pagination_none_by_default(self):
        """Test ResponseMeta pagination None by default."""
        meta = ResponseMeta()
        assert meta.pagination is None

    def test_response_meta_with_pagination(self):
        """Test ResponseMeta dengan pagination."""
        pagination = PaginationMeta(page=2, page_size=50, total_items=200, total_pages=4)
        meta = ResponseMeta(pagination=pagination)
        assert meta.pagination.page == 2


class TestSerialization:
    """Test serialization ke JSON."""

    def test_success_response_serialization(self):
        """Test SuccessResponse.model_dump(mode='json')."""
        response = SuccessResponse[dict](data={"k": "v"}, message="OK")
        dumped = response.model_dump(mode="json")
        assert "success" in dumped
        assert "data" in dumped
        assert "message" in dumped
        assert "meta" in dumped
        assert dumped["success"] is True
        assert dumped["data"]["k"] == "v"
        assert dumped["message"] == "OK"

    def test_error_response_serialization(self):
        """Test ErrorResponse.model_dump(mode='json')."""
        error = ErrorDetail(code="TEST_ERROR", message="Test")
        response = ErrorResponse(error=error)
        dumped = response.model_dump(mode="json")
        assert dumped["success"] is False
        assert dumped["error"]["code"] == "TEST_ERROR"
        assert dumped["error"]["message"] == "Test"

    def test_timestamp_serialization(self):
        """Test timestamp diserialisasi ke ISO format string."""
        response = SuccessResponse[dict](data={})
        dumped = response.model_dump(mode="json")
        # Timestamp harus string dalam JSON mode
        assert isinstance(dumped["meta"]["timestamp"], str)
        # Harus ISO format
        assert "T" in dumped["meta"]["timestamp"]
