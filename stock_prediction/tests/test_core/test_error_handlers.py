"""
tests/test_core/test_error_handlers.py — Integration tests untuk app/core/error_handlers.py
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.error_handlers import register_exception_handlers
from app.core.exceptions import NotFoundError, ValidationError, DomainError


def _make_app() -> FastAPI:
    """Factory untuk membuat FastAPI app dengan exception handlers."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/raise-not-found")
    def raise_not_found():
        raise NotFoundError("item not found")

    @app.get("/raise-validation")
    def raise_validation():
        raise ValidationError("bad input")

    @app.get("/raise-generic")
    def raise_generic():
        raise RuntimeError("boom")

    @app.get("/raise-domain-error")
    def raise_domain_error():
        raise DomainError("domain error message")

    return app


class TestNotFoundHandler:
    """Test NotFoundError exception handler."""

    def test_not_found_handler_returns_404_and_envelope(self):
        """Test NotFoundError returns 404 with envelope."""
        app = _make_app()
        client = TestClient(app)
        response = client.get("/raise-not-found")

        assert response.status_code == 404
        json_data = response.json()
        assert json_data["success"] is False
        assert json_data["error"]["code"] == "NOT_FOUND"
        assert json_data["error"]["message"] == "item not found"

    def test_not_found_response_has_meta(self):
        """Test NotFoundError response has meta field."""
        app = _make_app()
        client = TestClient(app)
        response = client.get("/raise-not-found")
        json_data = response.json()
        assert "meta" in json_data
        assert "timestamp" in json_data["meta"]
        assert "version" in json_data["meta"]


class TestValidationHandler:
    """Test ValidationError exception handler."""

    def test_validation_handler_returns_422(self):
        """Test ValidationError returns 422."""
        app = _make_app()
        client = TestClient(app)
        response = client.get("/raise-validation")

        assert response.status_code == 422
        json_data = response.json()
        assert json_data["success"] is False
        assert json_data["error"]["code"] == "VALIDATION_ERROR"
        assert json_data["error"]["message"] == "bad input"


class TestGenericExceptionHandler:
    """Test generic exception handler."""

    def test_generic_exception_returns_500(self):
        """Test unhandled exception returns 500."""
        app = _make_app()
        # Suppress exception logging for cleaner test output
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/raise-generic")

        assert response.status_code == 500
        json_data = response.json()
        assert json_data["success"] is False
        assert json_data["error"]["code"] == "INTERNAL_ERROR"

    def test_generic_exception_has_error_field(self):
        """Test generic exception response has error field."""
        app = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/raise-generic")
        json_data = response.json()
        assert "error" in json_data
        assert "message" in json_data["error"]


class TestDomainErrorHandler:
    """Test DomainError exception handler."""

    def test_domain_error_returns_correct_status(self):
        """Test DomainError returns correct http_status."""
        app = _make_app()
        client = TestClient(app)
        response = client.get("/raise-domain-error")

        # DomainError default http_status = 500
        assert response.status_code == 500
        json_data = response.json()
        assert json_data["success"] is False
        assert json_data["error"]["code"] == "DOMAIN_ERROR"


class TestNotFoundRoute:
    """Test 404 for non-existent routes."""

    def test_404_route_not_exist_returns_envelope(self):
        """Test accessing non-existent route returns JSON envelope."""
        app = _make_app()
        client = TestClient(app)
        response = client.get("/nope")

        assert response.status_code == 404
        json_data = response.json()
        assert "success" in json_data
        assert "error" in json_data
        assert json_data["success"] is False


class TestErrorResponseStructure:
    """Test error response structure compliance."""

    def test_error_has_code_message_fields(self):
        """Test error object has code and message fields."""
        app = _make_app()
        client = TestClient(app)
        response = client.get("/raise-not-found")
        json_data = response.json()
        error = json_data["error"]
        assert "code" in error
        assert "message" in error

    def test_error_detail_optional(self):
        """Test error detail field is optional."""
        app = _make_app()
        client = TestClient(app)
        response = client.get("/raise-not-found")
        json_data = response.json()
        # detail field may or may not be present, but should be None or not there
        error = json_data["error"]
        if "detail" in error:
            assert error["detail"] is None or isinstance(error["detail"], str)


class TestResponseEnvelope:
    """Test consistent response envelope structure."""

    def test_all_error_responses_have_meta(self):
        """Test all error responses include meta field."""
        app = _make_app()
        client = TestClient(app, raise_server_exceptions=False)

        endpoints = ["/raise-not-found", "/raise-validation", "/raise-generic", "/nope"]
        for endpoint in endpoints:
            response = client.get(endpoint)
            json_data = response.json()
            assert "meta" in json_data, f"Missing meta in {endpoint}"
            assert "timestamp" in json_data["meta"]
            assert "version" in json_data["meta"]
