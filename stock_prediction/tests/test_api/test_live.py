"""
tests/test_api/test_live.py — Test fitur "Prediksi Live" (fetch OHLCV+berita
live via yfinance -> preprocessing -> inference). `yfinance.Ticker` di-mock
(tanpa internet) supaya test deterministik; FinBERT scoring TETAP pakai model
lokal asli (sudah tersedia di `models/finbert/`, tidak butuh internet, cepat).
"""

from __future__ import annotations

import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from server import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _parse_sse_events(lines) -> list[dict]:
    events = []
    for line in lines:
        if not line or not line.startswith("data: "):
            continue
        events.append(json.loads(line[len("data: "):]))
    return events


def _last_business_day_anchor() -> pd.Timestamp:
    """Hari bursa terakhir <= hari ini. TIDAK pakai `pd.bdate_range(end=today,
    periods=N)` langsung sebagai anchor karena pandas (setidaknya 3.0.2) punya
    quirk: kalau `end` jatuh di akhir pekan, hasilnya kehilangan 1 elemen
    (`periods=N` -> cuma N-1 baris) — jadi harus di-resolve manual dulu ke
    hari bursa asli SEBELUM dipakai sebagai `end=` di `bdate_range` lain,
    supaya test tidak flaky tergantung hari nyata saat dijalankan."""
    anchor = pd.Timestamp.today().normalize()
    while anchor.weekday() >= 5:  # Sabtu=5, Minggu=6
        anchor -= pd.Timedelta(days=1)
    return anchor


class _FakeTicker:
    """Stand-in untuk `yfinance.Ticker` — history() 40 hari bursa sintetis
    (cukup untuk window=20 setelah pct_change buang 1 baris) + news() 2 hari
    kalender terakhir (mirror keterbatasan nyata `.get_news()`)."""

    def __init__(self, n_days: int = 40, news_days: int = 2) -> None:
        self._n_days = n_days
        self._news_days = news_days

    def history(self, period: str = "90d") -> pd.DataFrame:
        dates = pd.bdate_range(end=_last_business_day_anchor(), periods=self._n_days)
        base = 5000.0
        rows = []
        price = base
        for d in dates:
            price *= 1 + 0.001
            rows.append(
                {"Open": price, "High": price * 1.01, "Low": price * 0.99, "Close": price, "Volume": 1_000_000}
            )
        df = pd.DataFrame(rows, index=dates)
        df.index.name = "Date"
        return df

    def get_news(self, count: int = 10) -> list[dict]:
        # Anchor ke hari BURSA terakhir (sama seperti history()) — lihat
        # docstring _last_business_day_anchor().
        business_days = pd.bdate_range(end=_last_business_day_anchor(), periods=self._news_days)
        dates = list(business_days[::-1])
        items = []
        for i, d in enumerate(dates):
            for j in range(3):
                items.append(
                    {
                        "content": {
                            "title": f"S&P 500 sample headline {i}-{j} moves higher on strong earnings",
                            "pubDate": d.strftime("%Y-%m-%dT12:00:00Z"),
                        }
                    }
                )
        return items


@pytest.fixture
def mock_yfinance(monkeypatch):
    monkeypatch.setattr(
        "app.services.live_data_service.yf.Ticker",
        lambda ticker: _FakeTicker(),
    )


@pytest.fixture(autouse=True)
def isolated_live_repo(tmp_path, monkeypatch):
    """Setiap test dapat `LiveDataRepository` SQLite kosong & terisolasi
    (bukan `data/live/live_data.db` proyek asli) — WAJIB sejak akumulasi
    lintas-fetch ditambahkan, supaya test tidak saling bocor state maupun
    menulis ke database live yang sungguhan."""
    from app.repositories.live_data_repository import LiveDataRepository

    repo = LiveDataRepository(db_path=tmp_path / "live_data_test.db")
    monkeypatch.setattr(
        "app.services.live_data_service.get_repositories",
        lambda: {"live_data": repo},
    )


class TestLiveStocksLatest:
    def test_live_stocks_latest_envelope(self, client, mock_yfinance):
        resp = client.get("/api/v1/live/stocks/latest?n=5")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["n"] == 5
        assert len(data["rows"]) == 5
        assert "fetched_at" in data
        assert set(["Date", "Open", "High", "Low", "Close", "Volume"]).issubset(data["columns"])


