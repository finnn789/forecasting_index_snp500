"""models/lstm/notebook07_trainer.py — Konstanta TERISOLASI untuk "Random Search
Skripsi-Scoped" (replikasi live `notebooks/07_LSTM_FinBERT_skripsi_scoped.ipynb`,
Batasan Masalah BAB I skripsi).

Search space, jumlah iterasi, dan window di sini PERSIS sama dengan yang dipakai
di notebook 07 — TIDAK dibuat configurable dari FE, supaya hasil live-training via
API tetap konsisten dengan metodologi yang didokumentasikan di BAB III.

Logic training aktual ada di `models/lstm/notebook07_common.py`. Modul ini hanya
konstanta + nama file artefak per varian.

PENTING — isolasi dari produksi & dari notebook 05: artefak disimpan dengan nama
file SAMA PERSIS dengan yang disimpan notebook 07 sendiri (`lstm_baseline_skripsi.*`
/ `finbert_lstm_skripsi.*`) — supaya training via API atau via notebook saling
kompatibel/interchangeable, TIDAK menimpa `direction_classifier.pt` / `lstm_nb05_*`.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Search space Random Search (persis notebook 07, Bagian 3)
# ---------------------------------------------------------------------------

SEARCH_SPACE: dict[str, Any] = {
    "hidden_size": [16, 32, 64, 128],
    "num_layers": [1, 2],
    "dropout": (0.2, 0.5),          # uniform continuous
    "optimizer": ["adam", "rmsprop", "sgd"],
    "activation": ["relu", "tanh", "sigmoid"],
    "lr": (1e-4, 1e-2),             # log-uniform continuous
    "epochs": [30, 50, 80],
    "batch_size": [16, 32, 64],
}

N_ITER = 20
WINDOW = 30

# ---------------------------------------------------------------------------
# Artefak
# ---------------------------------------------------------------------------

ARTIFACT_DIR = "data/artifacts/lstm_weights"

BASELINE_FILES: dict[str, str] = {
    "model": "lstm_baseline_skripsi.pt",
    "scaler": "lstm_baseline_skripsi_scaler.joblib",
    "metadata": "lstm_baseline_skripsi_metadata.json",
}

FINBERT_FILES: dict[str, str] = {
    "model": "finbert_lstm_skripsi.pt",
    "scaler": "finbert_lstm_skripsi_scaler.joblib",
    "metadata": "finbert_lstm_skripsi_metadata.json",
}
