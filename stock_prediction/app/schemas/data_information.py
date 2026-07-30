"""
app/schemas/data_information.py — Response schemas untuk app/api/v1/routes_data_information.py.

Mengekspos temuan diagnostik notebooks/11_diagnostic_data_analysis_horizon.ipynb
(kenapa model prediksi arah collapse/bias) sebagai data live untuk tab "Data
Information" di ui-stock-prediction. Setiap endpoint menghitung ULANG dari data
mentah (bukan angka statis) memakai logic yang sama dengan notebook 11.
"""

from typing import Literal

from pydantic import BaseModel

from app.schemas.data_analysis import Histogram

ModelKey = Literal["ohlcv", "joined"]
Horizon = Literal[1, 5]
SplitName = Literal["train", "val", "test"]


# ---------------------------------------------------------------------------
# 1. Regime overview — pergeseran pola pasar antar periode
# ---------------------------------------------------------------------------

class ClosePoint(BaseModel):
    date: str
    close: float


class SplitPeriodSummary(BaseModel):
    split: SplitName
    date_start: str
    date_end: str
    price_start: float
    price_end: float
    change_pct: float
    price_min: float
    price_max: float
    up_pct: float
    n_rows: int


class RegimeOverviewResponse(BaseModel):
    model: ModelKey
    horizon: Horizon
    points: list[ClosePoint]
    splits: list[SplitPeriodSummary]
    note: str = (
        "Split kronologis 70/15/15 kebetulan membelah data jadi 3 periode dengan "
        "arah pasar berbeda. Perubahan harga (change_pct) dan Up% label per periode "
        "menunjukkan seberapa jauh periode validasi berbeda dari periode latih/uji."
    )
    plot_hint: str = (
        "line chart harga penutupan dengan 3 area berwarna (latih/validasi/uji) — "
        "x: tanggal, y: harga penutupan"
    )


# ---------------------------------------------------------------------------
# 2. Label balance — distribusi arah naik/turun per periode
# ---------------------------------------------------------------------------

class SplitLabelBalance(BaseModel):
    split: SplitName
    n: int
    up_pct: float
    down_pct: float


class ModelLabelBalance(BaseModel):
    model: ModelKey
    model_label: str
    splits: list[SplitLabelBalance]


class RollingUpPoint(BaseModel):
    date: str
    rolling_up_pct: float | None


class LabelBalanceResponse(BaseModel):
    horizon: Horizon
    models: list[ModelLabelBalance]
    rolling: list[RollingUpPoint]
    rolling_window: int = 60
    note: str = (
        "Up% dihitung dari label arah (naik jika harga penutupan hari target lebih "
        "tinggi dari hari ini). rolling_up_pct memakai jendela bergerak "
        f"agar terlihat KAPAN pergeseran pola pasar terjadi, bukan cuma angka rata-rata per periode."
    )
    plot_hint: str = "bar chart Up%/Down% per periode + line chart Up% bergerak sepanjang waktu"


# ---------------------------------------------------------------------------
# 3. Scaling range — nilai di luar jangkauan data latihan
# ---------------------------------------------------------------------------

class FeatureScalingInfo(BaseModel):
    feature: str
    train_min: float
    train_max: float
    val_pct_out_of_range: float
    test_pct_out_of_range: float
    val_scaled_min: float
    val_scaled_max: float
    test_scaled_min: float
    test_scaled_max: float


class ScaledClosePoint(BaseModel):
    date: str
    close_scaled: float
    split: SplitName


class ScalingRangeResponse(BaseModel):
    model: ModelKey
    horizon: Horizon
    features: list[FeatureScalingInfo]
    close_series: list[ScaledClosePoint]
    note: str = (
        "Normalisasi (MinMaxScaler) dipasang HANYA dari data latih (metodologi yang "
        "benar, mencegah kebocoran data). Karena harga terus mencetak rekor baru, "
        "sebagian baris data validasi/uji bernilai di luar jangkauan [0, 1] setelah "
        "dinormalisasi — artinya model melihat bentuk data yang belum pernah "
        "ditemui saat pelatihan."
    )
    plot_hint: str = (
        "line chart harga penutupan ternormalisasi dengan garis batas 0 dan 1 — "
        "titik di luar garis batas = di luar jangkauan data latihan"
    )


# ---------------------------------------------------------------------------
# 4. Feature-label correlation — arah hubungan yang berbalik
# ---------------------------------------------------------------------------

