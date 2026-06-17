"""LSTM Direction Predictor — load artefak dan lakukan inferensi.

Load pada __init__:
    metadata.json   -> konfigurasi arsitektur + feature_cols + window
    direction_classifier.pt -> state_dict
    scaler.joblib   -> MinMaxScaler (untuk build_latest_window)

predict_latest() memanggil pipeline.feature_engineering.dataset_builder.build_latest_window
untuk mendapat window terbaru dari data historis, lalu mengembalikan probabilitas arah.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import joblib
import numpy as np
import torch

from models.lstm.lstm_model import build_classifier

if TYPE_CHECKING:
    pass  # tipe untuk type checker saja


class DirectionPredictor:
    """Load artefak LSTM dan menyediakan antarmuka inferensi.

    Args:
        artifact_dir: Path ke direktori artefak (berisi .pt, .joblib, .json).
    """

    def __init__(self, artifact_dir: str = "data/artifacts/lstm_weights") -> None:
        self._artifact_dir = Path(artifact_dir)
        self._model: torch.nn.Module | None = None
        self._scaler = None
        self._metadata: dict | None = None
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self._load_artifacts()

    # ------------------------------------------------------------------
    # Internal loading
    # ------------------------------------------------------------------

    def _load_artifacts(self) -> None:
        """Coba load semua artefak. Jika tidak ada, set ke None (is_available=False)."""
        meta_path = self._artifact_dir / "metadata.json"
        model_path = self._artifact_dir / "direction_classifier.pt"
        scaler_path = self._artifact_dir / "scaler.joblib"

        if not (meta_path.exists() and model_path.exists() and scaler_path.exists()):
            # Artefak belum ada — model belum di-train
            return

        # Load metadata
        with open(meta_path, "r", encoding="utf-8") as f:
            self._metadata = json.load(f)

        # Rebuild arsitektur dari metadata lalu load state_dict
        model = build_classifier(
            n_features=self._metadata["n_features"],
            hidden=self._metadata.get("hidden", 64),
            num_layers=self._metadata.get("num_layers", 2),
            dropout=self._metadata.get("dropout", 0.3),
        )
        state_dict = torch.load(
            model_path,
            map_location=self._device,
            weights_only=True,
        )
        model.load_state_dict(state_dict)
        model.to(self._device)
        model.eval()
        self._model = model

        # Load scaler
        self._scaler = joblib.load(scaler_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_available(self) -> bool:
        """True jika semua artefak berhasil di-load."""
        return self._model is not None and self._scaler is not None and self._metadata is not None

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Hitung probabilitas arah naik dari array fitur yang sudah di-scale.

        Args:
            X: Input array shape (B, W, F) float32 — sudah di-transform oleh scaler.

        Returns:
            probs: Array shape (B,) float64, nilai di [0, 1].

        Raises:
            RuntimeError: Jika model belum tersedia (artefak tidak ditemukan).
        """
        if not self.is_available:
            raise RuntimeError(
                "Model belum tersedia. Jalankan train() terlebih dahulu untuk menghasilkan artefak."
            )

        with torch.no_grad():
            X_t = torch.tensor(X, dtype=torch.float32).to(self._device)
            logits = self._model(X_t).cpu().numpy()  # type: ignore[union-attr]

        # Sigmoid manual (numpy) agar tidak perlu torch pada output
        probs = 1.0 / (1.0 + np.exp(-logits))
        return probs

    def predict_latest(self) -> dict:
        """Prediksi arah harga untuk hari bursa berikutnya menggunakan data terbaru.

        Memanggil `pipeline.feature_engineering.dataset_builder.build_latest_window`
        untuk mendapatkan window terbaru dari CSV historis, lalu menghitung probabilitas.

        Returns:
            dict dengan field:
                probability_up (float): probabilitas harga naik, di [0,1].
                direction (str): 'up' jika probability_up >= 0.5 else 'down'.
                confidence (float): max(p, 1-p), di [0.5, 1].
                as_of_date (str): tanggal data terakhir (ISO string).
                target_date (str): tanggal prediksi (hari bursa berikutnya).

        Raises:
            RuntimeError: Jika model belum tersedia.
            ImportError: Jika dataset_builder belum tersedia.
        """
        if not self.is_available:
            raise RuntimeError(
                "Model belum tersedia. Jalankan train() terlebih dahulu untuk menghasilkan artefak."
            )

        # Import di sini agar ImportError tidak meledak saat module di-load
        # (dataset_builder mungkin belum ada saat unit test lstm_model)
        from pipeline.feature_engineering.dataset_builder import build_latest_window  # noqa: PLC0415

        window: int = self._metadata["window"]  # type: ignore[index]
        X, as_of_date = build_latest_window(window=window, scaler=self._scaler)
        # X shape: (1, W, F)

        probs = self.predict_proba(X)
        p = float(probs[0])

        direction = "up" if p >= 0.5 else "down"
        confidence = max(p, 1.0 - p)

        # target_date: hari kalender berikutnya setelah as_of_date
        # (build_latest_window sudah menghitung ini, tapi kita hitung ulang
        #  sebagai fallback sederhana)
        from datetime import date, timedelta  # noqa: PLC0415

        try:
            as_of = date.fromisoformat(as_of_date)
            target_date = (as_of + timedelta(days=1)).isoformat()
        except ValueError:
            target_date = as_of_date  # fallback

        return {
            "probability_up": round(p, 6),
            "direction": direction,
            "confidence": round(confidence, 6),
            "as_of_date": as_of_date,
            "target_date": target_date,
        }
