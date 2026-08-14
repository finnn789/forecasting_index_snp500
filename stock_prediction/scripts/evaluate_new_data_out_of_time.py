"""scripts/evaluate_new_data_out_of_time.py — Uji generalisasi temporal
(out-of-time) model FinBERT-LSTM resmi (`finbert_lstm_skripsi.*`, dilatih
MURNI dari data 2018-2024, TIDAK di-retrain) terhadap data scraping baru
2026-06-12 s/d 2026-07-30 (`scripts/new_data_output/new_return_features_stationary.csv`,
hasil `process_new_scraped_data.py`).

Tujuan: menjawab pertanyaan dosen pembimbing — "seberapa efektif model kalau
data 2018-2024 dipakai training, tapi diuji ke data terbaru 2026?" — sebagai
angka konkret (Accuracy/Precision/Recall/F1) di data yang model BELUM PERNAH
lihat sama sekali, dibandingkan metrik test-set asli (2018-2024) dan baseline
trivial (majority/persistence) di data baru yang SAMA.

Reuse penuh komponen produksi (TIDAK reimplement):
  - models/lstm/notebook07_common.py: load_split_capped, apply_capping,
    _make_windows, load_trained_notebook07
  - pipeline/feature_engineering/dataset_builder.py: load_return_features,
    RETURN_FEATURE_COLS_B (fitur resmi Model B)
  - models/lstm/notebook07_trainer.py: FINBERT_FILES, ARTIFACT_DIR (nama
    artefak resmi)

TIDAK menyentuh data/model resmi — hanya membaca artefak model (read-only)
dan file baru di scripts/new_data_output/ (read-only).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score

ROOT = Path("E:/forecasting_index_snp500/stock_prediction")
sys.path.insert(0, str(ROOT))
import os

os.chdir(ROOT)

from models.lstm.notebook07_common import apply_capping, _make_windows, load_split_capped, load_trained_notebook07
from models.lstm.notebook07_trainer import ARTIFACT_DIR, FINBERT_FILES, RETURN_HORIZON
from pipeline.feature_engineering.dataset_builder import RETURN_FEATURE_COLS_B, load_return_features

NEW_DATA_CSV = ROOT / "scripts/new_data_output/new_return_features_stationary.csv"
WINDOW = 20


def main() -> None:
    print("=" * 70)
    print("STEP 1: Load model resmi FinBERT-LSTM (2018-2024, TIDAK di-retrain)")
    print("=" * 70)
    loaded = load_trained_notebook07(
        artifact_dir=ARTIFACT_DIR,
        model_filename=FINBERT_FILES["model"],
        scaler_filename=FINBERT_FILES["scaler"],
        metadata_filename=FINBERT_FILES["metadata"],
    )
    if loaded is None:
        print("Model belum pernah dilatih — jalankan training dulu.")
        return

    feature_cols = loaded["feature_cols"]
    threshold = loaded["metadata"].get("threshold", 0.5)
    test_metrics_2018_2024 = loaded["metadata"].get("metrics")
    print(f"feature_cols  : {feature_cols}")
    print(f"window        : {loaded['window']}")
    print(f"threshold     : {threshold}")
    print(f"trained_at    : {loaded['metadata'].get('trained_at')}")
    print(f"test-set metrics (2018-2024): {test_metrics_2018_2024}")

    print()
    print("=" * 70)
    print("STEP 2: Hitung ulang capping bounds dari df_train RESMI (2018-2024)")
    print("=" * 70)
    split_ratio = loaded["metadata"].get("split_ratio", {"train": 0.70, "val": 0.15})
    df_train, _, _, capping_bounds, _ = load_split_capped(
        load_return_features, RETURN_FEATURE_COLS_B, RETURN_HORIZON,
        train_ratio=split_ratio["train"], val_ratio=split_ratio["val"],
    )
    print(f"df_train rows : {len(df_train)}  (bounds dihitung IQR fit-train-only, sama seperti saat training)")

    print()
    print("=" * 70)
    print("STEP 3: Load data baru 2026 + label horizon=%d (Close[t+%d] > Close[t])" % (RETURN_HORIZON, RETURN_HORIZON))
    print("=" * 70)
    df_new = pd.read_csv(NEW_DATA_CSV, parse_dates=["Date"])
    df_new["label"] = (df_new["Close"].shift(-RETURN_HORIZON) > df_new["Close"]).astype("int64")
    df_new = df_new.iloc[:-RETURN_HORIZON].copy().reset_index(drop=True)
    print(f"Baris data baru (setelah label horizon=5, buang 5 baris terakhir tanpa aktual): {len(df_new)}")
    print(f"Rentang: {df_new['Date'].min().date()} s/d {df_new['Date'].max().date()}")
    print(f"Distribusi label (1=up): {df_new['label'].value_counts().to_dict()}")

    df_new_capped = apply_capping(df_new, capping_bounds)
    n_capped = {
        col: int(((df_new[col] < lo) | (df_new[col] > hi)).sum())
        for col, (lo, hi) in capping_bounds.items()
    }
    print(f"Jumlah nilai yang ter-capping (di luar IQR bounds train 2018-2024): {n_capped}")

    print()
    print("=" * 70)
    print(f"STEP 4: Scale (scaler resmi, TIDAK di-fit ulang) + windowing (window={WINDOW})")
    print("=" * 70)
    X_scaled = loaded["scaler"].transform(df_new_capped[feature_cols].values.astype(np.float64))
    y_labels = df_new_capped["label"].values.astype(np.int64)
    X_seq, y_seq = _make_windows(X_scaled, y_labels, WINDOW)
    dates_seq = df_new_capped["Date"].iloc[WINDOW - 1:].dt.strftime("%Y-%m-%d").tolist()
    print(f"Jumlah sampel windowed yang bisa dievaluasi: {len(X_seq)}")

    if len(X_seq) == 0:
        print("Tidak cukup data untuk membentuk 1 sampel windowed pun. Berhenti.")
        return

    print()
    print("=" * 70)
    print("STEP 5: Inferensi (forward pass murni, model TIDAK dilatih ulang)")
    print("=" * 70)
    model = loaded["model"]
    with torch.no_grad():
        logits = model(torch.tensor(X_seq, dtype=torch.float32))
        probs_up = torch.softmax(logits, dim=1).numpy()[:, 1]
    pred_int = (probs_up >= threshold).astype(int)
    y_int = y_seq.astype(int)

    print(f"{'Tanggal':<12}{'Aktual':<8}{'Prediksi':<10}{'Prob.Up':<10}{'Benar?'}")
    for i in range(len(dates_seq)):
        actual = "UP" if y_int[i] == 1 else "DOWN"
        pred = "UP" if pred_int[i] == 1 else "DOWN"
        correct = "Ya" if pred_int[i] == y_int[i] else "Tidak"
        print(f"{dates_seq[i]:<12}{actual:<8}{pred:<10}{probs_up[i]:<10.4f}{correct}")

    print()
    print("=" * 70)
    print("STEP 6: Metrik out-of-time (data 2026, model 2018-2024, tanpa retrain)")
    print("=" * 70)
    metrics_ood = {
        "accuracy": float(accuracy_score(y_int, pred_int)),
        "precision": float(precision_score(y_int, pred_int, zero_division=0)),
        "recall": float(recall_score(y_int, pred_int, zero_division=0)),
        "f1": float(f1_score(y_int, pred_int, zero_division=0)),
    }
    tn, fp, fn, tp = confusion_matrix(y_int, pred_int, labels=[0, 1]).ravel()
    print(f"n_samples  : {len(y_int)}")
    print(f"metrics    : {metrics_ood}")
    print(f"confusion  : tp={tp} tn={tn} fp={fp} fn={fn}")

    up_rate = float(y_int.mean())
    majority_baseline = max(up_rate, 1 - up_rate)
    label_series = pd.Series(y_int)
    persistence_baseline = float((label_series == label_series.shift(1)).mean())
    print()
    print(f"Baseline majority (data baru, sama)   : {majority_baseline:.4f}  (up_rate={up_rate:.4f})")
    print(f"Baseline persistence (data baru, sama): {persistence_baseline:.4f}")

    print()
    print("=" * 70)
    print("RINGKASAN BANDING")
    print("=" * 70)
    print(f"{'Metrik':<12}{'Test 2018-2024':<18}{'Out-of-time 2026'}")
    if test_metrics_2018_2024:
        for k in ["accuracy", "precision", "recall", "f1"]:
            print(f"{k:<12}{test_metrics_2018_2024.get(k, float('nan')):<18.4f}{metrics_ood[k]:.4f}")
    print()
    print(f"n_samples test 2018-2024: {loaded['metadata'].get('split_sizes', {}).get('test_samples')}")
    print(f"n_samples out-of-time 2026: {len(y_int)}  <-- SANGAT KECIL, interpretasikan sebagai indikasi awal, bukan kesimpulan statistik kuat")


if __name__ == "__main__":
    main()