class FeatureCorrelationRow(BaseModel):
    feature: str
    train_r: float
    val_r: float
    test_r: float
    reversed_direction: bool


class FeatureLabelCorrelationResponse(BaseModel):
    model: ModelKey
    horizon: Horizon
    rows: list[FeatureCorrelationRow]
    note: str = (
        "Nilai korelasi (r) menunjukkan arah hubungan antara suatu fitur dengan arah "
        "pergerakan harga (naik/turun). Kalau tandanya berbalik antara periode latih "
        "dan periode uji (reversed_direction = true), pola yang dipelajari model dari "
        "data latih justru terbalik saat diuji — salah satu penyebab utama prediksi meleset."
    )
    plot_hint: str = "tabel korelasi per fitur x per periode, baris dengan arah berbalik ditandai warna"


# ---------------------------------------------------------------------------
# 5. Sentiment lag correlation — sentimen berita reaktif, bukan memimpin harga
# ---------------------------------------------------------------------------

class LagCorrelationPoint(BaseModel):
    lag_days: int
    r: float
    p_value: float


class SentimentLagCorrelationResponse(BaseModel):
    overall: list[LagCorrelationPoint]
    train: list[LagCorrelationPoint]
    val: list[LagCorrelationPoint]
    test: list[LagCorrelationPoint]
    note: str = (
        "lag_days=0 berarti skor sentimen berita dibandingkan dengan perubahan harga "
        "PADA HARI YANG SAMA; lag_days=1..10 berarti dibandingkan dengan perubahan "
        "harga BEBERAPA HARI SETELAHNYA. Korelasi yang tinggi hanya di lag_days=0 dan "
        "nyaris nol di lag_days lainnya berarti skor sentimen bersifat reaktif "
        "(mengikuti harga yang sudah terjadi), bukan sinyal yang bisa memimpin/"
        "memprediksi pergerakan harga berikutnya."
    )
    plot_hint: str = "line/bar chart korelasi vs jarak hari (lag_days 0-10), overall & per periode"


# ---------------------------------------------------------------------------
# 6. Baseline comparison — model vs pembanding sederhana
# ---------------------------------------------------------------------------

class BaselineComparisonRow(BaseModel):
    model: ModelKey
    model_label: str
    horizon: Horizon
    split: SplitName
    n: int
    majority_baseline_acc: float
    persistence_baseline_acc: float
    model_trained: bool
    model_accuracy: float | None
    model_precision: float | None
    model_recall: float | None
    model_f1: float | None


class BaselineComparisonResponse(BaseModel):
    rows: list[BaselineComparisonRow]
    note: str = (
        "majority_baseline_acc = akurasi kalau selalu menebak kelas mayoritas "
        "(naik atau turun, mana yang lebih sering). persistence_baseline_acc = "
        "akurasi kalau selalu menebak arah hari ini sama dengan arah hari "
        "sebelumnya. Metrik model sungguhan (model_accuracy dkk) hanya tersedia "
        "untuk periode uji (test) karena itulah yang dievaluasi & disimpan saat "
        "pelatihan. Kalau model tidak mengungguli kedua baseline ini, model belum "
        "menemukan pola yang berguna."
    )
    plot_hint: str = "tabel perbandingan akurasi model vs baseline sederhana, per model/horizon/periode"


# ---------------------------------------------------------------------------
# 7. (opsional) Distribution drift — uji perbedaan distribusi (KS-test)
# ---------------------------------------------------------------------------

class FeatureDriftRow(BaseModel):
    feature: str
    ks_statistic: float
    p_value: float
    significant: bool


class FeatureHistogramPair(BaseModel):
    feature: str
    train: Histogram
    test: Histogram


class DistributionDriftResponse(BaseModel):
    model: ModelKey
    horizon: Horizon
    rows: list[FeatureDriftRow]
    histograms: list[FeatureHistogramPair]
    note: str = (
        "Uji statistik perbedaan distribusi (Kolmogorov-Smirnov / KS-test) "
        "membandingkan bentuk sebaran nilai suatu fitur antara periode latih dan "
        "periode uji. significant=true (p_value < 0.01) berarti perbedaannya "
        "signifikan secara statistik — bukan kebetulan — sehingga data uji memang "
        "berasal dari kondisi pasar yang berbeda dari data latih."
    )
    plot_hint: str = "tabel KS-statistic + p-value per fitur, histogram overlay latih vs uji"
