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

Parameter `horizon` (default 1, ditambahkan belakangan): fungsi ini sendiri
TIDAK mengunci horizon — nilainya ditentukan oleh caller.

DEVIASI BATASAN MASALAH BAB I (disengaja, keputusan eksplisit user 2026-07-28
setelah notebook 12 — lihat CLAUDE.md log): `training_service.py` kini mengirim
`horizon=5` (bukan default 1) untuk varian Model A/B skripsi, dan seleksi model
Random Search dipilih via **F1-macro + threshold sweep** (`sweep_best_threshold()`,
BUKAN val-F1 kelas positif + argmax/0.5 seperti sebelumnya) — resep dari
notebook 09/12 untuk mengatasi class collapse. `metrics` juga bertambah
`f1_macro`/`recall_down`/`recall_up` (di luar 4 metrik ketat Batasan Masalah)
karena dibutuhkan untuk memverifikasi model tidak collapse ke 1 kelas.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
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


def sweep_best_threshold(y_true: np.ndarray, probs_up: np.ndarray, n_steps: int = 197) -> tuple[float, float]:
    """Cari threshold probabilitas "up" yang memaksimalkan F1-macro (rata-rata
    F1 kelas up & down) di `y_true`/`probs_up`. Beda dari argmax/0.5 tetap
    (yang hanya optimal utk F1 kelas positif) — dipakai utk memilih & evaluasi
    model supaya Random Search tidak memilih konfigurasi yang collapse ke 1
    kelas (recall kelas yang diabaikan jatuh ke 0, otomatis menyeret F1-macro
    turun — resep notebook 09/12 utk mengatasi class collapse). Return
    (best_threshold, best_f1_macro)."""
    best_t, best_score = 0.5, -1.0
    for t in np.linspace(0.01, 0.99, n_steps):
        preds = (probs_up >= t).astype(int)
        score = f1_score(y_true, preds, average="macro", zero_division=0)
        if score > best_score:
            best_score, best_t = score, float(t)
    return best_t, float(best_score)


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


def load_split_capped(
    load_data_fn: Callable[[], pd.DataFrame],
    capping_cols: list[str],
    horizon: int = 1,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, tuple[float, float]], dict[str, dict[str, int]]]:
    """Load + label horizon-N + split KRONOLOGIS PERSENTASE + capping outlier
    IQR (fit-train-only). Diekstrak dari `run_notebook07_training()` supaya
    predict/backtest bisa reuse split & bounds yang SAMA seperti training
    (split deterministik by-percentage, jadi re-split menghasilkan df_train yang
    identik — capping_bounds boleh dihitung ulang tanpa disimpan ke artefak).

    `horizon` default 1 (sesuai Batasan Masalah BAB I) — TIDAK mengubah perilaku
    caller produksi manapun yang tidak mengirim argumen ini secara eksplisit.
    Nilai lain (mis. 5) dipakai notebook eksperimen di luar scope BAB I untuk
    menguji sensitivitas horizon prediksi.

    `train_ratio`/`val_ratio` default 0.70/0.15 (split Random Search — sisanya
    jadi test 15%). Caller produksi lain yang tidak mengirim argumen ini TIDAK
    berubah perilaku. `run_notebook07_manual_training()` mengirim 0.80/0.0
    (Train:Test 80:20, TANPA val) — proses training manual/final TIDAK butuh
    val terpisah karena tidak ada seleksi konfigurasi seperti Random Search;
    `df_val` akan kosong (0 baris) bila `val_ratio=0.0`.

    `n_capped` (jumlah nilai yang di-clip per split) WAJIB dihitung SEBELUM
    capping diterapkan — setelah di-capping, semua nilai otomatis berada dalam
    bounds sehingga hitungannya akan selalu nol.
    """
    df = load_data_fn()
    df["label"] = (df["Close"].shift(-horizon) > df["Close"]).astype("int64")
    df = df.iloc[:-horizon].copy().reset_index(drop=True)

    n = len(df)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

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
# DatasetBundle — hasil load->label->split->capping->scaling->windowing,
# dipakai BERSAMA oleh training live (run_notebook07_training/manual) DAN
# artifact tersimpan (save/load_dataset_bundle, dipakai tombol "Bangun Dataset
# Latih" halaman Workflow) — SATU-SATUNYA salinan logic ini.
# ---------------------------------------------------------------------------

