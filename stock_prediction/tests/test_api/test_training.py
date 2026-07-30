"""
tests/test_api/test_training.py — Test endpoint "Random Search Skripsi-Scoped"
(notebook 07, Batasan Masalah BAB I skripsi).
"""

from __future__ import annotations

import json

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
        payload = line[len("data: "):]
        events.append(json.loads(payload))
    return events


# ---------------------------------------------------------------------------
# "Random Search Skripsi-Scoped" (notebook 07, Batasan Masalah BAB I skripsi)
# ---------------------------------------------------------------------------

class TestSkripsiSearchSpaceEndpoint:
    def test_search_space_envelope(self, client):
        resp = client.get("/api/v1/train/skripsi/search-space")
        assert resp.status_code == 200, resp.text

        body = resp.json()
        assert body["success"] is True
        data = body["data"]

        assert data["hidden_size"] == [16, 32, 64, 128]
        assert data["num_layers"] == [1, 2]
        assert data["optimizer"] == ["adam", "rmsprop", "sgd"]
        assert data["activation"] == ["relu", "tanh", "sigmoid"]
        assert data["epochs"] == [30, 50, 80]
        assert data["batch_size"] == [16, 32, 64]
        assert data["n_iter"] == 20
        assert data["window"] == 10


def _assert_skripsi_done_event(done_event: dict, artifact_substr: str) -> None:
    assert set(done_event["metrics"].keys()) == {"accuracy", "precision", "recall", "f1"}
    assert "confusion_matrix" in done_event
    assert set(done_event["confusion_matrix"].keys()) == {"tn", "fp", "fn", "tp"}
    assert "best_config" in done_event
    assert "best_val_f1" in done_event
    assert "artifact_paths" in done_event
    artifact_paths = done_event["artifact_paths"]
    assert set(artifact_paths.keys()) == {"model", "scaler", "metadata"}
    for path in artifact_paths.values():
        assert artifact_substr in path


class TestTrainSkripsiBaselineStream:
    def test_train_stream_n_iter_1(self, client):
        """POST dengan n_iter=1 (satu-satunya override yang diizinkan — search
        space & window tetap sesuai Batasan Masalah BAB I) — cek event nested
        start/iteration_start/epoch/iteration_end/done lengkap."""
        with client.stream(
            "POST",
            "/api/v1/train/skripsi/ohlcv",
            json={"n_iter": 1},
        ) as resp:
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")
            events = _parse_sse_events(resp.iter_lines())

        types = [e["type"] for e in events]
        assert "start" in types
        assert types.count("iteration_start") == 1
        assert types.count("epoch") >= 1
        assert types.count("iteration_end") == 1
        assert "done" in types
        assert "error" not in types, f"Training gagal: {events}"

        start_event = next(e for e in events if e["type"] == "start")
        assert start_event["total_iterations"] == 1
        assert start_event["window"] == 10
        assert start_event["feature_cols"] == ["Open", "High", "Low", "Close", "Volume"]
        assert "preprocessing" in start_event
        assert "capping_bounds" in start_event["preprocessing"]

        done_event = next(e for e in events if e["type"] == "done")
        _assert_skripsi_done_event(done_event, "lstm_baseline_skripsi")


class TestTrainSkripsiFinbertStream:
    def test_train_stream_n_iter_1(self, client):
        """Varian Model B (FinBERT-LSTM, 6 fitur) — artefak terisolasi beda
        dari Model A (prefix finbert_lstm_skripsi, bukan lstm_baseline_skripsi)."""
        with client.stream(
            "POST",
            "/api/v1/train/skripsi/finbert-lstm",
            json={"n_iter": 1},
        ) as resp:
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")
            events = _parse_sse_events(resp.iter_lines())

        types = [e["type"] for e in events]
        assert "start" in types
        assert types.count("iteration_start") == 1
        assert types.count("iteration_end") == 1
        assert "done" in types
        assert "error" not in types, f"Training gagal: {events}"

        start_event = next(e for e in events if e["type"] == "start")
        assert start_event["feature_cols"] == ["Open", "High", "Low", "Close", "Volume", "sentiment_mean"]
        assert set(start_event["preprocessing"]["capping_bounds"].keys()) == {"Volume", "sentiment_mean"}

        done_event = next(e for e in events if e["type"] == "done")
        _assert_skripsi_done_event(done_event, "finbert_lstm_skripsi")


# ---------------------------------------------------------------------------
# Training Manual (1-konfigurasi fixed, BUKAN Random Search) — dipakai fitur
# "Training Manual" & "Retrain dengan Best Config" FE.
# ---------------------------------------------------------------------------

_MANUAL_CONFIG = {
    "hidden_size": 16,
    "num_layers": 1,
    "dropout": 0.3,
    "optimizer": "adam",
    "activation": "relu",
    "lr": 0.001,
    "epochs": 1,
    "batch_size": 32,
}


