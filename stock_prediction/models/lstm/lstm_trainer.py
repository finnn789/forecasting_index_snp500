"""LSTM Trainer — melatih LSTMDirectionClassifier dan menyimpan artefak.

Artefak output (ARTIFACT_DIR):
    direction_classifier.pt  — best state_dict (val AUC tertinggi)
    scaler.joblib            — MinMaxScaler hasil fit di train
    metadata.json            — {feature_cols, window, n_features, hidden,
                                metrics, trained_at (ISO UTC), framework}

Strategi training:
    - Loss  : BCEWithLogitsLoss
    - Optim : Adam(lr)
    - Early stopping : monitor val AUC, patience epoch tanpa peningkatan
    - Seed  : reproducibility (torch + numpy)
"""

from __future__ import annotations

import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import joblib
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from torch.utils.data import DataLoader, TensorDataset

from models.lstm.lstm_model import build_classifier

if TYPE_CHECKING:
    from pipeline.feature_engineering.dataset_builder import DatasetBundle

ARTIFACT_DIR = "data/artifacts/lstm_weights"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_seed(seed: int) -> None:
    """Set seed untuk reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _make_loader(X: np.ndarray, y: np.ndarray, batch_size: int, shuffle: bool) -> DataLoader:
    """Buat DataLoader dari numpy array."""
    X_t = torch.tensor(X, dtype=torch.float32)
    y_t = torch.tensor(y, dtype=torch.float32)
    dataset = TensorDataset(X_t, y_t)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)


def _evaluate(
    model: nn.Module,
    X: np.ndarray,
    y: np.ndarray,
    device: torch.device,
) -> dict:
    """Hitung accuracy, f1, auc pada split tertentu (no_grad)."""
    model.eval()
    with torch.no_grad():
        X_t = torch.tensor(X, dtype=torch.float32).to(device)
        logits = model(X_t).cpu().numpy()
    probs = 1.0 / (1.0 + np.exp(-logits))  # sigmoid manual (numpy)
    preds = (probs >= 0.5).astype(int)
    y_int = y.astype(int)
    return {
        "accuracy": float(accuracy_score(y_int, preds)),
        "f1": float(f1_score(y_int, preds, zero_division=0)),
        "auc": float(roc_auc_score(y_int, probs)),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def train(
    bundle: "DatasetBundle",
    epochs: int = 50,
    batch_size: int = 32,
    lr: float = 1e-3,
    patience: int = 8,
    seed: int = 42,
) -> dict:
    """Latih LSTMDirectionClassifier dan simpan artefak.

    Args:
        bundle   : DatasetBundle dari pipeline.feature_engineering.dataset_builder.
        epochs   : Jumlah maksimum epoch.
        batch_size: Ukuran batch untuk DataLoader training.
        lr       : Learning rate Adam.
        patience : Jumlah epoch toleransi early stopping (monitor val AUC).
        seed     : Random seed untuk reproducibility.

    Returns:
        dict berisi {val_acc, val_f1, val_auc, test_acc, test_f1, test_auc}.
    """
    _set_seed(seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    n_features = bundle.X_train.shape[2]
    hidden = 64
    num_layers = 2
    dropout = 0.3

    model = build_classifier(
        n_features=n_features,
        hidden=hidden,
        num_layers=num_layers,
        dropout=dropout,
    ).to(device)

    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    train_loader = _make_loader(bundle.X_train, bundle.y_train, batch_size, shuffle=True)

    # Tensor val sekali saja (dipakai tiap epoch untuk early stopping)
    X_val_t = torch.tensor(bundle.X_val, dtype=torch.float32).to(device)
    y_val_t = torch.tensor(bundle.y_val, dtype=torch.float32).to(device)

    best_val_auc: float = -1.0
    best_state: dict | None = None
    no_improve: int = 0

    for epoch in range(1, epochs + 1):
        # --- Training ---
        model.train()
        for X_batch, y_batch in train_loader:
            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)
            optimizer.zero_grad()
            logits = model(X_batch)
            loss = criterion(logits, y_batch)
            loss.backward()
            optimizer.step()

        # --- Validation AUC untuk early stopping ---
        model.eval()
        with torch.no_grad():
            val_logits = model(X_val_t).cpu().numpy()
        val_probs = 1.0 / (1.0 + np.exp(-val_logits))
        val_auc = float(roc_auc_score(bundle.y_val.astype(int), val_probs))

        if val_auc > best_val_auc:
            best_val_auc = val_auc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            no_improve = 0
        else:
            no_improve += 1

        if no_improve >= patience:
            print(f"Early stopping at epoch {epoch} (best val_auc={best_val_auc:.4f})")
            break

    # Restore best model
    assert best_state is not None, "Training loop tidak menghasilkan best_state"
    model.load_state_dict(best_state)
    model.eval()

    # --- Hitung metrics final ---
    val_metrics = _evaluate(model, bundle.X_val, bundle.y_val, device)
    test_metrics = _evaluate(model, bundle.X_test, bundle.y_test, device)

    metrics = {
        "val_acc": val_metrics["accuracy"],
        "val_f1": val_metrics["f1"],
        "val_auc": val_metrics["auc"],
        "test_acc": test_metrics["accuracy"],
        "test_f1": test_metrics["f1"],
        "test_auc": test_metrics["auc"],
    }

    # --- Simpan artefak ---
    artifact_path = Path(ARTIFACT_DIR)
    artifact_path.mkdir(parents=True, exist_ok=True)

    # 1. Model state_dict
    torch.save(best_state, artifact_path / "direction_classifier.pt")

    # 2. Scaler
    joblib.dump(bundle.scaler, artifact_path / "scaler.joblib")

    # 3. Metadata JSON
    metadata = {
        "feature_cols": bundle.feature_cols,
        "window": bundle.window,
        "n_features": n_features,
        "hidden": hidden,
        "num_layers": num_layers,
        "dropout": dropout,
        "metrics": metrics,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "framework": "pytorch",
    }
    with open(artifact_path / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Artefak disimpan ke: {artifact_path.resolve()}")
    print(f"Val  — acc={val_metrics['accuracy']:.4f} f1={val_metrics['f1']:.4f} auc={val_metrics['auc']:.4f}")
    print(f"Test — acc={test_metrics['accuracy']:.4f} f1={test_metrics['f1']:.4f} auc={test_metrics['auc']:.4f}")

    return metrics
