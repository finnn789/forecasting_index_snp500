"""models/lstm/notebook05_common.py — Logic training SHARED untuk kedua varian
"API Training Live Notebook 05":

    - Varian OHLCV + sentiment_mean (metodologi notebook 05 asli)
    - Varian OHLCV-only (ablation study — mengukur kontribusi sentiment_mean)

Satu-satunya salinan windowing/scaler/training-loop/diagnosis — kedua varian
memanggil `run_notebook05_training()` dengan parameter berbeda (feature_cols,
loader data, nama artefak). Perbedaan VARIAN ditentukan di
`app/services/training_service.py`, bukan di modul ini.

PENTING — isolasi dari produksi:
    - Pakai `LSTMSoftmaxClassifier` (2-class softmax), BUKAN `LSTMDirectionClassifier`.
    - Split KRONOLOGIS PERSENTASE 70/15/15 (BEDA dari `build_dataset()` produksi
      yang split by-date).
    - Artefak disimpan ke file terpisah berprefix `lstm_nb05_*` — TIDAK
      menimpa `direction_classifier.pt` / `scaler.joblib` / `metadata.json`.

Model ini diketahui KOLAPS KELAS ("selalu menebak Up") pada varian sentimen
— sesuai temuan notebook 05. Trainer WAJIB menghitung & mengembalikan
diagnosis class-collapse apa adanya (jujur), bukan hanya F2-score yang
menyesatkan.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    fbeta_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import MinMaxScaler
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader, TensorDataset

from models.lstm.lstm_model import LSTMSoftmaxClassifier

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_sequences(
    X: np.ndarray, y: np.ndarray, seq_len: int
) -> tuple[np.ndarray, np.ndarray]:
    """Windowing per-split.

    X_seq[i] = X[i-seq_len:i], y_seq[i] = y[i], untuk i in range(seq_len, len(X)).
    """
    n = len(X)
    if n <= seq_len:
        return (
            np.empty((0, seq_len, X.shape[1]), dtype=np.float32),
            np.empty((0,), dtype=np.int64),
        )
    X_seq = np.stack([X[i - seq_len : i] for i in range(seq_len, n)]).astype(np.float32)
    y_seq = y[seq_len:n].astype(np.int64)
    return X_seq, y_seq


def compute_class_weights(y_train: np.ndarray, device: torch.device) -> torch.Tensor:
    """Inverse-frequency class weights."""
    counts = np.bincount(y_train.astype(np.int64), minlength=2)
    w = 1.0 / (counts + 1e-9)
    w = w / w.sum() * len(counts)
    return torch.tensor(w, dtype=torch.float32, device=device)


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float]:
    """Satu epoch training. Return (loss rata-rata, accuracy)."""
    model.train()
    total_loss = 0.0
    n_samples = 0
    y_true_all: list[int] = []
    y_pred_all: list[int] = []

    for X_batch, y_batch in loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)

        optimizer.zero_grad()
        logits = model(X_batch)
        loss = criterion(logits, y_batch)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        bs = X_batch.size(0)
        total_loss += loss.item() * bs
        n_samples += bs

        preds = logits.argmax(dim=1).detach().cpu().numpy()
        y_true_all.extend(y_batch.detach().cpu().numpy().tolist())
        y_pred_all.extend(preds.tolist())

    avg_loss = total_loss / n_samples if n_samples else 0.0
    acc = accuracy_score(y_true_all, y_pred_all) if n_samples else 0.0
    return avg_loss, float(acc)


def evaluate_loader(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float, float, np.ndarray, np.ndarray]:
    """Evaluasi model pada sebuah DataLoader (no_grad).

    Return (loss, f2, acc, y_true, y_pred).
    """
    model.eval()
    total_loss = 0.0
    n_samples = 0
    y_true_all: list[int] = []
    y_pred_all: list[int] = []

    with torch.no_grad():
        for X_batch, y_batch in loader:
            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)

            logits = model(X_batch)
            loss = criterion(logits, y_batch)

            bs = X_batch.size(0)
            total_loss += loss.item() * bs
            n_samples += bs

            preds = logits.argmax(dim=1).cpu().numpy()
            y_true_all.extend(y_batch.cpu().numpy().tolist())
            y_pred_all.extend(preds.tolist())

    y_true = np.array(y_true_all, dtype=np.int64)
    y_pred = np.array(y_pred_all, dtype=np.int64)

    avg_loss = total_loss / n_samples if n_samples else 0.0
    f2 = fbeta_score(y_true, y_pred, beta=2, zero_division=0) if n_samples else 0.0
    acc = accuracy_score(y_true, y_pred) if n_samples else 0.0
    return avg_loss, float(f2), float(acc), y_true, y_pred


def _split_recalls(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[bool, dict[str, float]]:
    """Hitung recall_down/recall_up dari confusion matrix split, deteksi collapse."""
    if len(y_true) == 0:
        return False, {"recall_down": 0.0, "recall_up": 0.0}
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    recall_down = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    recall_up = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    collapse = bool(recall_down <= 0.05 or recall_up <= 0.05)
    return collapse, {"recall_down": float(recall_down), "recall_up": float(recall_up)}


def _r6(x: float) -> float:
    """Round wajar & aman untuk JSON (cast dari numpy)."""
    return round(float(x), 6)


def _load_and_split(
    load_data_fn: Callable[[], pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load data + label + split KRONOLOGIS PERSENTASE 70/15/15.

    Diekstrak dari `run_notebook05_training()` supaya bisa dipakai ulang oleh
    `backtest_notebook05()` — logic split TIDAK diduplikasi.
    """
    df = load_data_fn()
    df["target"] = (df["Close"].shift(-1) > df["Close"]).astype("int64")
    df = df.iloc[:-1].copy().reset_index(drop=True)

    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    df_train = df.iloc[:train_end].reset_index(drop=True)
    df_val = df.iloc[train_end:val_end].reset_index(drop=True)
    df_test = df.iloc[val_end:].reset_index(drop=True)
    return df_train, df_val, df_test


