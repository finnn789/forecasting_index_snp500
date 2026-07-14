"""models/lstm/notebook05_trainer.py — Konstanta TERISOLASI untuk varian
training "OHLCV + sentiment_mean" (fitur

"API Training Live Notebook 05").

Mereplikasi PERSIS metodologi notebook 05 (grid-search 144 kombinasi,
sudah diverifikasi — TIDAK dijalankan ulang di sini, lihat GRID_SEARCH_RESULT
di bawah).

Logic training aktual (windowing, scaler, training loop, diagnosis) ada di
`models/lstm/notebook05_common.py::run_notebook05_training()` — SHARED dengan
varian OHLCV-only (ablation). Modul ini hanya menyimpan konstanta khusus
varian OHLCV+sentiment_mean: default hyperparameter, hasil grid-search statis,
dan nama file artefak. Lihat `app/services/training_service.py` untuk
pemilihan varian (di situlah `run_notebook05_training()` benar-benar
dipanggil dengan parameter feature_cols/loader yang sesuai).

PENTING — isolasi dari produksi: artefak disimpan ke file terpisah berprefix
`lstm_nb05_*` — TIDAK menimpa `direction_classifier.pt` / `scaler.joblib` /
`metadata.json`.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------------

ARTIFACT_DIR = "data/artifacts/lstm_weights"
MODEL_FILENAME = "lstm_nb05_best.pt"
SCALER_FILENAME = "lstm_nb05_scaler.joblib"
METADATA_FILENAME = "lstm_nb05_metadata.json"

# Best config hasil grid-search 144 kombinasi (notebook 05, §1.3).
DEFAULT_CONFIG: dict[str, Any] = {
    "seq_len": 20,
    "hidden_size": 64,
    "num_layers": 2,
    "dropout": 0.4,
    "lr": 0.0005,
    "batch_size": 64,
    "epochs": 150,
    "early_stop": 30,
}

# Hasil grid-search STATIS (144 kombinasi) — TIDAK dijalankan ulang.
# top_configs = TOP 10 baris tabel notebook (val_f2 desc); epochs/early_stop
# di sini beda dengan DEFAULT_CONFIG karena baris ini dari FASE grid-search
# (epochs=80/early_stop=20), sedangkan DEFAULT_CONFIG dipakai utk training
# FINAL (epochs=150/early_stop=30). Dibiarkan apa adanya sesuai notebook.
GRID_SEARCH_RESULT: dict[str, Any] = {
    "total_combinations": 144,
    "best_val_f2": 0.811037,
    "best_config": dict(DEFAULT_CONFIG),
    "top_configs": [
        {"seq_len": 20, "hidden_size": 64, "num_layers": 2, "dropout": 0.4, "lr": 0.0005, "batch_size": 64, "epochs": 80, "early_stop": 20, "val_f2": 0.811037},
        {"seq_len": 20, "hidden_size": 128, "num_layers": 1, "dropout": 0.2, "lr": 0.0010, "batch_size": 32, "epochs": 80, "early_stop": 20, "val_f2": 0.808333},
        {"seq_len": 20, "hidden_size": 64, "num_layers": 2, "dropout": 0.4, "lr": 0.0005, "batch_size": 32, "epochs": 80, "early_stop": 20, "val_f2": 0.806988},
        {"seq_len": 20, "hidden_size": 64, "num_layers": 2, "dropout": 0.2, "lr": 0.0010, "batch_size": 32, "epochs": 80, "early_stop": 20, "val_f2": 0.806988},
        {"seq_len": 20, "hidden_size": 64, "num_layers": 1, "dropout": 0.4, "lr": 0.0010, "batch_size": 32, "epochs": 80, "early_stop": 20, "val_f2": 0.806988},
        {"seq_len": 20, "hidden_size": 64, "num_layers": 1, "dropout": 0.4, "lr": 0.0010, "batch_size": 64, "epochs": 80, "early_stop": 20, "val_f2": 0.806988},
        {"seq_len": 20, "hidden_size": 64, "num_layers": 2, "dropout": 0.2, "lr": 0.0005, "batch_size": 32, "epochs": 80, "early_stop": 20, "val_f2": 0.806988},
        {"seq_len": 20, "hidden_size": 64, "num_layers": 1, "dropout": 0.2, "lr": 0.0010, "batch_size": 64, "epochs": 80, "early_stop": 20, "val_f2": 0.806988},
        {"seq_len": 20, "hidden_size": 64, "num_layers": 1, "dropout": 0.2, "lr": 0.0010, "batch_size": 32, "epochs": 80, "early_stop": 20, "val_f2": 0.806988},
        {"seq_len": 20, "hidden_size": 64, "num_layers": 2, "dropout": 0.4, "lr": 0.0010, "batch_size": 32, "epochs": 80, "early_stop": 20, "val_f2": 0.806988},
    ],
}
