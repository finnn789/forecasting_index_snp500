"""
app/services/prediction_service.py — Business logic untuk prediksi arah harga.

Import DirectionPredictor secara LAZY (di dalam fungsi) agar torch tidak
di-import saat module load — verifikasi route tetap jalan walau model belum ada.
"""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import NotFoundError
from app.helpers.serialization import format_iso_date
from app.repositories.provider import get_repositories
from app.schemas.prediction import (
    BacktestPoint,
    BacktestResponse,
    ConfusionMatrix,
    DirectionPredictionResponse,
    ModelInfoResponse,
)

_ARTIFACT_DIR = Path("data/artifacts/lstm_weights")


def get_model_status() -> ModelInfoResponse:
    """
    Cek ketersediaan artefak model LSTM.
    Jika metadata.json ada → is_available=True, isi field dari file.
    Jika tidak ada → is_available=False, artifact_path saja.
    """
    artifact_path = str(_ARTIFACT_DIR)
    artifact_repo = get_repositories()["artifact"]

    if not artifact_repo.metadata_path().exists():
        return ModelInfoResponse(
            is_available=False,
            artifact_path=artifact_path,
        )

    try:
        meta = artifact_repo.load_metadata()
    except Exception:
        return ModelInfoResponse(
            is_available=False,
            artifact_path=artifact_path,
        )

    return ModelInfoResponse(
        is_available=True,
        artifact_path=artifact_path,
        window=meta.get("window"),
        features_used=meta.get("feature_cols", []),
        n_features=meta.get("n_features"),
        metrics=meta.get("metrics"),
        trained_at=meta.get("trained_at"),
    )


def predict_direction(ticker: str = "GSPC") -> DirectionPredictionResponse:
    """
    Jalankan prediksi arah harga untuk ticker yang diberikan.

    Import DirectionPredictor secara lazy agar torch tidak di-import saat
    module load — route tetap dapat di-register meski model belum dilatih.

    Raises:
        NotFoundError: Jika model belum tersedia (belum dilatih).
    """
    # Lazy import — torch hanya di-load saat endpoint ini benar-benar dipanggil.
    from models.lstm.lstm_predictor import DirectionPredictor  # noqa: PLC0415

    predictor = DirectionPredictor(artifact_dir=str(_ARTIFACT_DIR))

    if not predictor.is_available:
        raise NotFoundError(
            "Model LSTM belum tersedia. Latih model terlebih dahulu.",
            code="MODEL_NOT_TRAINED",
            detail=f"Artefak tidak ditemukan di {_ARTIFACT_DIR}",
        )

    result = predictor.predict_latest()

    # Baca metadata untuk field window & features_used
    window: int = 20
    features_used: list[str] = []
    trained_at: str | None = None

    artifact_repo = get_repositories()["artifact"]
    if artifact_repo.metadata_path().exists():
        try:
            meta = artifact_repo.load_metadata()
            window = meta.get("window", 20)
            features_used = meta.get("feature_cols", [])
            trained_at = meta.get("trained_at")
        except Exception:
            pass

    return DirectionPredictionResponse(
        ticker=ticker,
        as_of_date=result["as_of_date"],
        target_date=result["target_date"],
        direction=result["direction"],
        probability_up=result["probability_up"],
        confidence=result["confidence"],
        window=window,
        features_used=features_used,
        model_version=trained_at,
    )


