"""models/lstm/notebook07_common.py — Logic training SHARED untuk "Random Search
Skripsi-Scoped" (replikasi live `notebooks/07_LSTM_FinBERT_skripsi_scoped.ipynb`,
Batasan Masalah BAB I: horizon 1-hari, split kronologis 70/15/15, Random Search
20 iterasi, HANYA 4 metrik evaluasi Accuracy/Precision/Recall/F1).

Satu-satunya salinan capping-outlier/scaler/windowing/Random-Search-loop — kedua
varian (Model A: OHLCV baseline, Model B: FinBERT-LSTM) memanggil
`run_notebook07_training()` dengan parameter berbeda (feature_cols, loader data,
kolom yang di-capping, nama artefak). Perbedaan VARIAN ditentukan di
`app/services/training_service.py`, bukan di modul ini — konsisten dengan pola
`notebook05_common.py`.

PENTING — isolasi:
    - Arsitektur: `FlexibleLSTMClassifier` (2-class softmax, aktivasi FC-head
      configurable) — BUKAN `LSTMDirectionClassifier` (produksi) maupun
      `LSTMSoftmaxClassifier` (notebook 05).
    - Split KRONOLOGIS PERSENTASE 70/15/15 (sama rasio dengan notebook 05, tapi
      logic capping-outlier SEBELUM scaling ini SPESIFIK notebook 07).
    - TIDAK ada early-stopping — tiap konfigurasi Random Search dilatih PENUH
      sejumlah `config["epochs"]` (epochs sendiri adalah salah satu hyperparameter
      yang di-*search*, bukan ditentukan dinamis).
    - Artefak disimpan ke file berprefix `lstm_baseline_skripsi_*` /
      `finbert_lstm_skripsi_*` (SAMA PERSIS dgn yang disimpan notebook 07 sendiri)
      — TIDAK menimpa `direction_classifier.pt` / `lstm_nb05_*`.

Granularitas SSE: 3 level (`start` -> [`iteration_start` -> `epoch`xN ->
`iteration_end`] x N_ITER -> `done`/`error`) — beda dari notebook05_common.py yang
flat (`start` -> `epoch`xN -> `done`). Ini karena Random Search melatih N_ITER
model independen (1 model = 1 konfigurasi), bukan 1 model final seperti notebook 05.
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
    precision_score,
    recall_score,
)
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset

from models.lstm.lstm_model import FlexibleLSTMClassifier

# ---------------------------------------------------------------------------
# Helpers — capping outlier (IQR, fit-train-only)
# ---------------------------------------------------------------------------

def compute_iqr_bounds(df_train: pd.DataFrame, cols: list[str]) -> dict[str, tuple[float, float]]:
    """Hitung batas IQR (Q1-1.5*IQR, Q3+1.5*IQR) HANYA dari train (anti-leakage)."""
    bounds: dict[str, tuple[float, float]] = {}
    for col in cols:
        q1, q3 = df_train[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        bounds[col] = (float(q1 - 1.5 * iqr), float(q3 + 1.5 * iqr))
    return bounds


def apply_capping(df: pd.DataFrame, bounds: dict[str, tuple[float, float]]) -> pd.DataFrame:
    """Clip kolom sesuai batas IQR yang sudah dihitung (dari train)."""
    out = df.copy()
    for col, (lower, upper) in bounds.items():
        out[col] = out[col].clip(lower=lower, upper=upper)
    return out


def _count_capped(df: pd.DataFrame, bounds: dict[str, tuple[float, float]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for col, (lower, upper) in bounds.items():
        counts[col] = int(((df[col] < lower) | (df[col] > upper)).sum())
    return counts


# ---------------------------------------------------------------------------
# Helpers — windowing
# ---------------------------------------------------------------------------

def _make_windows(features: np.ndarray, labels: np.ndarray, window: int) -> tuple[np.ndarray, np.ndarray]:
    n = len(features)
    if n < window:
        return (
            np.empty((0, window, features.shape[1]), dtype=np.float32),
            np.empty((0,), dtype=np.int64),
        )
    num_samples = n - window + 1
    X = np.stack([features[i : i + window] for i in range(num_samples)]).astype(np.float32)
    y = labels[window - 1 : window - 1 + num_samples].astype(np.int64)
    return X, y


# ---------------------------------------------------------------------------
# Helpers — Random Search sampling
# ---------------------------------------------------------------------------

def sample_config(rng: np.random.Generator, search_space: dict[str, Any]) -> dict[str, Any]:
    dropout_lo, dropout_hi = search_space["dropout"]
    lr_lo, lr_hi = search_space["lr"]
    log_lr = rng.uniform(np.log10(lr_lo), np.log10(lr_hi))
    return {
        "hidden_size": int(rng.choice(search_space["hidden_size"])),
        "num_layers": int(rng.choice(search_space["num_layers"])),
        "dropout": float(rng.uniform(dropout_lo, dropout_hi)),
        "optimizer": str(rng.choice(search_space["optimizer"])),
        "activation": str(rng.choice(search_space["activation"])),
        "lr": float(10 ** log_lr),
        "epochs": int(rng.choice(search_space["epochs"])),
        "batch_size": int(rng.choice(search_space["batch_size"])),
    }


def build_optimizer(name: str, params, lr: float) -> torch.optim.Optimizer:
    if name == "adam":
        return torch.optim.Adam(params, lr=lr)
    if name == "rmsprop":
        return torch.optim.RMSprop(params, lr=lr)
    if name == "sgd":
        return torch.optim.SGD(params, lr=lr)
    raise ValueError(f"Optimizer tidak dikenal: {name}")


def compute_class_weights(y_train: np.ndarray, device: torch.device) -> torch.Tensor:
    """Inverse-frequency class weights (2 kelas), dihitung dari TRAIN saja."""
    counts = np.bincount(y_train.astype(np.int64), minlength=2)
    w = 1.0 / (counts + 1e-9)
    w = w / w.sum() * len(counts)
    return torch.tensor(w, dtype=torch.float32, device=device)


# ---------------------------------------------------------------------------
# Helpers — training/eval loop per epoch
# ---------------------------------------------------------------------------

def _train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float]:
    model.train()
    total_loss = 0.0
    n_samples = 0
    y_true_all: list[int] = []
    y_pred_all: list[int] = []

    for xb, yb in loader:
        xb, yb = xb.to(device), yb.to(device)
        optimizer.zero_grad()
        logits = model(xb)
        loss = criterion(logits, yb)
        loss.backward()
        optimizer.step()

        bs = xb.size(0)
        total_loss += loss.item() * bs
        n_samples += bs

        preds = logits.argmax(dim=1).detach().cpu().numpy()
        y_true_all.extend(yb.detach().cpu().numpy().tolist())
        y_pred_all.extend(preds.tolist())

    avg_loss = total_loss / n_samples if n_samples else 0.0
    acc = accuracy_score(y_true_all, y_pred_all) if n_samples else 0.0
    return avg_loss, float(acc)


def _evaluate_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float, float, np.ndarray, np.ndarray]:
    """Return (loss, acc, f1, y_true, y_pred)."""
    model.eval()
    total_loss = 0.0
    n_samples = 0
    y_true_all: list[int] = []
    y_pred_all: list[int] = []

    with torch.no_grad():
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            logits = model(xb)
            loss = criterion(logits, yb)

            bs = xb.size(0)
            total_loss += loss.item() * bs
            n_samples += bs

            preds = logits.argmax(dim=1).cpu().numpy()
            y_true_all.extend(yb.cpu().numpy().tolist())
            y_pred_all.extend(preds.tolist())

    y_true = np.array(y_true_all, dtype=np.int64)
    y_pred = np.array(y_pred_all, dtype=np.int64)

    avg_loss = total_loss / n_samples if n_samples else 0.0
    acc = accuracy_score(y_true, y_pred) if n_samples else 0.0
    f1 = f1_score(y_true, y_pred, zero_division=0) if n_samples else 0.0
    return avg_loss, float(acc), float(f1), y_true, y_pred


def _r6(x: float) -> float:
    """Round wajar & aman untuk JSON (cast dari numpy)."""
    return round(float(x), 6)


def _load_split_capped(
    load_data_fn: Callable[[], pd.DataFrame],
    capping_cols: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, tuple[float, float]], dict[str, dict[str, int]]]:
    """Load + label horizon-1 + split KRONOLOGIS PERSENTASE 70/15/15 + capping
    outlier IQR (fit-train-only). Diekstrak dari `run_notebook07_training()`
    supaya predict/backtest bisa reuse split & bounds yang SAMA seperti training
    (split deterministik by-percentage, jadi re-split menghasilkan df_train yang
    identik — capping_bounds boleh dihitung ulang tanpa disimpan ke artefak).

    `n_capped` (jumlah nilai yang di-clip per split) WAJIB dihitung SEBELUM
    capping diterapkan — setelah di-capping, semua nilai otomatis berada dalam
    bounds sehingga hitungannya akan selalu nol.
    """
    df = load_data_fn()
    df["label"] = (df["Close"].shift(-1) > df["Close"]).astype("int64")
    df = df.iloc[:-1].copy().reset_index(drop=True)

    n = len(df)
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)

    df_train = df.iloc[:n_train].reset_index(drop=True)
    df_val = df.iloc[n_train : n_train + n_val].reset_index(drop=True)
    df_test = df.iloc[n_train + n_val :].reset_index(drop=True)

    capping_bounds = compute_iqr_bounds(df_train, capping_cols) if capping_cols else {}
    n_capped = {
        "train": _count_capped(df_train, capping_bounds),
        "val": _count_capped(df_val, capping_bounds),
        "test": _count_capped(df_test, capping_bounds),
    }
    if capping_bounds:
        df_train = apply_capping(df_train, capping_bounds)
        df_val = apply_capping(df_val, capping_bounds)
        df_test = apply_capping(df_test, capping_bounds)

    return df_train, df_val, df_test, capping_bounds, n_capped


# ---------------------------------------------------------------------------
# run_notebook07_training — dipakai bersama oleh Model A (baseline) & Model B (FinBERT-LSTM)
# ---------------------------------------------------------------------------

def run_notebook07_training(
    *,
    emit: Callable[[dict], None],
    feature_cols: list[str],
    load_data_fn: Callable[[], pd.DataFrame],
    capping_cols: list[str],
    search_space: dict[str, Any],
    n_iter: int,
    window: int,
    artifact_dir: str,
    model_filename: str,
    scaler_filename: str,
    metadata_filename: str,
    seed: int = 42,
) -> dict:
    """Jalankan Random Search (replikasi notebook 07) dan stream progress via
    `emit()`. Event: "start" -> ["iteration_start" -> "epoch"xN -> "iteration_end"]
    x n_iter -> "done" (atau "error" bila gagal).

    Return dict payload event "done"/"error" (tanpa key "type") untuk kebutuhan
    pemanggilan non-SSE (mis. smoke test).
    """
    try:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # -------------------------------------------------------------
        # 1-3. Load+label+split 70/15/15 + capping outlier (IQR, fit-train-only)
        # -------------------------------------------------------------
        df_train, df_val, df_test, capping_bounds, n_capped = _load_split_capped(load_data_fn, capping_cols)

        # -------------------------------------------------------------
        # 4. Scaling — MinMaxScaler fit HANYA di train (anti-leakage)
        # -------------------------------------------------------------
        scaler = MinMaxScaler()
        train_feat = scaler.fit_transform(df_train[feature_cols].values.astype(np.float64))
        val_feat = scaler.transform(df_val[feature_cols].values.astype(np.float64))
        test_feat = scaler.transform(df_test[feature_cols].values.astype(np.float64))

        # -------------------------------------------------------------
        # 5. Windowing per-split (fixed window, TIDAK ikut di-search)
        # -------------------------------------------------------------
        X_train, y_train = _make_windows(train_feat, df_train["label"].values, window)
        X_val, y_val = _make_windows(val_feat, df_val["label"].values, window)
        X_test, y_test = _make_windows(test_feat, df_test["label"].values, window)

        emit({
            "type": "start",
            "total_iterations": n_iter,
            "window": window,
            "search_space": search_space,
            "feature_cols": feature_cols,
            "device": device.type,
            "split": {
                "train_rows": len(df_train),
                "val_rows": len(df_val),
                "test_rows": len(df_test),
                "train_samples": len(X_train),
                "val_samples": len(X_val),
                "test_samples": len(X_test),
            },
            "preprocessing": {
                "capping_bounds": {k: list(v) for k, v in capping_bounds.items()},
                "n_capped": n_capped,
            },
        })

        # -------------------------------------------------------------
        # 6. Random Search — n_iter iterasi, tiap iterasi = 1 model penuh
        # -------------------------------------------------------------
        rng = np.random.default_rng(seed)
        best: dict[str, Any] = {"val_f1": -1.0, "val_acc": -1.0, "config": None, "state_dict": None}

        train_ds = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train))
        X_val_dl_ds = TensorDataset(torch.from_numpy(X_val), torch.from_numpy(y_val))

        for i in range(n_iter):
            config = sample_config(rng, search_space)
            emit({
                "type": "iteration_start",
                "iteration": i + 1,
                "total_iterations": n_iter,
                "config": config,
            })

            torch.manual_seed(seed + i)
            model = FlexibleLSTMClassifier(
                input_size=len(feature_cols),
                hidden_size=config["hidden_size"],
                num_layers=config["num_layers"],
                dropout=config["dropout"],
                activation=config["activation"],
                num_classes=2,
            ).to(device)

            optimizer = build_optimizer(config["optimizer"], model.parameters(), config["lr"])
            class_weights = compute_class_weights(y_train, device)
            criterion = nn.CrossEntropyLoss(weight=class_weights)

            train_loader = DataLoader(train_ds, batch_size=config["batch_size"], shuffle=True)
            val_loader = DataLoader(X_val_dl_ds, batch_size=config["batch_size"], shuffle=False)

            final_val_acc = 0.0
            final_val_f1 = 0.0

            for epoch in range(1, config["epochs"] + 1):
                train_loss, train_acc = _train_one_epoch(model, train_loader, optimizer, criterion, device)
                val_loss, val_acc, val_f1, _, _ = _evaluate_epoch(model, val_loader, criterion, device)

                final_val_acc = val_acc
                final_val_f1 = val_f1

                emit({
                    "type": "epoch",
                    "iteration": i + 1,
                    "epoch": epoch,
                    "total_epochs": config["epochs"],
                    "train_loss": _r6(train_loss),
                    "train_acc": _r6(train_acc),
                    "val_loss": _r6(val_loss),
                    "val_acc": _r6(val_acc),
                    "val_f1": _r6(val_f1),
                })

            is_new_best = final_val_f1 > best["val_f1"]
            emit({
                "type": "iteration_end",
                "iteration": i + 1,
                "total_iterations": n_iter,
                "config": config,
                "val_f1": _r6(final_val_f1),
                "val_acc": _r6(final_val_acc),
                "is_new_best": bool(is_new_best),
            })

            if is_new_best:
                best = {
                    "val_f1": final_val_f1,
                    "val_acc": final_val_acc,
                    "config": config,
                    "state_dict": deepcopy({k: v.detach().cpu().clone() for k, v in model.state_dict().items()}),
                }

        assert best["state_dict"] is not None, "Random Search tidak menghasilkan model terbaik"

        # -------------------------------------------------------------
        # 7. Evaluasi final di TEST (HANYA 4 metrik, sesuai Batasan Masalah)
        # -------------------------------------------------------------
        best_config = best["config"]
        best_model = FlexibleLSTMClassifier(
            input_size=len(feature_cols),
            hidden_size=best_config["hidden_size"],
            num_layers=best_config["num_layers"],
            dropout=best_config["dropout"],
            activation=best_config["activation"],
            num_classes=2,
        ).to(device)
        best_model.load_state_dict(best["state_dict"])
        best_model.eval()

        X_test_t = torch.from_numpy(X_test).to(device)
        with torch.no_grad():
            test_logits = best_model(X_test_t)
            y_test_pred = test_logits.argmax(dim=1).cpu().numpy()

        tn, fp, fn, tp = confusion_matrix(y_test, y_test_pred, labels=[0, 1]).ravel()
        metrics = {
            "accuracy": _r6(accuracy_score(y_test, y_test_pred)),
            "precision": _r6(precision_score(y_test, y_test_pred, zero_division=0)),
            "recall": _r6(recall_score(y_test, y_test_pred, zero_division=0)),
            "f1": _r6(f1_score(y_test, y_test_pred, zero_division=0)),
        }
        confusion = {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}

        # -------------------------------------------------------------
        # 8. Simpan artefak TERISOLASI (nama sama persis notebook 07)
        # -------------------------------------------------------------
        artifact_path_dir = Path(artifact_dir)
        artifact_path_dir.mkdir(parents=True, exist_ok=True)

        model_path = artifact_path_dir / model_filename
        scaler_path = artifact_path_dir / scaler_filename
        metadata_path = artifact_path_dir / metadata_filename

        torch.save({
            "model_state_dict": best["state_dict"],
            "config": best_config,
            "feature_cols": feature_cols,
            "window": window,
        }, model_path)
        joblib.dump(scaler, scaler_path)

        trained_at = datetime.now(timezone.utc).isoformat()
        metadata = {
            "config": best_config,
            "feature_cols": feature_cols,
            "window": window,
            "metrics": metrics,
            "confusion_matrix": confusion,
            "best_val_f1": _r6(best["val_f1"]),
            "best_val_acc": _r6(best["val_acc"]),
            "split_sizes": {
                "train_rows": len(df_train),
                "val_rows": len(df_val),
                "test_rows": len(df_test),
                "train_samples": len(X_train),
                "val_samples": len(X_val),
                "test_samples": len(X_test),
            },
            "trained_at": trained_at,
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
            "best_config": best_config,
            "best_val_f1": _r6(best["val_f1"]),
            "best_val_acc": _r6(best["val_acc"]),
            "metrics": metrics,
            "confusion_matrix": confusion,
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
# run_notebook07_training() di atas (lstm_baseline_skripsi_*/finbert_lstm_skripsi_*).
# ---------------------------------------------------------------------------

def load_trained_notebook07(
    *,
    artifact_dir: str,
    model_filename: str,
    scaler_filename: str,
    metadata_filename: str,
) -> dict[str, Any] | None:
    """Rekonstruksi `FlexibleLSTMClassifier` (eval mode) + scaler + metadata dari
    artefak tersimpan. Beda dari `load_trained_notebook05`: `window` dibaca dari
    `checkpoint["window"]` (top-level), BUKAN dari `config["seq_len"]` — config
    notebook07 tidak punya `seq_len` karena window fixed (tidak ikut di-search).
    Return `None` kalau belum pernah training."""
    artifact_path_dir = Path(artifact_dir)
    model_path = artifact_path_dir / model_filename
    scaler_path = artifact_path_dir / scaler_filename
    metadata_path = artifact_path_dir / metadata_filename

    if not (model_path.exists() and scaler_path.exists() and metadata_path.exists()):
        return None

    checkpoint = torch.load(model_path, map_location="cpu")
    cfg = checkpoint["config"]
    feature_cols = checkpoint["feature_cols"]
    window = checkpoint["window"]

    model = FlexibleLSTMClassifier(
        input_size=len(feature_cols),
        hidden_size=int(cfg["hidden_size"]),
        num_layers=int(cfg["num_layers"]),
        dropout=float(cfg["dropout"]),
        activation=cfg["activation"],
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
        "window": window,
    }


def predict_latest_notebook07(
    *,
    feature_cols: list[str],
    load_data_fn: Callable[[], pd.DataFrame],
    capping_cols: list[str],
    artifact_dir: str,
    model_filename: str,
    scaler_filename: str,
    metadata_filename: str,
) -> dict[str, Any]:
    """Prediksi arah harga hari berikutnya dari window TERAKHIR data, pakai
    model terlatih (persisted). Window terakhir di-capping dgn bounds yang
    dihitung ulang dari df_train (`_load_split_capped()`, konsisten dgn
    preprocessing training) SEBELUM di-scale. Return `{"trained": False}`
    kalau belum pernah training."""
    loaded = load_trained_notebook07(
        artifact_dir=artifact_dir,
        model_filename=model_filename,
        scaler_filename=scaler_filename,
        metadata_filename=metadata_filename,
    )
    if loaded is None:
        return {"trained": False}

    window = loaded["window"]
    df_train, _, _, capping_bounds, _ = _load_split_capped(load_data_fn, capping_cols)

    df = load_data_fn()
    if len(df) < window:
        raise ValueError(
            f"Dataset hanya punya {len(df)} baris, butuh minimal {window} baris."
        )

    df_latest = df.iloc[-window:].reset_index(drop=True)
    if capping_bounds:
        df_latest = apply_capping(df_latest, capping_bounds)

    feat = loaded["scaler"].transform(df_latest[feature_cols].values.astype(np.float64))
    X = feat[np.newaxis, :, :].astype(np.float32)

    as_of_date = df_latest["Date"].iloc[-1]
    as_of_str = as_of_date.strftime("%Y-%m-%d")
    target_str = (as_of_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

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
        "window": window,
        "feature_cols": feature_cols,
        "trained_at": loaded["metadata"].get("trained_at"),
        "best_val_f1": loaded["metadata"].get("best_val_f1"),
    }


def backtest_notebook07(
    *,
    feature_cols: list[str],
    load_data_fn: Callable[[], pd.DataFrame],
    capping_cols: list[str],
    artifact_dir: str,
    model_filename: str,
    scaler_filename: str,
    metadata_filename: str,
    split: str = "test",
) -> dict[str, Any]:
    """Jalankan model terlatih di data historis (split + capping yang SAMA
    seperti training — reuse `_load_split_capped()`, scaler TIDAK di-fit ulang;
    windowing pakai `_make_windows()` punya modul ini, BUKAN `create_sequences`
    notebook05) dan kembalikan prediksi-vs-aktual per-titik + metrik (HANYA 4:
    accuracy/precision/recall/f1, sesuai Batasan Masalah BAB I — TIDAK ada F2/AUC
    supaya konsisten dengan apa yang dihitung `run_notebook07_training()`).
    Return `{"trained": False}` kalau belum pernah training."""
    loaded = load_trained_notebook07(
        artifact_dir=artifact_dir,
        model_filename=model_filename,
        scaler_filename=scaler_filename,
        metadata_filename=metadata_filename,
    )
    if loaded is None:
        return {"trained": False}

    window = loaded["window"]
    scaler = loaded["scaler"]

    df_train, df_val, df_test, _, _ = _load_split_capped(load_data_fn, capping_cols)
    df_split = {"train": df_train, "val": df_val, "test": df_test}[split]

    X_raw = scaler.transform(df_split[feature_cols].values.astype(np.float64))
    y_raw = df_split["label"].values.astype(np.int64)
    X_seq, y_seq = _make_windows(X_raw, y_raw, window)

    dates = df_split["Date"].iloc[window - 1 :].dt.strftime("%Y-%m-%d").tolist()
    closes = df_split["Close"].iloc[window - 1 :].tolist()

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

    metrics = {
        "accuracy": _r6(accuracy_score(y_int, pred_int)),
        "precision": _r6(precision_score(y_int, pred_int, zero_division=0)),
        "recall": _r6(recall_score(y_int, pred_int, zero_division=0)),
        "f1": _r6(f1_score(y_int, pred_int, zero_division=0)),
    }

    tn, fp, fn, tp = confusion_matrix(y_int, pred_int, labels=[0, 1]).ravel()

    return {
        "trained": True,
        "window": window,
        "split": split,
        "n_samples": len(points),
        "metrics": metrics,
        "confusion_matrix": {"tp": int(tp), "tn": int(tn), "fp": int(fp), "fn": int(fn)},
        "points": points,
    }
