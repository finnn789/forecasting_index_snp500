"""
tests/test_core/test_exceptions.py — Unit tests untuk app/core/exceptions.py
"""

import pytest
from app.core.exceptions import (
    DomainError,
    ExternalServiceError,
    ModelNotLoadedError,
    NotFoundError,
    PipelineError,
    ValidationError,
)


class TestDomainError:
    """Test DomainError base class."""

    def test_domain_error_default(self):
        """Test DomainError dengan pesan."""
        error = DomainError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.code == "DOMAIN_ERROR"
        assert error.http_status == 500

    def test_domain_error_with_custom_code(self):
        """Test DomainError dengan custom code."""
        error = DomainError("msg", code="CUSTOM_ERROR")
        assert error.code == "CUSTOM_ERROR"

    def test_domain_error_with_detail(self):
        """Test DomainError dengan detail field."""
        error = DomainError("msg", detail="Extra information")
        assert error.detail == "Extra information"

    def test_domain_error_str(self):
        """Test DomainError string representation."""
        error = DomainError("Error message")
        assert str(error) == "Error message"


class TestNotFoundError:
    """Test NotFoundError."""

    def test_not_found_error_defaults(self):
        """Test NotFoundError code dan http_status."""
        error = NotFoundError("Item not found")
        assert error.message == "Item not found"
        assert error.code == "NOT_FOUND"
        assert error.http_status == 404

    def test_not_found_error_custom_code_override(self):
        """Test NotFoundError dengan custom code override."""
        error = NotFoundError("User not found", code="USER_NOT_FOUND")
        assert error.code == "USER_NOT_FOUND"
        assert error.http_status == 404  # http_status tetap


class TestValidationError:
    """Test ValidationError."""

    def test_validation_error_defaults(self):
        """Test ValidationError http_status."""
        error = ValidationError("Invalid input")
        assert error.code == "VALIDATION_ERROR"
        assert error.http_status == 422

    def test_validation_error_with_detail(self):
        """Test ValidationError dengan detail."""
        error = ValidationError("Bad request", detail="Field 'age' must be positive")
        assert error.detail == "Field 'age' must be positive"


class TestModelNotLoadedError:
    """Test ModelNotLoadedError."""

    def test_model_not_loaded_error_defaults(self):
        """Test ModelNotLoadedError http_status 503."""
        error = ModelNotLoadedError("LSTM model not loaded")
        assert error.code == "MODEL_NOT_LOADED"
        assert error.http_status == 503


class TestPipelineError:
    """Test PipelineError."""

    def test_pipeline_error_defaults(self):
        """Test PipelineError http_status 500."""
        error = PipelineError("Pipeline processing failed")
        assert error.code == "PIPELINE_ERROR"
        assert error.http_status == 500


class TestExternalServiceError:
    """Test ExternalServiceError."""

    def test_external_service_error_defaults(self):
        """Test ExternalServiceError http_status 502."""
        error = ExternalServiceError("Stock API unreachable")
        assert error.code == "EXTERNAL_SERVICE_ERROR"
        assert error.http_status == 502


class TestErrorCodeOverride:
    """Test code override di subclass."""

    def test_custom_code_override_hierarchy(self):
        """Test inheritance chain code override."""
        # NotFoundError default
        e1 = NotFoundError("x")
        assert e1.code == "NOT_FOUND"

        # Override dengan custom code
        e2 = NotFoundError("x", code="ITEM_NOT_FOUND")
        assert e2.code == "ITEM_NOT_FOUND"

        # Multiple errors maintain their own codes
        e3 = ValidationError("y")
        assert e3.code == "VALIDATION_ERROR"
