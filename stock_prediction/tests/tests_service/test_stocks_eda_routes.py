"""
tests/tests_service/test_stocks_eda_routes.py

Smoke test untuk 5 endpoint EDA saham GSPC baru di routes_data.py.
Mengecek tiap endpoint mengembalikan status 200, body['success'] is True,
dan memiliki key 'data' (envelope SuccessResponse via EnvelopeRoute).
"""

import pytest
from fastapi.testclient import TestClient

from server import app

# Path endpoint (prefix /api/v1 ditangani app.api.v1.__init__)
STOCK_EDA_ENDPOINTS = [
    "/api/v1/data/eda/stocks/descriptive-stats",
    "/api/v1/data/eda/stocks/time-series",
    "/api/v1/data/eda/stocks/daily-returns",
    "/api/v1/data/eda/stocks/drawdown",
    "/api/v1/data/eda/stocks/summary",
]


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient untuk seluruh test suite."""
    return TestClient(app)


@pytest.mark.parametrize("endpoint", STOCK_EDA_ENDPOINTS)
def test_stocks_eda_endpoint_envelope(client, endpoint):
    """Tiap endpoint EDA saham return 200 dengan envelope success + key data."""
    resp = client.get(endpoint)

    assert resp.status_code == 200, (
        f"Expected 200 for {endpoint}, got {resp.status_code}: {resp.text}"
    )

    body = resp.json()
    assert body.get("success") is True, (
        f"Expected success=True for {endpoint}, got: {body}"
    )
    assert "data" in body, f"Missing 'data' key for {endpoint}: {body}"