# ---------------------------------------------------------------------------
# run_notebook05_training — dipakai bersama oleh kedua varian
# ---------------------------------------------------------------------------

def run_notebook05_training(
    *,
    config: dict,
    emit: Callable[[dict], None],
    feature_cols: list[str],
    load_data_fn: Callable[[], pd.DataFrame],
    default_config: dict[str, Any],
    artifact_dir: str,
    model_filename: str,
    scaler_filename: str,
    metadata_filename: str,
) -> dict:
    """Jalankan training final `LSTMSoftmaxClassifier` (metodologi notebook 05),
    digeneralisasi lewat `feature_cols`/`load_data_fn`/nama artefak supaya bisa
    dipakai baik varian OHLCV+sentiment_mean maupun varian OHLCV-only (ablation).

    Meng-emit event SSE via `emit()`: "start" -> "epoch" (tiap epoch) ->
    "done" (atau "error" bila gagal). Return dict payload event "done"
    (tanpa key "type") untuk kebutuhan pemanggilan non-SSE (mis. smoke test).
    """
    try:
        cfg = {**default_config, **{k: v for k, v in config.items() if v is not None}}
        seq_len: int = int(cfg["seq_len"])
        hidden_size: int = int(cfg["hidden_size"])
        num_layers: int = int(cfg["num_layers"])
        dropout: float = float(cfg["dropout"])
        lr: float = float(cfg["lr"])
        batch_size: int = int(cfg["batch_size"])
        epochs: int = int(cfg["epochs"])
        early_stop: int = int(cfg["early_stop"])

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # -------------------------------------------------------------
        # 1-2. Load data + label + split KRONOLOGIS PERSENTASE 70/15/15
        # -------------------------------------------------------------
        df_train, df_val, df_test = _load_and_split(load_data_fn)

        # -------------------------------------------------------------
        # 3. MinMaxScaler — fit HANYA di train (anti-leakage)
        # -------------------------------------------------------------
        scaler = MinMaxScaler()
        X_train_raw = scaler.fit_transform(df_train[feature_cols].values.astype(np.float64))
        X_val_raw = scaler.transform(df_val[feature_cols].values.astype(np.float64))
        X_test_raw = scaler.transform(df_test[feature_cols].values.astype(np.float64))

        y_train_raw = df_train["target"].values.astype(np.int64)
        y_val_raw = df_val["target"].values.astype(np.int64)
        y_test_raw = df_test["target"].values.astype(np.int64)

        # -------------------------------------------------------------
        # 4. Windowing per-split
        # -------------------------------------------------------------
        X_train, y_train = create_sequences(X_train_raw, y_train_raw, seq_len)
        X_val, y_val = create_sequences(X_val_raw, y_val_raw, seq_len)
        X_test, y_test = create_sequences(X_test_raw, y_test_raw, seq_len)

        # -------------------------------------------------------------
        # 5. DataLoader
        # -------------------------------------------------------------
        def _loader(X: np.ndarray, y: np.ndarray, shuffle: bool, drop_last: bool) -> DataLoader:
            ds = TensorDataset(torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.int64))
            return DataLoader(ds, batch_size=batch_size, shuffle=shuffle, drop_last=drop_last)

        train_loader = _loader(X_train, y_train, shuffle=False, drop_last=True)
        val_loader = _loader(X_val, y_val, shuffle=False, drop_last=False)
        test_loader = _loader(X_test, y_test, shuffle=False, drop_last=False)

        emit({
            "type": "start",
            "total_epochs": epochs,
            "config": {
                "seq_len": seq_len,
                "hidden_size": hidden_size,
                "num_layers": num_layers,
                "dropout": dropout,
                "lr": lr,
                "batch_size": batch_size,
                "epochs": epochs,
                "early_stop": early_stop,
            },
            "device": device.type,
            "split": {
                "train_rows": len(df_train),
                "val_rows": len(df_val),
                "test_rows": len(df_test),
                "train_samples": len(X_train),
                "val_samples": len(X_val),
                "test_samples": len(X_test),
            },
        })

        # -------------------------------------------------------------
        # 6. Model, optimizer, loss, scheduler
        # -------------------------------------------------------------
        model = LSTMSoftmaxClassifier(
            input_size=len(feature_cols),
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            num_classes=2,
        ).to(device)

        class_w = compute_class_weights(y_train, device)
        criterion = nn.CrossEntropyLoss(weight=class_w)
        optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
        scheduler = ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=7, min_lr=1e-6)

        # -------------------------------------------------------------
        # 7. Training loop
        # -------------------------------------------------------------
        history: dict[str, list[float]] = {
            "train_loss": [], "train_f2": [], "train_acc": [],
            "val_loss": [], "val_f2": [], "val_acc": [],
        }
        best_val_f2 = -1.0
        best_state: dict[str, Any] | None = None
        best_epoch_1based = 0
        patience_cnt = 0

        for epoch in range(1, epochs + 1):
            train_loss, train_acc = train_one_epoch(model, train_loader, optimizer, criterion, device)
            # Metrik train (f2) dihitung lewat evaluate_loader agar konsisten
            # dgn definisi f2/acc (train_one_epoch hanya kembalikan loss & acc kasar).
            _, train_f2, _, _, _ = evaluate_loader(model, train_loader, criterion, device)
            val_loss, val_f2, val_acc, _, _ = evaluate_loader(model, val_loader, criterion, device)

            scheduler.step(val_f2)

            history["train_loss"].append(train_loss)
            history["train_f2"].append(train_f2)
            history["train_acc"].append(train_acc)
            history["val_loss"].append(val_loss)
            history["val_f2"].append(val_f2)
            history["val_acc"].append(val_acc)

            if val_f2 > best_val_f2:
                best_val_f2 = val_f2
                best_state = deepcopy({k: v.detach().cpu().clone() for k, v in model.state_dict().items()})
                best_epoch_1based = epoch
                patience_cnt = 0
            else:
                patience_cnt += 1

            emit({
                "type": "epoch",
                "epoch": epoch,
                "total_epochs": epochs,
                "train_loss": _r6(train_loss),
                "train_f2": _r6(train_f2),
                "train_acc": _r6(train_acc),
                "val_loss": _r6(val_loss),
                "val_f2": _r6(val_f2),
                "val_acc": _r6(val_acc),
            })

            if patience_cnt >= early_stop:
                break

        assert best_state is not None, "Training loop tidak menghasilkan best_state"
        model.load_state_dict(best_state)
        model.eval()

        # -------------------------------------------------------------
        # 8. Evaluasi final di TEST
        # -------------------------------------------------------------
        _, test_f2, test_acc, y_test_true, y_test_pred = evaluate_loader(model, test_loader, criterion, device)
        test_precision = precision_score(y_test_true, y_test_pred, zero_division=0)
        test_recall = recall_score(y_test_true, y_test_pred, zero_division=0)
        test_f1 = f1_score(y_test_true, y_test_pred, zero_division=0)

        tn, fp, fn, tp = confusion_matrix(y_test_true, y_test_pred, labels=[0, 1]).ravel()

        # -------------------------------------------------------------
        # 9. Diagnosis (replikasi persis notebook)
        # -------------------------------------------------------------
        best_epoch_idx = int(np.argmax(history["val_f2"]))
        best_train_f2 = history["train_f2"][best_epoch_idx]
        best_val_f2_hist = history["val_f2"][best_epoch_idx]

        overfitting = bool((best_train_f2 - test_f2) > 0.10)
        underfitting = bool(best_train_f2 < 0.55 and best_val_f2_hist < 0.55)
        if overfitting:
            fit_status = "OVERFITTING"
        elif underfitting:
            fit_status = "UNDERFITTING"
        else:
            fit_status = "GOOD_FIT"

        # class_collapse per split — train & val dievaluasi ulang di best model
        _, _, _, y_train_true, y_train_pred = evaluate_loader(model, train_loader, criterion, device)
        _, _, _, y_val_true, y_val_pred = evaluate_loader(model, val_loader, criterion, device)

        collapse_train, _ = _split_recalls(y_train_true, y_train_pred)
        collapse_val, _ = _split_recalls(y_val_true, y_val_pred)
        collapse_test, _ = _split_recalls(y_test_true, y_test_pred)
        any_collapse = bool(collapse_train or collapse_val or collapse_test)

        diagnosis = {
            "overfitting": overfitting,
            "underfitting": underfitting,
            "fit_status": fit_status,
            "class_collapse": {
                "train": collapse_train,
                "val": collapse_val,
                "test": collapse_test,
            },
            "any_collapse": any_collapse,
        }

        metrics = {
            "accuracy": _r6(test_acc),
            "precision": _r6(test_precision),
            "recall": _r6(test_recall),
            "f1": _r6(test_f1),
            "f2": _r6(test_f2),
        }
        confusion = {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}

        # -------------------------------------------------------------
        # 10. Simpan artefak TERISOLASI (lstm_nb05_*)
        # -------------------------------------------------------------
        artifact_path_dir = Path(artifact_dir)
        artifact_path_dir.mkdir(parents=True, exist_ok=True)

        model_path = artifact_path_dir / model_filename
        scaler_path = artifact_path_dir / scaler_filename
        metadata_path = artifact_path_dir / metadata_filename

        torch.save(
            {
                "model_state_dict": best_state,
                "config": cfg,
                "feature_cols": feature_cols,
                "best_val_f2": _r6(best_val_f2),
            },
            model_path,
        )
        joblib.dump(scaler, scaler_path)

        trained_at = datetime.now(timezone.utc).isoformat()
        metadata = {
            "config": cfg,
            "feature_cols": feature_cols,
            "metrics": metrics,
            "confusion_matrix": confusion,
            "diagnosis": diagnosis,
            "split_sizes": {
                "train_rows": len(df_train),
                "val_rows": len(df_val),
                "test_rows": len(df_test),
                "train_samples": len(X_train),
                "val_samples": len(X_val),
                "test_samples": len(X_test),
            },
            "trained_at": trained_at,
            "best_epoch": best_epoch_1based,
            "best_val_f2": _r6(best_val_f2),
        }
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        artifact_paths = {
            "model": str(model_path),
            "scaler": str(scaler_path),
            "metadata": str(metadata_path),
        }

        done_payload = {
            "type": "done",
            "best_val_f2": _r6(best_val_f2),
            "best_epoch": best_epoch_1based,
            "metrics": metrics,
            "confusion_matrix": confusion,
            "diagnosis": diagnosis,
            "artifact_paths": artifact_paths,
        }
        emit(done_payload)
        return done_payload

    except Exception as e:  # noqa: BLE001 — training final, wajib emit error apa adanya
        error_payload = {"type": "error", "message": str(e)}
        emit(error_payload)
        return error_payload