def _assert_manual_done_event(done_event: dict, artifact_substr: str) -> None:
    assert set(done_event["metrics"].keys()) == {"accuracy", "precision", "recall", "f1"}
    assert "confusion_matrix" in done_event
    assert set(done_event["confusion_matrix"].keys()) == {"tn", "fp", "fn", "tp"}
    assert done_event["config"]["hidden_size"] == _MANUAL_CONFIG["hidden_size"]
    assert "final_test_f1" in done_event
    assert "final_test_acc" in done_event
    assert "artifact_paths" in done_event
    artifact_paths = done_event["artifact_paths"]
    assert set(artifact_paths.keys()) == {"model", "scaler", "metadata"}
    for path in artifact_paths.values():
        assert artifact_substr in path


class TestTrainSkripsiBaselineManualStream:
    def test_train_manual_stream_flat_events(self, client):
        """Event SSE flat (start/epoch/done) — TIDAK ada iteration_start/
        iteration_end (beda dari Random Search)."""
        with client.stream(
            "POST",
            "/api/v1/train/skripsi/ohlcv/manual",
            json=_MANUAL_CONFIG,
        ) as resp:
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")
            events = _parse_sse_events(resp.iter_lines())

        types = [e["type"] for e in events]
        assert types.count("start") == 1
        assert "iteration_start" not in types
        assert "iteration_end" not in types
        assert types.count("epoch") == _MANUAL_CONFIG["epochs"]
        assert "done" in types
        assert "error" not in types, f"Training gagal: {events}"

        start_event = next(e for e in events if e["type"] == "start")
        assert start_event["window"] == 10
        assert start_event["config"] == _MANUAL_CONFIG
        assert start_event["feature_cols"] == ["Open", "High", "Low", "Close", "Volume"]

        done_event = next(e for e in events if e["type"] == "done")
        _assert_manual_done_event(done_event, "lstm_baseline_skripsi")


class TestTrainSkripsiFinbertManualStream:
    def test_train_manual_stream_flat_events(self, client):
        with client.stream(
            "POST",
            "/api/v1/train/skripsi/finbert-lstm/manual",
            json=_MANUAL_CONFIG,
        ) as resp:
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")
            events = _parse_sse_events(resp.iter_lines())

        types = [e["type"] for e in events]
        assert types.count("start") == 1
        assert "iteration_start" not in types
        assert types.count("epoch") == _MANUAL_CONFIG["epochs"]
        assert "done" in types
        assert "error" not in types, f"Training gagal: {events}"

        start_event = next(e for e in events if e["type"] == "start")
        assert start_event["feature_cols"] == ["Open", "High", "Low", "Close", "Volume", "sentiment_mean"]

        done_event = next(e for e in events if e["type"] == "done")
        _assert_manual_done_event(done_event, "finbert_lstm_skripsi")


# ---------------------------------------------------------------------------
# Halaman Prediction — GET .../result, POST .../predict, GET .../backtest
# untuk model Random Search skripsi-scoped (Model A: baseline, Model B: finbert).
# Artefak SUDAH ADA di disk dari training sesi sebelumnya — tidak training ulang.
# ---------------------------------------------------------------------------

class TestNotebook07ResultEndpoint:
    def test_result_baseline_is_available(self, client):
        resp = client.get("/api/v1/train/skripsi/ohlcv/result")
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["is_available"] is True
        assert data["feature_cols"] == ["Open", "High", "Low", "Close", "Volume"]
        assert data["window"] == 10
        assert set(data["metrics"].keys()) == {"accuracy", "precision", "recall", "f1"}

    def test_result_finbert_is_available(self, client):
        resp = client.get("/api/v1/train/skripsi/finbert-lstm/result")
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["is_available"] is True
        assert "sentiment_mean" in data["feature_cols"]
        assert set(data["metrics"].keys()) == {"accuracy", "precision", "recall", "f1"}


class TestNotebook07PredictEndpoint:
    def test_predict_baseline(self, client):
        resp = client.post("/api/v1/train/skripsi/ohlcv/predict")
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["variant"] == "baseline"
        assert data["direction"] in ("up", "down")
        assert 0.0 <= data["probability_up"] <= 1.0
        assert 0.0 <= data["confidence"] <= 1.0
        assert "sentiment_mean" not in data["feature_cols"]

    def test_predict_finbert(self, client):
        resp = client.post("/api/v1/train/skripsi/finbert-lstm/predict")
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["variant"] == "finbert"
        assert data["direction"] in ("up", "down")
        assert "sentiment_mean" in data["feature_cols"]


class TestNotebook07BacktestEndpoint:
    def test_backtest_baseline(self, client):
        resp = client.get("/api/v1/train/skripsi/ohlcv/backtest", params={"split": "test"})
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["variant"] == "baseline"
        assert data["split"] == "test"
        assert data["n_samples"] == len(data["points"])
        assert set(data["metrics"].keys()) == {"accuracy", "precision", "recall", "f1"}
        assert set(data["confusion_matrix"].keys()) == {"tp", "tn", "fp", "fn"}
        if data["points"]:
            point = data["points"][0]
            assert set(point.keys()) == {
                "date", "close", "actual_direction", "predicted_direction",
                "probability_up", "correct",
            }

    def test_backtest_finbert(self, client):
        resp = client.get("/api/v1/train/skripsi/finbert-lstm/backtest", params={"split": "test"})
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["variant"] == "finbert"
        assert data["n_samples"] == len(data["points"])