class TestLiveNewsLatest:
    def test_live_news_latest_envelope(self, client, mock_yfinance):
        resp = client.get("/api/v1/live/news/latest?n=5")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert len(data["headlines"]) == 5
        assert len(data["daily_sentiment"]) == 2  # news_days=2 di _FakeTicker
        assert data["accumulated_days"] == 2
        for h in data["headlines"]:
            assert h["sentiment_label"] in {"positive", "negative", "neutral"}
        for d in data["daily_sentiment"]:
            assert d["headline_count"] == 3


class TestLiveNewsAccumulation:
    """Fitur akumulasi lintas-fetch (permintaan user): headline dari fetch
    SEBELUMNYA tidak boleh hilang saat fetch berikutnya, dan re-fetch hari yang
    sama tidak boleh menghasilkan duplikat (idempotent, keyed by title+date)."""

    def test_accumulates_across_different_days(self, client, monkeypatch):
        class _Day1Ticker(_FakeTicker):
            def get_news(self, count: int = 10) -> list[dict]:
                return [{"content": {
                    "title": "Market rallies on strong jobs report data today",
                    "pubDate": "2024-01-10T12:00:00Z",
                }}]

        class _Day2Ticker(_FakeTicker):
            def get_news(self, count: int = 10) -> list[dict]:
                return [{"content": {
                    "title": "Fed signals rate cut amid inflation cooling down",
                    "pubDate": "2024-01-11T12:00:00Z",
                }}]

        monkeypatch.setattr("app.services.live_data_service.yf.Ticker", lambda ticker: _Day1Ticker())
        resp1 = client.get("/api/v1/live/news/latest?n=10")
        assert resp1.status_code == 200, resp1.text
        data1 = resp1.json()["data"]
        assert data1["accumulated_days"] == 1

        monkeypatch.setattr("app.services.live_data_service.yf.Ticker", lambda ticker: _Day2Ticker())
        resp2 = client.get("/api/v1/live/news/latest?n=10")
        assert resp2.status_code == 200, resp2.text
        data2 = resp2.json()["data"]
        assert data2["accumulated_days"] == 2, "Hari 1 seharusnya tidak hilang saat fetch hari 2"
        assert {d["date"] for d in data2["daily_sentiment"]} == {"2024-01-10", "2024-01-11"}

    def test_refetching_same_day_is_idempotent(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.services.live_data_service.yf.Ticker",
            lambda ticker: _FakeTicker(news_days=1),
        )
        client.get("/api/v1/live/news/latest?n=10")
        resp2 = client.get("/api/v1/live/news/latest?n=10")
        data2 = resp2.json()["data"]
        assert data2["accumulated_days"] == 1
        assert data2["daily_sentiment"][0]["headline_count"] == 3, "Tidak boleh dobel dari 2x fetch hari yang sama"


class TestLivePredictFinbertStream:
    def test_predict_stream_success(self, client, mock_yfinance):
        """Model `finbert_lstm_skripsi` sudah terlatih (artefak resmi tersedia
        di repo) -- dgn data live sintetis 40 hari bursa (cukup utk window=20),
        pipeline penuh (fetch->preprocessing->inference) harus sampai `done`."""
        with client.stream("POST", "/api/v1/live/predict/finbert-lstm") as resp:
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")
            events = _parse_sse_events(resp.iter_lines())

        types = [e["type"] for e in events]
        assert types[0] == "start"
        assert "fetching_ohlcv" in types
        assert "fetching_news" in types
        assert "preprocessing" in types
        assert "inferring" in types
        assert "done" in types, f"Prediksi gagal: {events}"

        done_event = next(e for e in events if e["type"] == "done")
        assert done_event["direction"] in {"up", "down"}
        assert 0.0 <= done_event["probability_up"] <= 1.0
        assert done_event["window"] == 20
        assert done_event["feature_cols"] == [
            "ret_open", "ret_high", "ret_low", "ret_close", "ret_volume", "sentiment_mean",
        ]
        assert done_event["live_sentiment_days"] >= 1

    def test_predict_stream_insufficient_data(self, client, monkeypatch):
        """Kalau data live gabungan (OHLCV+sentimen) < window=20, endpoint WAJIB
        emit error yang jelas -- BUKAN memalsukan hasil prediksi."""
        monkeypatch.setattr(
            "app.services.live_data_service.yf.Ticker",
            lambda ticker: _FakeTicker(n_days=5, news_days=1),
        )
        with client.stream("POST", "/api/v1/live/predict/finbert-lstm") as resp:
            assert resp.status_code == 200
            events = _parse_sse_events(resp.iter_lines())

        types = [e["type"] for e in events]
        assert "error" in types
        assert "done" not in types
        error_event = next(e for e in events if e["type"] == "error")
        assert "tidak cukup" in error_event["message"]