@dataclass
class DatasetBundle:
    X_train: np.ndarray
    y_train: np.ndarray
    X_val: np.ndarray
    y_val: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    scaler: MinMaxScaler
    capping_bounds: dict[str, tuple[float, float]]
    n_capped: dict[str, dict[str, int]]
    feature_cols: list[str]
    window: int
    horizon: int
    train_ratio: float
    val_ratio: float
    split_sizes: dict[str, int]


def prepare_dataset_bundle(
    load_data_fn: Callable[[], pd.DataFrame],
    capping_cols: list[str],
    feature_cols: list[str],
    horizon: int,
    train_ratio: float,
    val_ratio: float,
    window: int,
) -> DatasetBundle:
    """load_split_capped() -> MinMaxScaler (fit train-only) -> windowing.
    Dipanggil live oleh run_notebook07_training()/run_notebook07_manual_training()
    (bila tidak diberi `prebuilt_dataset`) DAN oleh save_dataset_bundle() saat
    tombol "Bangun Dataset Latih" (Workflow) diklik."""
    df_train, df_val, df_test, capping_bounds, n_capped = load_split_capped(
        load_data_fn, capping_cols, horizon, train_ratio=train_ratio, val_ratio=val_ratio,
    )

    def _transform(df: pd.DataFrame) -> np.ndarray:
        # sklearn MinMaxScaler.transform() menolak array 0-baris (mis. df_val
        # kosong saat val_ratio=0.0, mode manual training) — short-circuit
        # supaya tetap menghasilkan array kosong ber-shape benar, bukan error.
        if len(df) == 0:
            return np.empty((0, len(feature_cols)), dtype=np.float64)
        return scaler.transform(df[feature_cols].values.astype(np.float64))

    scaler = MinMaxScaler()
    train_feat = scaler.fit_transform(df_train[feature_cols].values.astype(np.float64))
    val_feat = _transform(df_val)
    test_feat = _transform(df_test)

    X_train, y_train = _make_windows(train_feat, df_train["label"].values, window)
    X_val, y_val = _make_windows(val_feat, df_val["label"].values, window)
    X_test, y_test = _make_windows(test_feat, df_test["label"].values, window)

    split_sizes = {
        "train_rows": len(df_train),
        "val_rows": len(df_val),
        "test_rows": len(df_test),
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
    }
    return DatasetBundle(
        X_train=X_train, y_train=y_train,
        X_val=X_val, y_val=y_val,
        X_test=X_test, y_test=y_test,
        scaler=scaler,
        capping_bounds=capping_bounds,
        n_capped=n_capped,
        feature_cols=feature_cols,
        window=window,
        horizon=horizon,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        split_sizes=split_sizes,
    )


def _source_fingerprint() -> dict[str, Any]:
    """mtime+size STOCK_CSV/SENTIMENT_CSV — dipakai dataset_bundle_status() utk
    deteksi artifact basi (mis. setelah 'Jalankan Sentiment Scoring' dijalankan
    ulang dan menimpa headlines_daily_sentiment.csv)."""
    from pipeline.feature_engineering.dataset_builder import SENTIMENT_CSV, STOCK_CSV  # noqa: PLC0415

    root = Path(__file__).resolve().parents[2]
    fp: dict[str, Any] = {}
    for key, rel in [("stock_csv", STOCK_CSV), ("sentiment_csv", SENTIMENT_CSV)]:
        p = root / rel
        if p.exists():
            st = p.stat()
            fp[key] = {"path": rel, "mtime": round(st.st_mtime, 3), "size": st.st_size}
        else:
            fp[key] = None
    return fp


def _dataset_artifact_paths(artifact_dir: str, prefix: str) -> dict[str, Path]:
    d = Path(artifact_dir)
    return {
        "arrays": d / f"{prefix}_dataset.npz",
        "scaler": d / f"{prefix}_dataset_scaler.joblib",
        "meta": d / f"{prefix}_dataset_meta.json",
    }