def run_backtest(split: str = "test") -> BacktestResponse:
    """
    Jalankan model LSTM di data historis dan kembalikan pasangan prediksi-vs-aktual
    beserta metrik evaluasi.

    Args:
        split: Split data yang digunakan. Hanya "test" dan "val" yang didukung.
               Jika split="val", DatasetBundle tidak menyediakan val_dates sehingga
               fungsi ini mengembalikan error; default dan rekomendasi adalah "test".

    Returns:
        BacktestResponse berisi points (per tanggal), metrics, confusion_matrix.

    Raises:
        NotFoundError: Jika model belum tersedia (artefak tidak ditemukan).
        NotFoundError: Jika split tidak dikenali.
    """
    # Lazy import — torch dan sklearn hanya di-load saat endpoint dipanggil.
    import numpy as np  # noqa: PLC0415
    from sklearn.metrics import (  # noqa: PLC0415
        accuracy_score,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    from models.lstm.lstm_predictor import DirectionPredictor  # noqa: PLC0415
    from pipeline.feature_engineering.dataset_builder import build_dataset, load_joined  # noqa: PLC0415

    # Hanya split "test" yang didukung saat ini karena DatasetBundle tidak
    # menyediakan val_dates — untuk menghindari bug silent, tolak "val" secara eksplisit.
    if split not in ("test", "val"):
        raise NotFoundError(
            f"Split '{split}' tidak dikenali. Gunakan 'test'.",
            code="INVALID_SPLIT",
        )

    # Pastikan model tersedia
    predictor = DirectionPredictor(artifact_dir=str(_ARTIFACT_DIR))
    if not predictor.is_available:
        raise NotFoundError(
            "Model LSTM belum tersedia. Latih model terlebih dahulu.",
            code="MODEL_NOT_TRAINED",
            detail=f"Artefak tidak ditemukan di {_ARTIFACT_DIR}",
        )

    # Baca window dari metadata
    meta = get_repositories()["artifact"].load_metadata()
    window: int = meta.get("window", 20)
    ticker = "GSPC"

    # Bangun dataset — gunakan scaler yang di-fit dari training agar anti-leakage
    bundle = build_dataset(window=window)

    if split == "test":
        X = bundle.X_test
        y = bundle.y_test
        dates = bundle.test_dates
    else:
        # split == "val": DatasetBundle tidak punya val_dates, fallback ke test
        # Sesuai instruksi: "kalau DatasetBundle belum punya val_dates, dukung
        # split='test' saja" → tolak val dengan pesan yang jelas.
        raise NotFoundError(
            "Split 'val' belum didukung karena DatasetBundle tidak menyediakan val_dates. "
            "Gunakan split='test'.",
            code="SPLIT_NOT_SUPPORTED",
        )

    if len(X) == 0:
        raise NotFoundError(
            f"Tidak ada data untuk split '{split}'.",
            code="EMPTY_SPLIT",
        )

    # Inferensi — predict_proba menerima (B, W, F) yang sudah di-scale
    probs: np.ndarray = predictor.predict_proba(X).flatten()

    # Mapping label ke arah
    y_int = y.astype(int)
    pred_int = (probs >= 0.5).astype(int)

    actual_dirs: list[str] = ["up" if v == 1 else "down" for v in y_int]
    pred_dirs: list[str] = ["up" if v == 1 else "down" for v in pred_int]

    # Buat peta Date → Close dari joined dataframe
    df_joined = load_joined()
    date_to_close: dict[str, float] = {
        format_iso_date(row["Date"]): float(row["Close"])
        for _, row in df_joined.iterrows()
    }

    # Bangun list BacktestPoint
    points: list[BacktestPoint] = []
    for i, date_str in enumerate(dates):
        close_val = date_to_close.get(date_str, 0.0)
        points.append(
            BacktestPoint(
                date=date_str,
                close=close_val,
                actual_direction=actual_dirs[i],  # type: ignore[arg-type]
                predicted_direction=pred_dirs[i],  # type: ignore[arg-type]
                probability_up=round(float(probs[i]), 6),
                correct=bool(pred_int[i] == y_int[i]),
            )
        )

    # Hitung metrik — handle edge case bila hanya satu kelas hadir
    try:
        auc = float(roc_auc_score(y_int, probs))
    except ValueError:
        auc = float("nan")

    metrics = {
        "accuracy": round(float(accuracy_score(y_int, pred_int)), 6),
        "precision": round(float(precision_score(y_int, pred_int, zero_division=0)), 6),
        "recall": round(float(recall_score(y_int, pred_int, zero_division=0)), 6),
        "f1": round(float(f1_score(y_int, pred_int, zero_division=0)), 6),
        "auc": round(auc, 6),
    }

    # Confusion matrix: positif = "up" (label 1)
    tp = int(np.sum((y_int == 1) & (pred_int == 1)))
    tn = int(np.sum((y_int == 0) & (pred_int == 0)))
    fp = int(np.sum((y_int == 0) & (pred_int == 1)))
    fn = int(np.sum((y_int == 1) & (pred_int == 0)))

    return BacktestResponse(
        ticker=ticker,
        window=window,
        split=split,
        n_samples=len(points),
        metrics=metrics,
        confusion_matrix=ConfusionMatrix(tp=tp, tn=tn, fp=fp, fn=fn),
        points=points,
    )
