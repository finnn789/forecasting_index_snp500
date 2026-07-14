"""
tests/test_api/test_envelope.py

Integration test untuk endpoint JSON dengan SuccessResponse envelope.
Mengecek bahwa semua endpoint mengembalikan respons dengan struktur:
  - success: bool
  - data: T
  - message: str
  - meta: { timestamp, version }

Endpoint SSE (streaming) NOT included — hanya JSON endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from server import app


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient untuk seluruh test suite."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def assert_success_envelope(resp, expected_status=200):
    """
    Assertion utility untuk memeriksa envelope success response.

    Args:
        resp: Response object dari TestClient
        expected_status: Status code yang diharapkan

    Returns:
        Parsed JSON body jika assertion pass

    Raises:
        AssertionError jika envelope tidak valid
    """
    assert resp.status_code == expected_status, f"Expected {expected_status}, got {resp.status_code}: {resp.text}"

    body = resp.json()

    # Check success flag
    assert "success" in body, f"Missing 'success' key in response: {body}"
    assert body["success"] is True, f"Expected success=True, got {body['success']}"

    # Check data key
    assert "data" in body, f"Missing 'data' key in success response: {body}"

    # Check message key
    assert "message" in body, f"Missing 'message' key in response: {body}"

    # Check meta structure
    assert "meta" in body, f"Missing 'meta' key in response: {body}"
    assert isinstance(body["meta"], dict), f"meta should be dict: {body['meta']}"
    assert "timestamp" in body["meta"], f"Missing 'timestamp' in meta: {body['meta']}"
    assert "version" in body["meta"], f"Missing 'version' in meta: {body['meta']}"
    assert body["meta"]["version"] == "1.0", f"Expected version 1.0, got {body['meta']['version']}"

    return body


def assert_error_envelope(resp, expected_status):
    """
    Assertion utility untuk memeriksa envelope error response.
    Digunakan ketika endpoint mengembalikan error (4xx/5xx).

    Args:
        resp: Response object dari TestClient
        expected_status: Status code error yang diharapkan

    Returns:
        Parsed JSON body jika assertion pass
    """
    assert resp.status_code == expected_status, f"Expected {expected_status}, got {resp.status_code}"

    body = resp.json()

    # Check error structure
    assert body["success"] is False, f"Expected success=False in error: {body}"
    assert "error" in body, f"Missing 'error' key in error response: {body}"
    assert isinstance(body["error"], dict), f"error should be dict: {body['error']}"
    assert "code" in body["error"], f"Missing 'code' in error: {body['error']}"
    assert "message" in body["error"], f"Missing 'message' in error: {body['error']}"

    # Check meta
    assert "meta" in body, f"Missing 'meta' in error response: {body}"
    assert "timestamp" in body["meta"], f"Missing timestamp in error meta: {body['meta']}"

    return body


# ---------------------------------------------------------------------------
# Test: Root Endpoint
# ---------------------------------------------------------------------------

class TestRootEndpoint:
    """Test GET /"""

    def test_root_endpoint(self, client):
        """GET / — APIInfo envelope"""
        resp = client.get("/")
        body = assert_success_envelope(resp, expected_status=200)

        # Check data structure
        assert isinstance(body["data"], dict), "data should be dict"
        assert "name" in body["data"], "data should have 'name' key"
        assert "version" in body["data"], "data should have 'version' key"
        assert "docs_url" in body["data"], "data should have 'docs_url' key"


# ---------------------------------------------------------------------------
# Test: Status Endpoints
# ---------------------------------------------------------------------------

class TestStatusEndpoints:
    """Test /api/status dan /api/health"""

    def test_status_endpoint(self, client):
        """GET /api/status — ServiceStatus envelope"""
        resp = client.get("/api/status")
        body = assert_success_envelope(resp, expected_status=200)

        # Check data structure
        assert isinstance(body["data"], dict), "data should be dict"
        assert "status" in body["data"], "data should have 'status'"
        assert "uptime_seconds" in body["data"], "data should have 'uptime_seconds'"
        assert "timestamp" in body["data"], "data should have 'timestamp'"
        assert "python_version" in body["data"], "data should have 'python_version'"

    def test_health_endpoint(self, client):
        """GET /api/health — HealthCheck envelope"""
        resp = client.get("/api/health")
        body = assert_success_envelope(resp, expected_status=200)

        # Check data structure
        assert isinstance(body["data"], dict), "data should be dict"
        assert "status" in body["data"], "data should have 'status'"


# ---------------------------------------------------------------------------
# Test: Sentiment Pipeline Endpoints
# ---------------------------------------------------------------------------

class TestSentimentEndpoints:
    """Test /api/v1/sentiment/* JSON endpoints (NOT streaming)"""

    def test_sentiment_pipeline_status(self, client):
        """GET /api/v1/sentiment/pipeline/status — PipelineStatusResponse envelope"""
        resp = client.get("/api/v1/sentiment/pipeline/status")
        body = assert_success_envelope(resp, expected_status=200)

        assert isinstance(body["data"], dict), "data should be dict"

    def test_sentiment_data_preview(self, client):
        """GET /api/v1/sentiment/data/preview — PreviewResponse envelope"""
        resp = client.get("/api/v1/sentiment/data/preview")

        if resp.status_code == 503:
            body = assert_error_envelope(resp, expected_status=503)
        else:
            body = assert_success_envelope(resp, expected_status=200)
            assert isinstance(body["data"], dict)

    def test_sentiment_model_status(self, client):
        """GET /api/v1/sentiment/model/status — ModelStatusResponse envelope"""
        resp = client.get("/api/v1/sentiment/model/status")
        body = assert_success_envelope(resp, expected_status=200)

        assert isinstance(body["data"], dict), "data should be dict"


# ---------------------------------------------------------------------------
# Test: Data Analysis Endpoints (notebooks/01_EDA_stock_data.ipynb & 02_EDA_sentiment_data.ipynb)
# ---------------------------------------------------------------------------

STOCK_ANALYSIS_ENDPOINTS = [
    "/api/v1/data-analysis/stocks/raw-info",
    "/api/v1/data-analysis/stocks/descriptive-stats",
    "/api/v1/data-analysis/stocks/price-volume",
    "/api/v1/data-analysis/stocks/daily-returns",
    "/api/v1/data-analysis/stocks/rolling-stats",
    "/api/v1/data-analysis/stocks/ohlc-spread",
    "/api/v1/data-analysis/stocks/correlation",
    "/api/v1/data-analysis/stocks/seasonality",
    "/api/v1/data-analysis/stocks/cumulative-return-drawdown",
    "/api/v1/data-analysis/stocks/summary",
    "/api/v1/data-analysis/stocks/preprocessing",
    "/api/v1/data-analysis/combined/pipeline-steps",
]

SENTIMENT_RAW_ANALYSIS_ENDPOINTS = [
    "/api/v1/data-analysis/sentiment/raw-info",
    "/api/v1/data-analysis/sentiment/news-per-year",
    "/api/v1/data-analysis/sentiment/news-per-day",
    "/api/v1/data-analysis/sentiment/headline-length",
    "/api/v1/data-analysis/sentiment/closing-price",
    "/api/v1/data-analysis/sentiment/preprocessing",
]

# Butuh data/processed/sentiment/headlines_clean.csv (hasil pipeline FinBERT) — bisa 404
# di lingkungan yang belum pernah menjalankan POST /sentiment/pipeline/run.
SENTIMENT_SCORED_ANALYSIS_ENDPOINTS = [
    "/api/v1/data-analysis/sentiment/scoring-distribution",
    "/api/v1/data-analysis/sentiment/daily-aggregation",
    "/api/v1/data-analysis/sentiment/method-comparison",
]


class TestDataAnalysisEndpoints:
    """Test /api/v1/data-analysis/* endpoints"""

    @pytest.mark.parametrize("endpoint", STOCK_ANALYSIS_ENDPOINTS)
    def test_stock_analysis_endpoint(self, client, endpoint):
        resp = client.get(endpoint)
        body = assert_success_envelope(resp, expected_status=200)
        assert isinstance(body["data"], dict)

    @pytest.mark.parametrize("endpoint", SENTIMENT_RAW_ANALYSIS_ENDPOINTS)
    def test_sentiment_raw_analysis_endpoint(self, client, endpoint):
        resp = client.get(endpoint)
        body = assert_success_envelope(resp, expected_status=200)
        assert isinstance(body["data"], dict)

    @pytest.mark.parametrize("endpoint", SENTIMENT_SCORED_ANALYSIS_ENDPOINTS)
    def test_sentiment_scored_analysis_endpoint(self, client, endpoint):
        resp = client.get(endpoint)

        if resp.status_code == 404:
            body = assert_error_envelope(resp, expected_status=404)
        else:
            body = assert_success_envelope(resp, expected_status=200)
            assert isinstance(body["data"], dict)


# ---------------------------------------------------------------------------
# Test: Error Handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Test error envelope untuk route yang tidak ada"""

    def test_unknown_route_returns_error_envelope(self, client):
        """GET /api/v1/nonexistent-zzz — 404 dengan error envelope"""
        resp = client.get("/api/v1/nonexistent-zzz")
        body = assert_error_envelope(resp, expected_status=404)

        # Pastikan error code ada
        assert body["error"]["code"], "error.code should not be empty"


# ---------------------------------------------------------------------------
# Test: SSE Endpoint (Streaming) — NOT JSON
# ---------------------------------------------------------------------------

class TestStreamingEndpoints:
    """Test endpoint streaming SSE"""

    def test_sentiment_pipeline_run_is_sse(self, client):
        """
        POST /api/v1/sentiment/pipeline/run — Server-Sent Events (streaming).

        Endpoint ini mengembalikan text/event-stream, bukan JSON.
        Cukup cek bahwa:
        1. Status code 200
        2. Content-Type adalah text/event-stream
        3. JANGAN consume response body penuh — cukup close connection
        """
        resp = client.post(
            "/api/v1/sentiment/pipeline/run",
            params={"batch_size": 32}
        )

        # Cek status code dan content-type header
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert "text/event-stream" in resp.headers.get("content-type", ""), \
            f"Expected text/event-stream, got {resp.headers.get('content-type')}"

        # JANGAN consume body — stream dapat ditutup dengan benar
        # Cukup close response
        resp.close()