def save_dataset_bundle(bundle: DatasetBundle, artifact_dir: str, prefix: str) -> dict[str, Any]:
    """Simpan DatasetBundle ke disk: array .npz + scaler .joblib + meta .json
    (feature_cols/window/horizon/split_ratio/capping/split_sizes/fingerprint
    sumber data/built_at). Return ringkasan (dipakai response POST build-dataset)."""
    paths = _dataset_artifact_paths(artifact_dir, prefix)
    paths["arrays"].parent.mkdir(parents=True, exist_ok=True)

    np.savez(
        paths["arrays"],
        X_train=bundle.X_train, y_train=bundle.y_train,
        X_val=bundle.X_val, y_val=bundle.y_val,
        X_test=bundle.X_test, y_test=bundle.y_test,
    )
    joblib.dump(bundle.scaler, paths["scaler"])

    built_at = datetime.now(timezone.utc).isoformat()
    meta = {
        "feature_cols": bundle.feature_cols,
        "window": bundle.window,
        "horizon": bundle.horizon,
        "train_ratio": bundle.train_ratio,
        "val_ratio": bundle.val_ratio,
        "capping_bounds": {k: list(v) for k, v in bundle.capping_bounds.items()},
        "n_capped": bundle.n_capped,
        "split_sizes": bundle.split_sizes,
        "source_fingerprint": _source_fingerprint(),
        "built_at": built_at,
    }
    paths["meta"].write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return {
        "built_at": built_at,
        "split_sizes": bundle.split_sizes,
        "n_capped": bundle.n_capped,
        "artifact_paths": {k: str(v) for k, v in paths.items()},
    }


def load_dataset_bundle(artifact_dir: str, prefix: str) -> DatasetBundle | None:
    """Baca kembali DatasetBundle tersimpan. Return None kalau belum pernah dibangun."""
    paths = _dataset_artifact_paths(artifact_dir, prefix)
    if not all(p.exists() for p in paths.values()):
        return None

    arrays = np.load(paths["arrays"])
    scaler = joblib.load(paths["scaler"])
    meta = json.loads(paths["meta"].read_text(encoding="utf-8"))

    return DatasetBundle(
        X_train=arrays["X_train"], y_train=arrays["y_train"],
        X_val=arrays["X_val"], y_val=arrays["y_val"],
        X_test=arrays["X_test"], y_test=arrays["y_test"],
        scaler=scaler,
        capping_bounds={k: tuple(v) for k, v in meta["capping_bounds"].items()},
        n_capped=meta["n_capped"],
        feature_cols=meta["feature_cols"],
        window=meta["window"],
        horizon=meta["horizon"],
        train_ratio=meta["train_ratio"],
        val_ratio=meta["val_ratio"],
        split_sizes=meta["split_sizes"],
    )