# ---------------------------------------------------------------------------
# Inference & backtest — dipakai halaman Prediction (hasil training persisted,
# bukan cuma hidup di React state). Reuse artefak yang disimpan
# run_notebook05_training() di atas (lstm_nb05_*/lstm_nb05_ohlcv_*).
# ---------------------------------------------------------------------------

def load_trained_notebook05(
    *,
    artifact_dir: str,
    model_filename: str,
    scaler_filename: str,
    metadata_filename: str,
) -> dict[str, Any] | None:
    """Rekonstruksi `LSTMSoftmaxClassifier` (eval mode) + scaler + metadata dari
    artefak tersimpan. Return `None` kalau belum pernah training (artefak belum
    lengkap) — caller (predict/backtest) wajib menangani kasus ini apa adanya,
    BUKAN raise di sini (fungsi ini murni loader)."""
    artifact_path_dir = Path(artifact_dir)
    model_path = artifact_path_dir / model_filename
    scaler_path = artifact_path_dir / scaler_filename
    metadata_path = artifact_path_dir / metadata_filename

    if not (model_path.exists() and scaler_path.exists() and metadata_path.exists()):
        return None

    checkpoint = torch.load(model_path, map_location="cpu")
    cfg = checkpoint["config"]
    feature_cols = checkpoint["feature_cols"]

    model = LSTMSoftmaxClassifier(
        input_size=len(feature_cols),
        hidden_size=int(cfg["hidden_size"]),
        num_layers=int(cfg["num_layers"]),
        dropout=float(cfg["dropout"]),
        num_classes=2,
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    scaler = joblib.load(scaler_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    return {
        "model": model,
        "scaler": scaler,
        "metadata": metadata,
        "feature_cols": feature_cols,
        "config": cfg,
    }


def predict_latest_notebook05(
    *,
    feature_cols: list[str],
    load_data_fn: Callable[[], pd.DataFrame],
    artifact_dir: str,
    model_filename: str,
    scaler_filename: str,
    metadata_filename: str,
) -> dict[str, Any]:
    """Prediksi arah harga hari berikutnya dari window TERAKHIR data, pakai
    model terlatih (persisted). Return `{"trained": False}` kalau belum pernah
    training — caller (service layer) yang memutuskan raise/response apa."""
    loaded = load_trained_notebook05(
        artifact_dir=artifact_dir,
        model_filename=model_filename,
        scaler_filename=scaler_filename,
        metadata_filename=metadata_filename,
    )
    if loaded is None:
        return {"trained": False}

    from pipeline.feature_engineering.dataset_builder import build_latest_window  # noqa: PLC0415

    seq_len = int(loaded["config"]["seq_len"])
    X, as_of_str = build_latest_window(
        window=seq_len,
        scaler=loaded["scaler"],
        feature_cols=feature_cols,
        load_data_fn=load_data_fn,
    )
    target_str = (pd.Timestamp(as_of_str) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    model = loaded["model"]
    with torch.no_grad():
        logits = model(torch.tensor(X, dtype=torch.float32))
        probs = torch.softmax(logits, dim=1).numpy()[0]

    p_up = float(probs[1])
    direction = "up" if p_up >= 0.5 else "down"
    confidence = max(p_up, 1.0 - p_up)

    return {
        "trained": True,
        "as_of_date": as_of_str,
        "target_date": target_str,
        "direction": direction,
        "probability_up": _r6(p_up),
        "confidence": _r6(confidence),
        "window": seq_len,
        "feature_cols": feature_cols,
        "trained_at": loaded["metadata"].get("trained_at"),
        "best_val_f2": loaded["metadata"].get("best_val_f2"),
    }


def backtest_notebook05(
    *,
    feature_cols: list[str],
    load_data_fn: Callable[[], pd.DataFrame],
    artifact_dir: str,
    model_filename: str,
    scaler_filename: str,
    metadata_filename: str,
    split: str = "test",
) -> dict[str, Any]:
    """Jalankan model terlatih di data historis (split kronologis 70/15/15
    yang SAMA seperti training — reuse `_load_and_split()`, scaler TIDAK
    di-fit ulang) dan kembalikan prediksi-vs-aktual per-titik + metrik.
    Return `{"trained": False}` kalau belum pernah training."""
    loaded = load_trained_notebook05(
        artifact_dir=artifact_dir,
        model_filename=model_filename,
        scaler_filename=scaler_filename,
        metadata_filename=metadata_filename,
    )
    if loaded is None:
        return {"trained": False}

    seq_len = int(loaded["config"]["seq_len"])
    scaler = loaded["scaler"]

    df_train, df_val, df_test = _load_and_split(load_data_fn)
    df_split = {"train": df_train, "val": df_val, "test": df_test}[split]

    X_raw = scaler.transform(df_split[feature_cols].values.astype(np.float64))
    y_raw = df_split["target"].values.astype(np.int64)
    X_seq, y_seq = create_sequences(X_raw, y_raw, seq_len)

    dates = df_split["Date"].iloc[seq_len:].dt.strftime("%Y-%m-%d").tolist()
    closes = df_split["Close"].iloc[seq_len:].tolist()

    model = loaded["model"]
    with torch.no_grad():
        logits = model(torch.tensor(X_seq, dtype=torch.float32))
        probs = torch.softmax(logits, dim=1).numpy()[:, 1]

    y_int = y_seq.astype(int)
    pred_int = (probs >= 0.5).astype(int)

    points = [
        {
            "date": dates[i],
            "close": float(closes[i]),
            "actual_direction": "up" if y_int[i] == 1 else "down",
            "predicted_direction": "up" if pred_int[i] == 1 else "down",
            "probability_up": _r6(probs[i]),
            "correct": bool(pred_int[i] == y_int[i]),
        }
        for i in range(len(dates))
    ]

    try:
        auc = float(roc_auc_score(y_int, probs))
    except ValueError:
        auc = float("nan")

    metrics = {
        "accuracy": _r6(accuracy_score(y_int, pred_int)),
        "precision": _r6(precision_score(y_int, pred_int, zero_division=0)),
        "recall": _r6(recall_score(y_int, pred_int, zero_division=0)),
        "f1": _r6(f1_score(y_int, pred_int, zero_division=0)),
        "auc": _r6(auc) if auc == auc else auc,  # NaN-safe (auc != auc kalau NaN)
    }

    tn, fp, fn, tp = confusion_matrix(y_int, pred_int, labels=[0, 1]).ravel()

    return {
        "trained": True,
        "window": seq_len,
        "split": split,
        "n_samples": len(points),
        "metrics": metrics,
        "confusion_matrix": {"tp": int(tp), "tn": int(tn), "fp": int(fp), "fn": int(fn)},
        "points": points,
    }
