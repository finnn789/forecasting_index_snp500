# Frontend API Reference — Stock Prediction System

> Dokumen ini dihasilkan dengan memanggil setiap endpoint secara langsung via
> FastAPI TestClient dan mencatat respons nyata. Shape dan nilai contoh bersumber
> dari eksekusi aktual, bukan dari schema saja.
>
> Terakhir diperbarui: 2026-06-11

---

## Bagian Umum

### Base URL

| Environment | URL |
|---|---|
| Local Development | `http://localhost:8000` |
| Network Access | `http://0.0.0.0:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |

Semua endpoint berada di bawah prefix `/api` (status/health) atau `/api/v1` (semua endpoint fungsional).

---

### Struktur Envelope (Semua Respons)

Setiap respons — sukses maupun error — dibungkus dalam envelope standar yang didefinisikan di `app/schemas/base.py`. Handler route **tidak** membungkus manual; pembungkusan dilakukan otomatis oleh `EnvelopeRoute` (kecuali endpoint `/api/health` dan `/api/status` yang membungkus secara eksplisit).

#### Success Envelope

```json
{
  "success": true,
  "message": "Pesan singkat operasi",
  "meta": {
    "timestamp": "2026-06-11T12:02:15.567928Z",
    "version": "1.0",
    "pagination": null
  },
  "data": { ... }
}
```

Field `meta.pagination` selalu `null` untuk endpoint non-paginated. Untuk endpoint paginated (jika ada), `meta.pagination` berisi:

```json
{
  "page": 1,
  "page_size": 20,
  "total_items": 100,
  "total_pages": 5
}
```

#### Error Envelope

```json
{
  "success": false,
  "message": "",
  "meta": {
    "timestamp": "2026-06-11T12:07:19.075Z",
    "version": "1.0",
    "pagination": null
  },
  "error": {
    "code": "HTTP_404",
    "message": "Not Found",
    "detail": null
  }
}
```

`error.code` menggunakan format `SCREAMING_SNAKE_CASE`. Contoh kode error yang mungkin: `HTTP_404`, `NOT_FOUND`, `MODEL_NOT_LOADED`, `TICKER_NOT_FOUND`.

---

### Catatan Penting untuk Konsumen API

- **Akses `data`**: Selalu baca nilai dari `response.data`, bukan dari root response.
- **Format timestamp**: ISO 8601 UTC, contoh: `"2026-06-11T12:02:15.567928Z"`. Gunakan `new Date(ts)` di JavaScript.
- **Array panjang**: Endpoint `/data/eda/stocks/time-series`, `/data/eda/stocks/daily-returns`, `/data/eda/stocks/drawdown` mengembalikan ~1.552 titik data (seluruh seri historis 2018–2024). Pertimbangkan downsampling di sisi frontend untuk performa rendering.
- **Error 404**: Terjadi ketika data atau model tidak tersedia (bukan karena path salah). Contoh: model LSTM belum dilatih.
- **Endpoint raw stocks**: `/data/eda/stocks/raw` mengembalikan 10 baris terakhir saja (bukan seluruh dataset).
- **Pagination manual** (sentiment preview): Gunakan query params `page` dan `page_size`. Field pagination tidak ada di `meta.pagination` — total rows tersedia di `data.total_rows`.

---

## Endpoint: Status & Health

### GET /api/health

**Tujuan:** Liveness probe ringan. Cocok untuk Docker health check atau Kubernetes readiness probe.

**Query params:** Tidak ada

**Envelope:** `SuccessResponse` standar

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `status` | `string` | Selalu `"ok"` jika server hidup |
| `message` | `string` | Pesan deskriptif: `"Service is running normally."` |

**Contoh respons:**

```json
{
  "success": true,
  "message": "Service is healthy",
  "meta": {
    "timestamp": "2026-06-11T12:02:15.567928Z",
    "version": "1.0",
    "pagination": null
  },
  "data": {
    "status": "ok",
    "message": "Service is running normally."
  }
}
```

**Saran visual:** Tidak perlu chart. Gunakan untuk indikator koneksi (badge hijau/merah).

---

### GET /api/status

**Tujuan:** Status lengkap layanan termasuk uptime, versi Python, dan platform OS.

**Query params:** Tidak ada

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `status` | `string` | `"healthy"` jika normal |
| `uptime_seconds` | `number` | Detik sejak server startup |
| `timestamp` | `string` | Waktu saat ini (ISO 8601 UTC) |
| `python_version` | `string` | Versi Python runtime, mis. `"3.12.3"` |
| `platform` | `string` | Informasi OS lengkap |

**Contoh respons:**

```json
{
  "success": true,
  "message": "Service status retrieved",
  "meta": {
    "timestamp": "2026-06-11T12:02:15.570878Z",
    "version": "1.0",
    "pagination": null
  },
  "data": {
    "status": "healthy",
    "uptime_seconds": 0.0,
    "timestamp": "2026-06-11T12:02:15.569753+00:00",
    "python_version": "3.12.3",
    "platform": "Linux-6.14.0-37-generic-x86_64-with-glibc2.39"
  }
}
```

**Saran visual:** Card metrik kecil dengan `uptime_seconds` diformat ke hh:mm:ss.

---

## Endpoint: Prediction

### GET /api/v1/predict/model/status

**Tujuan:** Cek apakah model LSTM sudah tersedia dan metadata training-nya. Gunakan sebelum memanggil `/predict` untuk memverifikasi model siap.

**Query params:** Tidak ada

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `is_available` | `boolean` | `true` jika artefak model lengkap |
| `artifact_path` | `string` | Path direktori artefak LSTM |
| `window` | `integer \| null` | Panjang lookback window (default 20) |
| `features_used` | `string[]` | Kolom fitur yang digunakan saat training |
| `n_features` | `integer \| null` | Jumlah fitur (6) |
| `metrics` | `object \| null` | Metrik evaluasi dari training (lihat di bawah) |
| `trained_at` | `string \| null` | Waktu training selesai (ISO 8601) |

`metrics` object:

| Field | Tipe | Keterangan |
|---|---|---|
| `val_acc` | `number` | Accuracy di validation set |
| `val_f1` | `number` | F1-score di validation set |
| `val_auc` | `number` | AUC-ROC di validation set |
| `test_acc` | `number` | Accuracy di test set |
| `test_f1` | `number` | F1-score di test set |
| `test_auc` | `number` | AUC-ROC di test set |

**Contoh respons:**

```json
{
  "success": true,
  "message": "Status model prediksi berhasil dimuat",
  "meta": {
    "timestamp": "2026-06-11T12:02:25.171642Z",
    "version": "1.0",
    "pagination": null
  },
  "data": {
    "is_available": true,
    "artifact_path": "data/artifacts/lstm_weights",
    "window": 20,
    "features_used": ["Open", "High", "Low", "Close", "Volume", "sentiment_mean"],
    "n_features": 6,
    "metrics": {
      "val_acc": 0.5466666666666666,
      "val_f1": 0.7068965517241379,
      "val_auc": 0.5148652957117806,
      "test_acc": 0.6086956521739131,
      "test_f1": 0.7567567567567568,
      "test_auc": 0.38095238095238093
    },
    "trained_at": "2026-06-11T11:44:11.567432+00:00"
  }
}
```

**Error 404:** Jika `data/artifacts/lstm_weights/metadata.json` tidak ada.

**Saran visual:** Card "Model Status" dengan badge `is_available`, tabel metrik (accuracy/F1/AUC untuk val dan test).

---

### POST /api/v1/predict

**Tujuan:** Prediksi arah harga S&P 500 hari berikutnya (naik/turun) menggunakan model LSTM + sentimen yang sudah dilatih.

**Request body:**

```json
{
  "ticker": "GSPC"
}
```

| Field | Tipe | Default | Keterangan |
|---|---|---|---|
| `ticker` | `string` | `"GSPC"` | Ticker saham. Saat ini hanya `"GSPC"` yang didukung (model dilatih untuk GSPC). Body kosong `{}` akan menggunakan default. |

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `ticker` | `string` | Ticker yang diprediksi |
| `as_of_date` | `string` | Tanggal data terakhir yang digunakan (YYYY-MM-DD) |
| `target_date` | `string` | Tanggal prediksi (hari bursa berikutnya) |
| `direction` | `"up" \| "down"` | Arah prediksi: naik atau turun |
| `probability_up` | `number` | Probabilitas harga naik [0.0–1.0] |
| `confidence` | `number` | max(probability_up, 1-probability_up) [0.5–1.0] |
| `window` | `integer` | Panjang window yang digunakan (20) |
| `features_used` | `string[]` | Fitur yang digunakan dalam inferensi |
| `model_version` | `string \| null` | Timestamp training model |

**Contoh respons:**

```json
{
  "success": true,
  "message": "Prediksi arah harga berhasil",
  "meta": {
    "timestamp": "2026-06-11T12:02:25.536491Z",
    "version": "1.0",
    "pagination": null
  },
  "data": {
    "ticker": "GSPC",
    "as_of_date": "2024-03-04",
    "target_date": "2024-03-05",
    "direction": "up",
    "probability_up": 0.529294,
    "confidence": 0.529294,
    "window": 20,
    "features_used": ["Open", "High", "Low", "Close", "Volume", "sentiment_mean"],
    "model_version": "2026-06-11T11:44:11.567432+00:00"
  }
}
```

**Error 404:** Jika model belum dilatih (artefak tidak ada).

**Saran visual:** Card prediksi dengan arah (panah atas/bawah), gauge `probability_up`, dan label `confidence`.

---

### GET /api/v1/predict/backtest

**Tujuan:** Jalankan model LSTM di data historis dan kembalikan perbandingan prediksi vs aktual per tanggal, beserta metrik evaluasi dan confusion matrix.

**Query params:**

| Param | Tipe | Default | Keterangan |
|---|---|---|---|
| `split` | `string` | `"test"` | Split data: hanya `"test"` yang didukung saat ini |

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `ticker` | `string` | Ticker yang dibacktest |
| `window` | `integer` | Panjang lookback window |
| `split` | `string` | Split yang digunakan (`"test"`) |
| `n_samples` | `integer` | Jumlah sampel dalam split |
| `metrics` | `object` | Metrik evaluasi (lihat di bawah) |
| `confusion_matrix` | `object` | Confusion matrix klasifikasi biner |
| `points` | `BacktestPoint[]` | Daftar titik prediksi per tanggal |

`metrics` object:

| Field | Tipe | Keterangan |
|---|---|---|
| `accuracy` | `number` | Akurasi keseluruhan |
| `precision` | `number` | Precision (kelas positif = "up") |
| `recall` | `number` | Recall (kelas positif = "up") |
| `f1` | `number` | F1-score |
| `auc` | `number` | AUC-ROC |

`confusion_matrix` object:

| Field | Tipe | Keterangan |
|---|---|---|
| `tp` | `integer` | True Positive (prediksi "up", aktual "up") |
| `tn` | `integer` | True Negative (prediksi "down", aktual "down") |
| `fp` | `integer` | False Positive (prediksi "up", aktual "down") |
| `fn` | `integer` | False Negative (prediksi "down", aktual "up") |

`BacktestPoint` object (satu elemen dalam `points`):

| Field | Tipe | Keterangan |
|---|---|---|
| `date` | `string` | Tanggal trading (YYYY-MM-DD) |
| `close` | `number` | Harga penutupan aktual |
| `actual_direction` | `"up" \| "down"` | Arah aktual (derived dari close berikutnya) |
| `predicted_direction` | `"up" \| "down"` | Prediksi model |
| `probability_up` | `number` | Probabilitas naik [0.0–1.0] |
| `correct` | `boolean` | Apakah prediksi benar |

**Contoh respons (points dipotong ke 2 elemen):**

```json
{
  "success": true,
  "message": "Backtest prediksi berhasil dimuat",
  "meta": {
    "timestamp": "2026-06-11T12:07:19.047503Z",
    "version": "1.0",
    "pagination": null
  },
  "data": {
    "ticker": "GSPC",
    "window": 20,
    "split": "test",
    "n_samples": 23,
    "metrics": {
      "accuracy": 0.608696,
      "precision": 0.608696,
      "recall": 1.0,
      "f1": 0.756757,
      "auc": 0.380952
    },
    "confusion_matrix": {
      "tp": 14,
      "tn": 0,
      "fp": 9,
      "fn": 0
    },
    "points": [
      {
        "date": "2024-01-30",
        "close": 4924.9702148438,
        "actual_direction": "down",
        "predicted_direction": "up",
        "probability_up": 0.52913,
        "correct": false
      },
      {
        "date": "2024-01-31",
        "close": 4845.6499023438,
        "actual_direction": "up",
        "predicted_direction": "up",
        "probability_up": 0.529121,
        "correct": true
      }
    ]
  }
}
```

**Catatan:** Saat ini model menghasilkan probability_up yang sangat mirip antar titik (~0.529), menunjukkan model belum terdiversifikasi. `points` berisi ~23 sampel (test set 2024).

**Saran visual:**
- Tabel metrik (accuracy / precision / recall / F1 / AUC) sebagai metric cards.
- Confusion matrix sebagai 2x2 heatmap (recharts tidak punya bawaan; gunakan `<Cell>` di BarChart dengan 4 bar).
- `points` sebagai ComposedChart dengan bar `close` (area) + dot marker warna hijau/merah berdasarkan `correct`.

---

## Endpoint: Data & EDA — Stocks

### GET /api/v1/data/eda/stocks/time-series

**Tujuan:** Deret waktu harga Close dan Volume saham GSPC (2018–2024) lengkap dengan anotasi crash event. Data utama untuk chart harga.

**Query params:** Tidak ada

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `ticker` | `string` | `"GSPC"` |
| `period` | `string` | `"2018-2024"` |
| `data` | `TimeSeriesPoint[]` | Array ~1.552 titik (seluruh hari trading) |

`TimeSeriesPoint`:

| Field | Tipe | Keterangan |
|---|---|---|
| `date` | `string` | ISO date: `YYYY-MM-DD` |
| `close` | `number` | Harga penutupan |
| `volume` | `number` | Volume transaksi |
| `is_crash_event` | `boolean` | `true` untuk tanggal crash (COVID 2020, bear 2022) |

**Contoh respons (data dipotong ke 2 elemen):**

```json
{
  "success": true,
  "message": "Deret waktu saham berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "ticker": "GSPC",
    "period": "2018-2024",
    "data": [
      { "date": "2018-01-02", "close": 2695.8100585938, "volume": 3397430000.0, "is_crash_event": false },
      { "date": "2018-01-03", "close": 2713.0600585938, "volume": 3544030000.0, "is_crash_event": false }
    ]
  }
}
```

**Saran visual (recharts):** `ComposedChart` dengan dua `YAxis`. Line chart `close` (axis kiri), `Bar` untuk `volume` (axis kanan). Tambahkan `ReferenceLine` atau `<Dot>` berwarna merah untuk `is_crash_event === true`.

---

### GET /api/v1/data/eda/stocks/raw

**Tujuan:** 10 baris terakhir data mentah saham GSPC dari file CSV processed. Berguna untuk tabel "data terbaru".

**Query params:** Tidak ada

**Shape `data`:** Array `RawStocksResponse[]` (10 elemen). Tiap elemen:

| Field | Tipe | Keterangan |
|---|---|---|
| `date` | `string` | Tanggal: `YYYY-MM-DD` |
| `open` | `number` | Harga pembukaan |
| `high` | `number` | Harga tertinggi |
| `low` | `number` | Harga terendah |
| `close` | `number` | Harga penutupan |
| `volume` | `integer` | Volume transaksi |
| `daily_return` | `number \| null` | Perubahan harian (%), null untuk baris pertama |
| `hl_spread` | `number` | High - Low (intraday range) |
| `oc_spread` | `number` | Open - Close (arah dan magnitudo) |
| `ma_20` | `number \| null` | Moving Average 20 hari, null jika data kurang |
| `ma_50` | `number \| null` | Moving Average 50 hari, null jika data kurang |
| `ma_200` | `number \| null` | Moving Average 200 hari, null jika data kurang |
| `volatility_30` | `number \| null` | Volatilitas rolling 30 hari (%), null jika data kurang |

**Contoh respons (1 elemen):**

```json
{
  "success": true,
  "message": "Raw stock data berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": [
    {
      "date": "2024-02-20",
      "open": 4989.3198242188,
      "high": 4993.7099609375,
      "low": 4955.0200195312,
      "close": 4975.509765625,
      "volume": 4034880000,
      "daily_return": -0.6005322001175206,
      "hl_spread": 38.68994140630002,
      "oc_spread": -13.810058593800022,
      "ma_20": 4949.23449707032,
      "ma_50": 4821.645625,
      "ma_200": 4489.522301025387,
      "volatility_30": 0.722593736053202
    }
  ]
}
```

**Saran visual:** Tabel data dengan kolom harga OHLCV, badge warna untuk `daily_return` (merah/hijau), kolom MA sebagai sparkline kecil.

---

### GET /api/v1/data/eda/stocks/daily-returns

**Tujuan:** Distribusi daily return: statistik agregat, deret waktu return, dan breakdown statistik per tahun.

**Query params:** Tidak ada

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `ticker` | `string` | `"GSPC"` |
| `period` | `string` | `"2018-2024"` |
| `stats` | `StatBlock` | Statistik agregat keseluruhan (satuan %) |
| `time_series` | `ReturnPoint[]` | ~1.551 titik deret return per hari |
| `annual_breakdown` | `AnnualReturn[]` | 7 elemen, satu per tahun 2018–2024 |

`StatBlock` (digunakan di banyak endpoint):

| Field | Tipe | Keterangan |
|---|---|---|
| `min` | `number` | Minimum |
| `max` | `number` | Maksimum |
| `mean` | `number` | Rata-rata |
| `std` | `number` | Standar deviasi |
| `median` | `number \| null` | Median |
| `cv_pct` | `number \| null` | Coefficient of Variation (%) |
| `skew` | `number \| null` | Skewness |
| `kurtosis` | `number \| null` | Kurtosis |
| `q25` | `number \| null` | Kuartil 25% |
| `q75` | `number \| null` | Kuartil 75% |

`ReturnPoint`:

| Field | Tipe | Keterangan |
|---|---|---|
| `date` | `string` | Tanggal (YYYY-MM-DD) |
| `return_pct` | `number` | Return harian dalam % |
| `year` | `integer` | Tahun (untuk grouping) |

`AnnualReturn`:

| Field | Tipe | Keterangan |
|---|---|---|
| `year` | `integer` | Tahun |
| `stats` | `StatBlock` | Statistik return tahun tersebut |
| `count_trading_days` | `integer` | Jumlah hari trading |

**Contoh respons (diringkas):**

```json
{
  "success": true,
  "message": "Distribusi daily return berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "ticker": "GSPC",
    "period": "2018-2024",
    "stats": {
      "min": -11.984055240391813,
      "max": 9.382773976225112,
      "mean": 0.04985728601181702,
      "std": 1.289606160866323,
      "median": 0.0837042739364468,
      "skew": -0.5124352842780835,
      "kurtosis": 12.924091949634327,
      "q25": -0.480806719017457,
      "q75": 0.6913905272446397
    },
    "time_series": [
      { "date": "2018-01-03", "return_pct": 0.6398818768781567, "year": 2018 }
    ],
    "annual_breakdown": [
      { "year": 2018, "stats": { "min": -4.097922480424632, "max": 4.959374278957229, "mean": -0.023289704214387575, "std": 1.0749469402514653, "median": 0.0365070657224575, "skew": -0.4185689946395195, "kurtosis": 3.139124072027076, "q25": -0.48180952336510924, "q75": 0.5406881418258347, "cv_pct": -4615.545695026046 }, "count_trading_days": 250 }
    ]
  }
}
```

**Saran visual:**
- `time_series` sebagai AreaChart dengan area merah (return negatif) dan hijau (positif) — gunakan `defs > linearGradient` atau dua AreaChart yang di-clip.
- `annual_breakdown` sebagai grouped BarChart per tahun dengan bar `mean` dan error bar `std`.
- Histogram distribusi dengan bin manual dari data `return_pct`.

---

### GET /api/v1/data/eda/stocks/drawdown

**Tujuan:** Cumulative return dan drawdown saham GSPC beserta metrik ringkas (total return, max drawdown, annualized return & volatility).

**Query params:** Tidak ada

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `ticker` | `string` | `"GSPC"` |
| `period` | `string` | `"2018-2024"` |
| `data` | `DrawdownPoint[]` | ~1.552 titik deret drawdown |
| `metrics` | `DrawdownMetrics` | Metrik ringkas |

`DrawdownPoint`:

| Field | Tipe | Keterangan |
|---|---|---|
| `date` | `string` | Tanggal (YYYY-MM-DD) |
| `cumulative_return_pct` | `number` | % return dari titik awal (2018-01-02 = 0%) |
| `peak_price` | `number` | Running peak harga close |
| `drawdown_pct` | `number` | % turun dari peak (negatif atau 0) |

`DrawdownMetrics`:

| Field | Tipe | Keterangan |
|---|---|---|
| `total_return_pct` | `number` | Return total periode |
| `max_drawdown_pct` | `number` | Drawdown maksimum (negatif), misal `-33.92` |
| `max_drawdown_date` | `string` | Tanggal max drawdown (`"2020-03-23"`) |
| `days_to_recovery` | `integer \| null` | Hari untuk recover dari max drawdown |
| `annualized_return_pct` | `number \| null` | Return tahunan (%) |
| `annualized_volatility_pct` | `number \| null` | Volatilitas tahunan (%) |

**Contoh respons (diringkas):**

```json
{
  "success": true,
  "message": "Data drawdown saham berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "ticker": "GSPC",
    "period": "2018-2024",
    "data": [
      { "date": "2018-01-02", "cumulative_return_pct": 0.0, "peak_price": 2695.8100585938, "drawdown_pct": 0.0 },
      { "date": "2020-03-23", "cumulative_return_pct": -5.2, "peak_price": 3386.15, "drawdown_pct": -33.92496000265277 }
    ],
    "metrics": {
      "total_return_pct": 90.3305531098481,
      "max_drawdown_pct": -33.92496000265277,
      "max_drawdown_date": "2020-03-23",
      "days_to_recovery": null,
      "annualized_return_pct": 11.015626381969534,
      "annualized_volatility_pct": 20.471863145214286
    }
  }
}
```

**Saran visual:**
- `ComposedChart` dua sumbu Y: AreaChart `cumulative_return_pct` (atas, biru) + AreaChart `drawdown_pct` (bawah, merah transparan).
- Card metrik: total return, max drawdown, annualized return, annualized vol.

---

### GET /api/v1/data/eda/stocks/descriptive-stats

**Tujuan:** Statistik deskriptif OHLCV (min, max, mean, std, median, skewness, kurtosis, kuartil) untuk tiap kolom harga dan volume.

**Query params:** Tidak ada

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `ticker` | `string` | `"GSPC"` |
| `period` | `string` | `"2018-2024"` |
| `count_records` | `integer` | Jumlah observasi (1552) |
| `close` | `StatBlock` | Statistik harga Close |
| `open` | `StatBlock` | Statistik harga Open |
| `high` | `StatBlock` | Statistik harga High |
| `low` | `StatBlock` | Statistik harga Low |
| `volume` | `StatBlock` | Statistik Volume |

Semua field `StatBlock` sudah dijelaskan di endpoint `/daily-returns`.

**Contoh respons:**

```json
{
  "success": true,
  "message": "Statistik deskriptif saham berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "ticker": "GSPC",
    "period": "2018-2024",
    "count_records": 1552,
    "close": {
      "min": 2237.3999023438,
      "max": 5137.080078125,
      "mean": 3624.7019456686407,
      "std": 716.2300300477488,
      "median": 3729.5400390625,
      "cv_pct": 19.759694473737685,
      "skew": 0.046383370528114566,
      "kurtosis": -1.402515199596303,
      "q25": 2896.7349853515752,
      "q75": 4262.775146484375
    },
    "volume": {
      "min": 0.0,
      "max": 9976520000.0,
      "mean": 4187903730.670103,
      "std": 1035816214.168407,
      "median": 3966020000.0,
      "cv_pct": 24.733524951459827,
      "skew": 1.6425096222517817,
      "kurtosis": 4.571607397380234,
      "q25": 3549760000.0,
      "q75": 4560940000.0
    }
  }
}
```

**Saran visual:** Tabel dengan kolom OHLCV dan baris statistik (min/max/mean/std/median). Atau BoxPlot chart menggunakan scatter `q25`, `median`, `q75`, `min`, `max`.

---

### GET /api/v1/data/eda/stocks/summary

**Tujuan:** Ringkasan akhir performa saham GSPC: overall & annualized return, volatilitas, max drawdown, breakdown per tahun, dan key insights.

**Query params:** Tidak ada

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `ticker` | `string` | `"GSPC"` |
| `period` | `string` | `"2018-2024"` |
| `overall_return_pct` | `number` | Total return keseluruhan periode (%) |
| `annualized_return_pct` | `number \| null` | Return tahunan rata-rata (%) |
| `annualized_volatility_pct` | `number` | Volatilitas tahunan (%) |
| `max_drawdown_pct` | `number` | Max drawdown (negatif) |
| `total_trading_days` | `integer` | Total hari trading dalam periode |
| `annual_breakdown` | `AnnualPerformance[]` | Breakdown per tahun (7 elemen, 2018–2024) |
| `key_insights` | `string[] \| null` | Daftar insight teks siap tampil |

`AnnualPerformance`:

| Field | Tipe | Keterangan |
|---|---|---|
| `year` | `integer` | Tahun |
| `open_price` | `number` | Harga open awal tahun |
| `close_price` | `number` | Harga close akhir tahun |
| `return_pct` | `number` | Return tahun tersebut (%) |
| `max_drawdown_pct` | `number` | Max drawdown dalam tahun tersebut |
| `volatility_annualized_pct` | `number` | Volatilitas tahunan tahun tersebut |
| `count_trading_days` | `integer` | Jumlah hari trading |

**Contoh respons:**

```json
{
  "success": true,
  "message": "Ringkasan performa saham berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "ticker": "GSPC",
    "period": "2018-2024",
    "overall_return_pct": 90.3305531098481,
    "annualized_return_pct": 11.015626381969534,
    "annualized_volatility_pct": 20.471863145214286,
    "max_drawdown_pct": -33.92496000265277,
    "total_trading_days": 1552,
    "annual_breakdown": [
      { "year": 2018, "open_price": 2683.7299804688, "close_price": 2506.8500976562, "return_pct": -6.590822627457562, "max_drawdown_pct": -19.778210435683697, "volatility_annualized_pct": 17.064253658971108, "count_trading_days": 251 },
      { "year": 2020, "open_price": 3244.669921875, "close_price": 3756.0700683594, "return_pct": 15.76123793168079, "max_drawdown_pct": -33.92496000265277, "volatility_annualized_pct": 34.430996492002514, "count_trading_days": 253 }
    ],
    "key_insights": [
      "Total return periode 2018-2024: 90.3%",
      "Return tahunan maksimum: 30.4% pada tahun 2019",
      "Tahun terburuk: -19.6% pada tahun 2022",
      "Max drawdown: -33.9%, volatilitas tahunan: 20.5%"
    ]
  }
}
```

**Saran visual:**
- BarChart `annual_breakdown` dengan bar `return_pct` (warna merah/hijau berdasarkan positif/negatif).
- Card summary di atas chart: total return, annualized return, max drawdown.
- List `key_insights` sebagai bullet points.

---

## Endpoint: Data & EDA — Sentiment / Berita

### GET /api/v1/data/eda/sentiment-distribution

**Tujuan:** Distribusi label sentimen (positive/negative/neutral) beserta statistik sentiment_score dari 19.127 headline.

**Query params:** Tidak ada

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `data` | `SentimentDistributionItem[]` | 3 elemen: neutral, negative, positive |
| `sentiment_score_mean` | `number` | Rata-rata sentiment_score dataset |
| `sentiment_score_std` | `number` | Standar deviasi sentiment_score |
| `plot_hint` | `string` | `"bar chart — x: label, y: count"` |

`SentimentDistributionItem`:

| Field | Tipe | Keterangan |
|---|---|---|
| `label` | `string` | `"neutral"`, `"negative"`, atau `"positive"` |
| `count` | `integer` | Jumlah headline dengan label ini |
| `pct` | `number` | Persentase (%) |

**Contoh respons:**

```json
{
  "success": true,
  "message": "Distribusi label sentimen berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "data": [
      { "label": "neutral", "count": 10956, "pct": 57.28 },
      { "label": "negative", "count": 4777, "pct": 24.98 },
      { "label": "positive", "count": 3394, "pct": 17.74 }
    ],
    "sentiment_score_mean": 0.8192,
    "sentiment_score_std": 0.1395,
    "plot_hint": "bar chart — x: label, y: count"
  }
}
```

**Saran visual:** BarChart dengan tiga bar berwarna berbeda (misalnya kuning/merah/hijau). Atau PieChart dengan `data[].pct`. Tambahkan card `sentiment_score_mean` sebagai gauge.

---

### GET /api/v1/data/eda/news-per-year

**Tujuan:** Distribusi jumlah headline berita per tahun (2008–2024).

**Query params:** Tidak ada

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `data` | `NewsPerYearItem[]` | 17 elemen, satu per tahun 2008–2024 |
| `total` | `integer` | Total headline keseluruhan (19127) |
| `plot_hint` | `string` | `"bar chart — x: year, y: count"` |

`NewsPerYearItem`:

| Field | Tipe | Keterangan |
|---|---|---|
| `year` | `integer` | Tahun |
| `count` | `integer` | Jumlah headline |

**Contoh respons:**

```json
{
  "success": true,
  "message": "Distribusi berita per tahun berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "data": [
      { "year": 2008, "count": 141 },
      { "year": 2009, "count": 113 },
      { "year": 2010, "count": 209 }
    ],
    "total": 19127,
    "plot_hint": "bar chart — x: year, y: count"
  }
}
```

**Saran visual:** BarChart dengan `x: year`, `y: count`. Tambahkan `ReferenceLine` di tahun 2020 (COVID) dan 2008 (krisis finansial).

---

### GET /api/v1/data/eda/news-per-day

**Tujuan:** Statistik agregasi jumlah headline per hari (mean, max, min) beserta petunjuk visualisasi.

**Query params:** Tidak ada

**Shape `data`:** (flat, bukan array)

| Field | Tipe | Keterangan |
|---|---|---|
| `mean` | `number` | Rata-rata headline per hari (5.45) |
| `max` | `integer` | Jumlah headline terbanyak dalam satu hari (55) |
| `max_date` | `string` | Tanggal dengan jumlah terbanyak (`"2020-09-23"`) |
| `min` | `integer` | Jumlah headline paling sedikit (1) |
| `min_date` | `string` | Tanggal dengan jumlah paling sedikit (`"2008-01-03"`) |
| `plot_hint` | `string` | `"line chart — x: date, y: daily_count"` |

**Contoh respons:**

```json
{
  "success": true,
  "message": "Statistik berita per hari berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "mean": 5.45,
    "max": 55,
    "max_date": "2020-09-23",
    "min": 1,
    "min_date": "2008-01-03",
    "plot_hint": "line chart — x: date, y: daily_count"
  }
}
```

**Catatan:** Endpoint ini hanya mengembalikan statistik agregat (bukan deret time series per hari). Untuk deret harian, gunakan `sentiment/data/preview` dan iterasikan `headline_count`.

**Saran visual:** Card statistik dengan nilai mean/max/min. Untuk distribusi harian detail, gunakan endpoint preview.

---

### GET /api/v1/data/eda/headline-length

**Tujuan:** Statistik panjang headline dalam karakter dan kata. Data siap digunakan sebagai histogram.

**Query params:** Tidak ada

**Shape `data`:** (flat)

| Field | Tipe | Keterangan |
|---|---|---|
| `char_mean` | `number` | Rata-rata panjang dalam karakter (60.29) |
| `char_std` | `number` | Std dev panjang karakter (19.52) |
| `char_min` | `number` | Headline terpendek dalam karakter (6) |
| `char_max` | `number` | Headline terpanjang dalam karakter (172) |
| `word_mean` | `number` | Rata-rata jumlah kata (10.5) |
| `word_std` | `number` | Std dev jumlah kata (3.47) |
| `word_min` | `number` | Headline paling sedikit kata (1) |
| `word_max` | `number` | Headline paling banyak kata (33) |
| `plot_hint` | `string` | `"histogram — title_len_char & title_len_word"` |

**Contoh respons:**

```json
{
  "success": true,
  "message": "Statistik panjang headline berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "char_mean": 60.29,
    "char_std": 19.52,
    "char_min": 6.0,
    "char_max": 172.0,
    "word_mean": 10.5,
    "word_std": 3.47,
    "word_min": 1.0,
    "word_max": 33.0,
    "plot_hint": "histogram — title_len_char & title_len_word"
  }
}
```

**Saran visual:** Dua card statistik (char dan word) dengan nilai mean ± std. Histogram tidak bisa dibuat dari endpoint ini saja karena hanya agregat — endpoint ini cocok untuk ringkasan di teks.

---

### GET /api/v1/data/eda/summary

**Tujuan:** Statistik dasar dataset berita: total baris, rentang tanggal, span hari, dan tipe kolom.

**Query params:** Tidak ada

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `total_rows` | `integer` | Total headline (19127) |
| `date_start` | `string` | Tanggal mulai dataset (`"2008-01-02"`) |
| `date_end` | `string` | Tanggal akhir dataset (`"2024-03-04"`) |
| `span_days` | `integer` | Rentang total dalam hari (5906) |
| `dtypes` | `object` | Tipe kolom: `{"Title": "str", "Date": "datetime64[us]", "sentiment_label": "str", "sentiment_score": "float64", "sentiment_numeric": "int64"}` |

**Contoh respons:**

```json
{
  "success": true,
  "message": "Ringkasan dataset berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "total_rows": 19127,
    "date_start": "2008-01-02",
    "date_end": "2024-03-04",
    "span_days": 5906,
    "dtypes": {
      "Title": "str",
      "Date": "datetime64[us]",
      "sentiment_label": "str",
      "sentiment_score": "float64",
      "sentiment_numeric": "int64"
    }
  }
}
```

**Saran visual:** Card dataset summary (total rows, date range, span). Tabel kecil untuk `dtypes`.

---

## Endpoint: Feature Engineering

### GET /api/v1/feature-engineering/info

**Tujuan:** Scan dan tampilkan metadata semua file CSV di `data/processed/` dikelompokkan per subdirektori.

**Query params:** Tidak ada

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `stocks` | `ProcessedFileInfo[]` | File di `data/processed/stocks/` |
| `sentiment` | `ProcessedFileInfo[]` | File di `data/processed/sentiment/` |
| `total_files` | `integer` | Total file CSV (saat ini 4) |

`ProcessedFileInfo`:

| Field | Tipe | Keterangan |
|---|---|---|
| `filename` | `string` | Nama file beserta ekstensi |
| `path` | `string` | Path relatif dari root project |
| `total_rows` | `integer` | Jumlah baris |
| `columns` | `string[]` | Daftar nama kolom |
| `date_start` | `string \| null` | Tanggal pertama jika ada kolom Date |
| `date_end` | `string \| null` | Tanggal terakhir jika ada kolom Date |

**Contoh respons:**

```json
{
  "success": true,
  "message": "Daftar file processed berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "stocks": [
      {
        "filename": "GSPC_2018_2024.csv",
        "path": "data/processed/stocks/GSPC_2018_2024.csv",
        "total_rows": 1552,
        "columns": ["Date","Open","High","Low","Close","Volume","Daily_Return","HL_Spread","OC_Spread","MA_20","MA_50","MA_200","Volatility_30"],
        "date_start": "2018-01-02",
        "date_end": "2024-03-04"
      }
    ],
    "sentiment": [
      {
        "filename": "headlines_clean.csv",
        "path": "data/processed/sentiment/headlines_clean.csv",
        "total_rows": 19127,
        "columns": ["Title","Date","sentiment_label","sentiment_score","sentiment_numeric"],
        "date_start": "2008-01-02",
        "date_end": "2024-03-04"
      },
      {
        "filename": "headlines_daily_sentiment.csv",
        "path": "data/processed/sentiment/headlines_daily_sentiment.csv",
        "total_rows": 3507,
        "columns": ["Date","headline_count","sentiment_mean","sentiment_pos","sentiment_neg","sentiment_neu","sentiment_label"],
        "date_start": "2008-01-02",
        "date_end": "2024-03-04"
      }
    ],
    "total_files": 4
  }
}
```

**Saran visual:** Tabel file yang tersedia dengan badge warna per subdirektori (stocks/sentiment). Klik file untuk memanggil `/columns` atau `/preview`.

---

### GET /api/v1/feature-engineering/columns

**Tujuan:** Tampilkan nama kolom, tipe data Pandas, dan jumlah missing values dari satu file CSV.

**Query params:**

| Param | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `source` | `string` | Ya | `"stocks"` atau `"sentiment"` |
| `file` | `string` | Ya | Nama file tanpa ekstensi, mis. `"GSPC_2018_2024"` |

**Contoh:** `GET /api/v1/feature-engineering/columns?source=stocks&file=GSPC_2018_2024`

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `source` | `string` | Subdirektori sumber |
| `filename` | `string` | Nama file yang dibaca (dengan ekstensi) |
| `total_rows` | `integer` | Jumlah baris |
| `columns` | `string[]` | Semua nama kolom |
| `dtypes` | `object` | Tipe Pandas per kolom, mis. `{"Date": "str", "Open": "float64"}` |
| `missing_values` | `object` | Jumlah nilai kosong per kolom |

**Contoh respons (GSPC_2018_2024):**

```json
{
  "success": true,
  "message": "Informasi kolom berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "source": "stocks",
    "filename": "GSPC_2018_2024.csv",
    "total_rows": 1552,
    "columns": ["Date","Open","High","Low","Close","Volume","Daily_Return","HL_Spread","OC_Spread","MA_20","MA_50","MA_200","Volatility_30"],
    "dtypes": {
      "Date": "str", "Open": "float64", "High": "float64", "Low": "float64",
      "Close": "float64", "Volume": "int64", "Daily_Return": "float64",
      "HL_Spread": "float64", "OC_Spread": "float64", "MA_20": "float64",
      "MA_50": "float64", "MA_200": "float64", "Volatility_30": "float64"
    },
    "missing_values": {
      "Date": 0, "Open": 0, "High": 0, "Low": 0, "Close": 0, "Volume": 0,
      "Daily_Return": 1, "HL_Spread": 0, "OC_Spread": 0,
      "MA_20": 19, "MA_50": 49, "MA_200": 199, "Volatility_30": 30
    }
  }
}
```

**Error 404:** Jika file tidak ditemukan di subdirektori yang diminta.

**Saran visual:** Tabel kolom dengan badge tipe data dan progress bar `missing_values` per kolom.

---

### GET /api/v1/feature-engineering/preview

**Tujuan:** Preview N baris pertama dari satu file CSV di `data/processed/`.

**Query params:**

| Param | Tipe | Default | Keterangan |
|---|---|---|---|
| `source` | `string` | — | `"stocks"` atau `"sentiment"` (wajib) |
| `file` | `string` | — | Nama file tanpa ekstensi (wajib) |
| `n` | `integer` | `5` | Jumlah baris yang ditampilkan (1–50) |

**Contoh:** `GET /api/v1/feature-engineering/preview?source=stocks&file=GSPC_2018_2024&n=5`

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `source` | `string` | Subdirektori sumber |
| `filename` | `string` | Nama file dengan ekstensi |
| `total_rows` | `integer` | Total baris di file |
| `columns` | `string[]` | Daftar kolom |
| `rows` | `object[]` | N baris pertama sebagai list-of-dict |

**Contoh respons (n=2, GSPC_2018_2024):**

```json
{
  "success": true,
  "message": "Preview data berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "source": "stocks",
    "filename": "GSPC_2018_2024.csv",
    "total_rows": 1552,
    "columns": ["Date","Open","High","Low","Close","Volume","Daily_Return","HL_Spread","OC_Spread","MA_20","MA_50","MA_200","Volatility_30"],
    "rows": [
      {
        "Date": "2018-01-02", "Open": 2683.7299804688, "High": 2695.8898925781,
        "Low": 2682.3601074219, "Close": 2695.8100585938, "Volume": 3397430000,
        "Daily_Return": null, "HL_Spread": 13.529785156199978, "OC_Spread": 12.080078125,
        "MA_20": null, "MA_50": null, "MA_200": null, "Volatility_30": null
      },
      {
        "Date": "2018-01-03", "Open": 2697.8500976562, "High": 2714.3701171875,
        "Low": 2697.7700195312, "Close": 2713.0600585938, "Volume": 3544030000,
        "Daily_Return": 0.6398818768781567, "HL_Spread": 16.600097656300022, "OC_Spread": 15.209960937600044,
        "MA_20": null, "MA_50": null, "MA_200": null, "Volatility_30": null
      }
    ]
  }
}
```

**Catatan:** `null` pada kolom MA dan Volatility_30 di baris awal adalah normal — butuh N hari sebelumnya untuk kalkulasi.

**Saran visual:** Tabel data dengan kolom dinamis dari `columns`. Gunakan `n=5` sebagai default di UI, tambahkan selector `n`.

---

## Endpoint: Sentiment Pipeline

### GET /api/v1/sentiment/data/preview

**Tujuan:** Preview data sentimen harian dengan pagination manual.

**Query params:**

| Param | Tipe | Default | Keterangan |
|---|---|---|---|
| `page` | `integer` | `1` | Halaman (1-indexed) |
| `page_size` | `integer` | `20` | Jumlah baris per halaman |

**Catatan penting:** Pagination di endpoint ini **tidak** mengisi `meta.pagination`. Informasi total tersedia di `data.total_rows`. Frontend harus menghitung `total_pages = Math.ceil(total_rows / page_size)`.

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `source` | `string` | `"sentiment"` |
| `filename` | `string` | `"headlines_daily_sentiment.csv"` |
| `total_rows` | `integer` | Total baris di file (3507) |
| `columns` | `string[]` | Kolom: `["Date","headline_count","sentiment_mean","sentiment_pos","sentiment_neg","sentiment_neu","sentiment_label"]` |
| `rows` | `object[]` | Baris untuk halaman ini |

Tiap baris di `rows`:

| Field | Tipe | Keterangan |
|---|---|---|
| `Date` | `string` | ISO datetime: `"2008-01-02T00:00:00"` |
| `headline_count` | `integer` | Jumlah headline pada tanggal ini |
| `sentiment_mean` | `number` | Rata-rata sentimen harian [-1.0, 1.0]: positif=+1, negatif=-1, neutal=0 |
| `sentiment_pos` | `number` | Fraksi headline positif [0–1] |
| `sentiment_neg` | `number` | Fraksi headline negatif [0–1] |
| `sentiment_neu` | `number` | Fraksi headline neutral [0–1] |
| `sentiment_label` | `string` | Label dominan: `"positive"`, `"negative"`, atau `"neutral"` |

**Contoh respons (page=1, page_size=2):**

```json
{
  "success": true,
  "message": "Preview data sentimen berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "source": "sentiment",
    "filename": "headlines_daily_sentiment.csv",
    "total_rows": 3507,
    "columns": ["Date","headline_count","sentiment_mean","sentiment_pos","sentiment_neg","sentiment_neu","sentiment_label"],
    "rows": [
      {
        "Date": "2008-01-02T00:00:00",
        "headline_count": 3,
        "sentiment_mean": -0.6666666666666666,
        "sentiment_pos": 0.0,
        "sentiment_neg": 0.6666666666666666,
        "sentiment_neu": 0.3333333333333333,
        "sentiment_label": "negative"
      },
      {
        "Date": "2008-01-03T00:00:00",
        "headline_count": 1,
        "sentiment_mean": 1.0,
        "sentiment_pos": 1.0,
        "sentiment_neg": 0.0,
        "sentiment_neu": 0.0,
        "sentiment_label": "positive"
      }
    ]
  }
}
```

**Saran visual:** Tabel paginated dengan badge warna per `sentiment_label`. AreaChart `sentiment_mean` per tanggal sebagai sparkline.

---

### GET /api/v1/sentiment/model/status

**Tujuan:** Cek ketersediaan model FinBERT dan file-file yang diperlukan.

**Query params:** Tidak ada

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `is_available` | `boolean` | `true` jika semua file model tersedia |
| `model_path` | `string` | Path direktori model FinBERT |
| `source` | `string` | `"local_snapshot"`, `"local_dir"`, atau `"huggingface_hub"` |
| `snapshot_path` | `string \| null` | Path snapshot HuggingFace cache aktif |
| `required_files` | `object` | Keberadaan tiap file yang diperlukan (boolean per key) |
| `model_size_mb` | `number \| null` | Total ukuran model dalam MB |

`required_files` keys: `config.json`, `pytorch_model.bin`, `tokenizer_config.json`, `vocab.txt`.

**Contoh respons:**

```json
{
  "success": true,
  "message": "Status model FinBERT berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "is_available": true,
    "model_path": "models/finbert/models--ProsusAI--finbert",
    "source": "local_snapshot",
    "snapshot_path": "models/finbert/models--ProsusAI--finbert/snapshots/4556d13015211d73dccd3fdd39d39232506f3e43",
    "required_files": {
      "config.json": true,
      "pytorch_model.bin": true,
      "tokenizer_config.json": true,
      "vocab.txt": true
    },
    "model_size_mb": 1253.48
  }
}
```

**Saran visual:** Card model status dengan badge `is_available`, checklist `required_files`, dan ukuran model.

---

### GET /api/v1/sentiment/pipeline/status

**Tujuan:** Status pipeline sentimen: apakah file processed sudah ada, jumlah headline, dan rentang tanggal.

**Query params:** Tidak ada

**Shape `data`:**

| Field | Tipe | Keterangan |
|---|---|---|
| `clean_file_exists` | `boolean` | Apakah `headlines_clean.csv` sudah ada |
| `daily_file_exists` | `boolean` | Apakah `headlines_daily_sentiment.csv` sudah ada |
| `total_headlines` | `integer \| null` | Total headline (dari clean file), null jika belum ada |
| `total_days` | `integer \| null` | Total hari unik (dari daily file), null jika belum ada |
| `date_range` | `object` | `{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}` |

**Contoh respons:**

```json
{
  "success": true,
  "message": "Status pipeline sentimen berhasil dimuat",
  "meta": { "timestamp": "...", "version": "1.0", "pagination": null },
  "data": {
    "clean_file_exists": true,
    "daily_file_exists": true,
    "total_headlines": 19127,
    "total_days": 3507,
    "date_range": {
      "start": "2008-01-02",
      "end": "2024-03-04"
    }
  }
}
```

**Saran visual:** Card "Pipeline Status" dengan dua badge (clean file / daily file), total rows, dan rentang tanggal.

---

## Endpoint SSE (Streaming, Bukan JSON)

### POST /api/v1/sentiment/pipeline/run

**Tujuan:** Jalankan sentiment pipeline dan kirim progress secara real-time via Server-Sent Events.

**Catatan:** Endpoint ini **tidak** menggunakan envelope JSON biasa. Response adalah `text/event-stream`. Tidak cocok dikonsumsi dengan `fetch().json()`.

**Query params:**

| Param | Tipe | Default | Keterangan |
|---|---|---|---|
| `start_date` | `string \| null` | `null` | Filter tanggal mulai (YYYY-MM-DD) |
| `end_date` | `string \| null` | `null` | Filter tanggal akhir (YYYY-MM-DD) |
| `batch_size` | `integer` | `32` | Ukuran batch inferensi FinBERT |

**Format SSE tiap event:**

```
data: {"step": "loading_data", "pct": 10, "msg": "Loading headlines..."}
```

| Field | Tipe | Keterangan |
|---|---|---|
| `step` | `string` | Tahap pipeline saat ini |
| `pct` | `integer` | Progress 0–100 |
| `msg` | `string` | Pesan deskriptif |

Urutan `step`: `loading_data` → `filtering` → `loading_model` → `model_ready` → `inference` → `aggregating` → `saving` → `done` atau `error`.

Event `done` menyertakan field tambahan `result` berisi output lengkap pipeline.

**Saran implementasi frontend:** Gunakan `EventSource` API atau `fetch` dengan `ReadableStream`. Render progress bar dari `pct` dan log pesan dari `msg`.

---

## Ringkasan Endpoint

| # | Method | Path | Tag | Status |
|---|---|---|---|---|
| 1 | GET | `/api/health` | Status | Aktif |
| 2 | GET | `/api/status` | Status | Aktif |
| 3 | GET | `/api/v1/predict/model/status` | Prediction | Aktif |
| 4 | POST | `/api/v1/predict` | Prediction | Aktif |
| 5 | GET | `/api/v1/predict/backtest` | Prediction | Aktif |
| 6 | GET | `/api/v1/data/eda/stocks/time-series` | Data & EDA | Aktif |
| 7 | GET | `/api/v1/data/eda/stocks/raw` | Data & EDA | Aktif (10 baris terakhir) |
| 8 | GET | `/api/v1/data/eda/stocks/daily-returns` | Data & EDA | Aktif |
| 9 | GET | `/api/v1/data/eda/stocks/drawdown` | Data & EDA | Aktif |
| 10 | GET | `/api/v1/data/eda/stocks/descriptive-stats` | Data & EDA | Aktif |
| 11 | GET | `/api/v1/data/eda/stocks/summary` | Data & EDA | Aktif |
| 12 | GET | `/api/v1/data/eda/sentiment-distribution` | Data & EDA | Aktif |
| 13 | GET | `/api/v1/data/eda/news-per-year` | Data & EDA | Aktif |
| 14 | GET | `/api/v1/data/eda/news-per-day` | Data & EDA | Aktif |
| 15 | GET | `/api/v1/data/eda/headline-length` | Data & EDA | Aktif |
| 16 | GET | `/api/v1/data/eda/summary` | Data & EDA | Aktif |
| 17 | GET | `/api/v1/feature-engineering/info` | Feature Engineering | Aktif |
| 18 | GET | `/api/v1/feature-engineering/columns` | Feature Engineering | Aktif |
| 19 | GET | `/api/v1/feature-engineering/preview` | Feature Engineering | Aktif |
| 20 | GET | `/api/v1/sentiment/data/preview` | Sentiment Pipeline | Aktif |
| 21 | GET | `/api/v1/sentiment/model/status` | Sentiment Pipeline | Aktif |
| 22 | GET | `/api/v1/sentiment/pipeline/status` | Sentiment Pipeline | Aktif |
| 23 | POST | `/api/v1/sentiment/pipeline/run` | Sentiment Pipeline | SSE stream |