def dataset_bundle_status(artifact_dir: str, prefix: str) -> dict[str, Any]:
    """Status artifact dataset: exists/is_fresh (fingerprint sumber data
    dibandingkan saat ini)/built_at/split_sizes — dipakai GET dataset-status
    (Workflow) & training_service.py sebelum training baca artifact."""
    paths = _dataset_artifact_paths(artifact_dir, prefix)
    if not all(p.exists() for p in paths.values()):
        return {"exists": False, "is_fresh": False, "built_at": None, "split_sizes": None}

    meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
    is_fresh = meta.get("source_fingerprint") == _source_fingerprint()

    return {
        "exists": True,
        "is_fresh": is_fresh,
        "built_at": meta.get("built_at"),
        "split_sizes": meta.get("split_sizes"),
    }


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
    horizon: int = 1,
    prebuilt_dataset: DatasetBundle | None = None,
) -> dict:
    """Jalankan Random Search (replikasi notebook 07) dan stream progress via
    `emit()`. Event: "start" -> ["iteration_start" -> "epoch"xN -> "iteration_end"]
    x n_iter -> "done" (atau "error" bila gagal).

    `horizon` default 1 (Batasan Masalah BAB I) — caller produksi
    (`training_service.py`) tidak mengirim argumen ini sehingga perilakunya
    TIDAK berubah. Dipakai notebook eksperimen horizon-sensitivity di luar
    scope BAB I dengan mengirim `horizon=5` dst.

    `prebuilt_dataset` opsional (default None) — kalau diisi, `load_data_fn`/
    `capping_cols`/`horizon` TIDAK dipakai utk hitung ulang data (dataset sudah
    dibangun sebelumnya via `prepare_dataset_bundle()`/tombol "Bangun Dataset
    Latih" di Workflow, dibaca dari artifact tersimpan). Kalau None (default —
    dipakai `notebooks/10_LSTM_horizon5_skripsi_scoped.ipynb` & caller lama),
    data dihitung live persis seperti sebelumnya. `training_service.py` SELALU
    mengirim `prebuilt_dataset` (arsitektur "Data Provider" — training baca dari
    artifact Workflow, tidak recompute sendiri).

    Return dict payload event "done"/"error" (tanpa key "type") untuk kebutuhan
    pemanggilan non-SSE (mis. smoke test).
    """
    try:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # -------------------------------------------------------------
        # 1-5. Load+label+split 70/15/15 + capping outlier + scaling + windowing
        # — dari prebuilt_dataset (artifact) kalau ada, else hitung live.
        # -------------------------------------------------------------
        bundle = prebuilt_dataset or prepare_dataset_bundle(
            load_data_fn, capping_cols, feature_cols, horizon,
            train_ratio=0.70, val_ratio=0.15, window=window,
        )
        X_train, y_train = bundle.X_train, bundle.y_train
        X_val, y_val = bundle.X_val, bundle.y_val
        X_test, y_test = bundle.X_test, bundle.y_test
        scaler = bundle.scaler
        capping_bounds = bundle.capping_bounds
        n_capped = bundle.n_capped

        emit({
            "type": "start",
            "total_iterations": n_iter,
            "window": window,
            "horizon": horizon,
            "search_space": search_space,
            "feature_cols": feature_cols,
            "device": device.type,
            "split": bundle.split_sizes,
            "preprocessing": {
                "capping_bounds": {k: list(v) for k, v in capping_bounds.items()},
                "n_capped": n_capped,
            },
        })

        # -------------------------------------------------------------
        # 6. Random Search — n_iter iterasi, tiap iterasi = 1 model penuh
        # -------------------------------------------------------------
        rng = np.random.default_rng(seed)
        best: dict[str, Any] = {
            "val_f1_macro": -1.0, "threshold": 0.5,
            "val_f1": -1.0, "val_acc": -1.0, "config": None, "state_dict": None,
        }

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

            # -----------------------------------------------------------
            # Seleksi konfigurasi: F1-macro + threshold sweep (bukan
            # argmax/0.5) — resep notebook 09/12 utk hindari config yang
            # collapse ke 1 kelas (recall kelas diabaikan jatuh ke 0,
            # otomatis menyeret F1-macro turun sehingga config tsb ditolak).
            # -----------------------------------------------------------
            model.eval()
            X_val_t = torch.from_numpy(X_val).to(device)
            with torch.no_grad():
                val_probs_up = torch.softmax(model(X_val_t), dim=1)[:, 1].cpu().numpy()
            val_threshold, val_f1_macro = sweep_best_threshold(y_val, val_probs_up)

            is_new_best = val_f1_macro > best["val_f1_macro"]
            emit({
                "type": "iteration_end",
                "iteration": i + 1,
                "total_iterations": n_iter,
                "config": config,
                "val_f1": _r6(final_val_f1),
                "val_acc": _r6(final_val_acc),
                "val_f1_macro": _r6(val_f1_macro),
                "threshold": _r6(val_threshold),
                "is_new_best": bool(is_new_best),
            })

            if is_new_best:
                best = {
                    "val_f1_macro": val_f1_macro,
                    "threshold": val_threshold,
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

        best_threshold = best["threshold"]
        X_test_t = torch.from_numpy(X_test).to(device)
        with torch.no_grad():
            test_probs_up = torch.softmax(best_model(X_test_t), dim=1)[:, 1].cpu().numpy()
        y_test_pred = (test_probs_up >= best_threshold).astype(int)

        tn, fp, fn, tp = confusion_matrix(y_test, y_test_pred, labels=[0, 1]).ravel()
        metrics = {
            "accuracy": _r6(accuracy_score(y_test, y_test_pred)),
            "precision": _r6(precision_score(y_test, y_test_pred, zero_division=0)),
            "recall": _r6(recall_score(y_test, y_test_pred, zero_division=0)),
            "f1": _r6(f1_score(y_test, y_test_pred, zero_division=0)),
            "f1_macro": _r6(f1_score(y_test, y_test_pred, average="macro", zero_division=0)),
            "recall_down": _r6(recall_score(y_test, y_test_pred, pos_label=0, zero_division=0)),
            "recall_up": _r6(recall_score(y_test, y_test_pred, pos_label=1, zero_division=0)),
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
            "threshold": best_threshold,
        }, model_path)
        joblib.dump(scaler, scaler_path)

        trained_at = datetime.now(timezone.utc).isoformat()
        metadata = {
            "config": best_config,
            "feature_cols": feature_cols,
            "window": window,
            "horizon": horizon,
            "metrics": metrics,
            "confusion_matrix": confusion,
            "threshold": _r6(best_threshold),
            "best_val_f1_macro": _r6(best["val_f1_macro"]),
            "best_val_f1": _r6(best["val_f1"]),
            "best_val_acc": _r6(best["val_acc"]),
            "eval_split": "val",
            "split_ratio": {"train": bundle.train_ratio, "val": bundle.val_ratio},
            "split_sizes": bundle.split_sizes,
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
            "threshold": _r6(best_threshold),
            "best_val_f1_macro": _r6(best["val_f1_macro"]),
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
# run_notebook07_manual_training — training 1-konfigurasi (fixed hyperparameter,
# BUKAN Random Search). Dipakai fitur "Training Manual" FE (input bebas) dan
# "Retrain dengan Best Config" (config diambil dari hasil run_notebook07_training
# di atas, dilatih ulang persis 1x). Reuse load/split/scaling/windowing/model/
# optimizer/training-loop yang SAMA dengan run_notebook07_training(), hanya
# TANPA loop n_iter — 1 model, event SSE flat (2 level: start -> epoch xN ->
# done/error, BUKAN 3 level start -> [iteration_start -> epoch xN ->
# iteration_end] x n_iter). Artefak disimpan ke nama file YANG SAMA dengan
# Random Search varian terkait (model_filename/scaler_filename/metadata_filename
# dikirim caller) — training manual SENGAJA menimpa model resmi varian tsb,
# supaya halaman Prediction (result/predict/backtest) otomatis ikut ter-update.
# ---------------------------------------------------------------------------

def run_notebook07_manual_training(
    *,
    emit: Callable[[dict], None],
    config: dict[str, Any],
    feature_cols: list[str],
    load_data_fn: Callable[[], pd.DataFrame],
    capping_cols: list[str],
    window: int,
    artifact_dir: str,
    model_filename: str,
    scaler_filename: str,
    metadata_filename: str,
    seed: int = 42,
    horizon: int = 1,
    prebuilt_dataset: DatasetBundle | None = None,
) -> dict:
    """Latih 1 model dengan `config` yang sudah ditentukan (bukan hasil sampling
    Random Search) dan stream progress via `emit()`. Event: "start" ->
    "epoch"xN -> "done" (atau "error" bila gagal).

    `config` wajib berisi 8 field yang sama dengan hasil `sample_config()`:
    hidden_size, num_layers, dropout, optimizer, activation, lr, epochs,
    batch_size.

    Split Train:Test 80:20 (TANPA val) — beda dari `run_notebook07_training()`
    (Random Search, 70/15/15) karena training manual/final tidak melakukan
    seleksi konfigurasi (tidak butuh val terpisah dari test); `config` sudah
    fixed sejak awal (input bebas FE atau hasil `best_config` Random Search),
    jadi metrik per-epoch yang dimonitor JUJUR disebut "test" (dihitung dari
    20% test split), bukan "val" — tidak ada keputusan (seleksi/early-stop)
    yang diambil dari angka ini selama training, jadi tidak ada kebocoran
    metodologis walau dilaporkan live per-epoch.

    `prebuilt_dataset` opsional — lihat docstring `run_notebook07_training()`.
    Bila diisi, HARUS dataset hasil `split_mode="manual"` (train_ratio=0.80,
    val_ratio=0.0) — caller (`training_service.py`) bertanggung jawab
    mengirim bundle yang sesuai.

    Return dict payload event "done"/"error" (tanpa key "type"), sama seperti
    `run_notebook07_training()`.
    """
    try:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # -------------------------------------------------------------
        # 1-5. Load+label+split 80:20 (TANPA val) + capping outlier + scaling
        # + windowing — dari prebuilt_dataset (artifact) kalau ada, else live.
        # -------------------------------------------------------------
        bundle = prebuilt_dataset or prepare_dataset_bundle(
            load_data_fn, capping_cols, feature_cols, horizon,
            train_ratio=0.80, val_ratio=0.0, window=window,
        )
        X_train, y_train = bundle.X_train, bundle.y_train
        X_test, y_test = bundle.X_test, bundle.y_test
        scaler = bundle.scaler
        capping_bounds = bundle.capping_bounds
        n_capped = bundle.n_capped

        emit({
            "type": "start",
            "window": window,
            "horizon": horizon,
            "config": config,
            "feature_cols": feature_cols,
            "device": device.type,
            "split": {
                "train_rows": bundle.split_sizes["train_rows"],
                "test_rows": bundle.split_sizes["test_rows"],
                "train_samples": bundle.split_sizes["train_samples"],
                "test_samples": bundle.split_sizes["test_samples"],
            },
            "preprocessing": {
                "capping_bounds": {k: list(v) for k, v in capping_bounds.items()},
                "n_capped": {"train": n_capped["train"], "test": n_capped["test"]},
            },
        })

        # -------------------------------------------------------------
        # 6. Training — 1 model, config fixed (TIDAK ada sampling/seleksi)
        # -------------------------------------------------------------
        torch.manual_seed(seed)
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

        train_ds = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train))
        test_ds = TensorDataset(torch.from_numpy(X_test), torch.from_numpy(y_test))
        train_loader = DataLoader(train_ds, batch_size=config["batch_size"], shuffle=True)
        test_loader = DataLoader(test_ds, batch_size=config["batch_size"], shuffle=False)

        final_test_acc = 0.0
        final_test_f1 = 0.0

        for epoch in range(1, config["epochs"] + 1):
            train_loss, train_acc = _train_one_epoch(model, train_loader, optimizer, criterion, device)
            test_loss, test_acc, test_f1, _, _ = _evaluate_epoch(model, test_loader, criterion, device)

            final_test_acc = test_acc
            final_test_f1 = test_f1

            emit({
                "type": "epoch",
                "epoch": epoch,
                "total_epochs": config["epochs"],
                "train_loss": _r6(train_loss),
                "train_acc": _r6(train_acc),
                "test_loss": _r6(test_loss),
                "test_acc": _r6(test_acc),
                "test_f1": _r6(test_f1),
            })

        # -------------------------------------------------------------
        # 7. Evaluasi final di TEST (HANYA 4 metrik, sesuai Batasan Masalah)
        # -------------------------------------------------------------
        model.eval()
        X_test_t = torch.from_numpy(X_test).to(device)
        with torch.no_grad():
            test_logits = model(X_test_t)
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
        # 8. Simpan artefak — MENIMPA file resmi varian (sama nama dengan
        #    Random Search), sesuai tujuan fitur "retrain ulang".
        # -------------------------------------------------------------
        artifact_path_dir = Path(artifact_dir)
        artifact_path_dir.mkdir(parents=True, exist_ok=True)

        model_path = artifact_path_dir / model_filename
        scaler_path = artifact_path_dir / scaler_filename
        metadata_path = artifact_path_dir / metadata_filename

        state_dict = deepcopy({k: v.detach().cpu().clone() for k, v in model.state_dict().items()})
        torch.save({
            "model_state_dict": state_dict,
            "config": config,
            "feature_cols": feature_cols,
            "window": window,
        }, model_path)
        joblib.dump(scaler, scaler_path)

        trained_at = datetime.now(timezone.utc).isoformat()
        metadata = {
            "config": config,
            "feature_cols": feature_cols,
            "window": window,
            "horizon": horizon,
            "metrics": metrics,
            "confusion_matrix": confusion,
            "best_val_f1": _r6(final_test_f1),
            "best_val_acc": _r6(final_test_acc),
            "eval_split": "test",
            "split_ratio": {"train": bundle.train_ratio, "val": bundle.val_ratio},
            "split_sizes": {
                "train_rows": bundle.split_sizes["train_rows"],
                "test_rows": bundle.split_sizes["test_rows"],
                "train_samples": bundle.split_sizes["train_samples"],
                "test_samples": bundle.split_sizes["test_samples"],
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
            "config": config,
            "final_test_f1": _r6(final_test_f1),
            "final_test_acc": _r6(final_test_acc),
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
    horizon: int = 1,
) -> dict[str, Any]:
    """Prediksi arah harga N-hari ke depan (`horizon`, default 1) dari window
    TERAKHIR data, pakai model terlatih (persisted). Window terakhir di-capping
    dgn bounds yang dihitung ulang dari df_train (`load_split_capped()`,
    konsisten dgn preprocessing training) SEBELUM di-scale — rasio split
    dibaca dari `metadata["split_ratio"]` (fallback 70/15/15 utk artefak lama
    sebelum field ini ada), WAJIB sama dgn rasio saat model dilatih (mis.
    80:20 utk model hasil Training Manual) supaya `df_train` yang dipakai
    menghitung ulang `capping_bounds` persis sama. `horizon` HARUS sama
    dengan yang dipakai saat training model ini (caller bertanggung jawab
    mengirim nilai yang konsisten — tidak disimpan/divalidasi otomatis dari
    artefak). Return `{"trained": False}` kalau belum pernah training."""
    loaded = load_trained_notebook07(
        artifact_dir=artifact_dir,
        model_filename=model_filename,
        scaler_filename=scaler_filename,
        metadata_filename=metadata_filename,
    )
    if loaded is None:
        return {"trained": False}

    window = loaded["window"]
    split_ratio = loaded["metadata"].get("split_ratio", {"train": 0.70, "val": 0.15})
    df_train, _, _, capping_bounds, _ = load_split_capped(
        load_data_fn, capping_cols, horizon,
        train_ratio=split_ratio["train"], val_ratio=split_ratio["val"],
    )

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
    target_str = (as_of_date + pd.Timedelta(days=horizon)).strftime("%Y-%m-%d")

    model = loaded["model"]
    with torch.no_grad():
        logits = model(torch.tensor(X, dtype=torch.float32))
        probs = torch.softmax(logits, dim=1).numpy()[0]

    p_up = float(probs[1])
    threshold = loaded["metadata"].get("threshold", 0.5)
    direction = "up" if p_up >= threshold else "down"
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
    horizon: int = 1,
) -> dict[str, Any]:
    """Jalankan model terlatih di data historis (split + capping yang SAMA
    seperti training — reuse `load_split_capped()`, scaler TIDAK di-fit ulang;
    windowing pakai `_make_windows()` punya modul ini, BUKAN `create_sequences`
    notebook05) dan kembalikan prediksi-vs-aktual per-titik + metrik (HANYA 4:
    accuracy/precision/recall/f1, sesuai Batasan Masalah BAB I — TIDAK ada F2/AUC
    supaya konsisten dengan apa yang dihitung `run_notebook07_training()`).
    Rasio split dibaca dari `metadata["split_ratio"]` (fallback 70/15/15 utk
    artefak lama) supaya `df_train/df_val/df_test` yang di-re-split PERSIS
    sama dengan saat model dilatih — mis. model hasil Training Manual (80:20)
    punya `df_val` kosong, jadi `split="val"` akan mengembalikan `n_samples=0`
    utk model itu (bukan error). `horizon` HARUS sama dengan yang dipakai saat
    training model ini. Return `{"trained": False}` kalau belum pernah
    training."""
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

    split_ratio = loaded["metadata"].get("split_ratio", {"train": 0.70, "val": 0.15})
    df_train, df_val, df_test, _, _ = load_split_capped(
        load_data_fn, capping_cols, horizon,
        train_ratio=split_ratio["train"], val_ratio=split_ratio["val"],
    )
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

    threshold = loaded["metadata"].get("threshold", 0.5)
    y_int = y_seq.astype(int)
    pred_int = (probs >= threshold).astype(int)

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
