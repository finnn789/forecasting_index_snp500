# Prompt Instruksi — Tab "Data Information" di ui-stock-prediction + API Pendukung

**Status: BELUM DIEKSEKUSI.** Disiapkan 2026-07-24, direncanakan dieksekusi sesi berikutnya
oleh Claude Sonnet. Prompt ini dirancang untuk berdiri sendiri (self-contained) — sesi
Sonnet yang mengerjakannya tidak akan mewarisi percakapan yang menghasilkan rancangan ini.

---

## PROMPT (salin dari sini ke bawah untuk didelegasikan ke Sonnet)

Kamu akan membangun tab baru **"Data Information"** di frontend `ui-stock-prediction`
beserta API pendukungnya di backend `stock_prediction`. Tab ini menampilkan **temuan
diagnostik** tentang kenapa model prediksi arah harga (horizon 1 hari & horizon 5 hari)
berkinerja buruk — supaya bisa didemokan langsung di aplikasi saat sidang skripsi
(bukan lagi screenshot notebook statis).

### Konteks temuan yang harus ditampilkan (ground truth ada di notebook, JANGAN hardcode
angka dari sini — hitung ulang lewat kode yang sama)

Sumber logika: `stock_prediction/notebooks/11_diagnostic_data_analysis_horizon.ipynb`
(sudah dieksekusi, semua angka di notebook itu valid per 2026-07-24). Baca notebook ini
dulu sebagai spesifikasi PERSIS apa yang harus dihitung ulang oleh service backend —
JANGAN reinvent logic, JANGAN pula sekadar menyalin angka jadi konstanta statis (data
CSV/model bisa berubah, endpoint harus tetap hitung live).

Ringkasan 6 temuan yang perlu jadi 1 section masing-masing di tab baru:
1. **Pergeseran rezim pasar antar split** — split kronologis 70/15/15 kebetulan membelah
   data jadi 3 periode dengan arah pasar berbeda (train naik, val turun ~2022, test naik
   lagi). Perlu: chart harga Close dengan 3 area (train/val/test) diwarnai beda + tabel
   ringkas (tanggal, % perubahan harga, Up% label) per split.
2. **Harga keluar jangkauan hasil normalisasi** — `MinMaxScaler` di-fit HANYA di data
   train (metodologi anti-leakage yang benar), tapi karena harga terus naik ke rekor
   baru, 10-13.5% baris data uji punya nilai ternormalisasi di luar [0,1]. Perlu: chart
   harga Close ternormalisasi dengan garis batas 0 dan 1, + tabel persentase per fitur.
3. **Arah hubungan fitur-label berbalik antar periode** — korelasi Open/High/Low/Close/
   Volume dengan label berubah tanda (negatif di train → positif di test), makin
   ekstrem di horizon 5. Perlu: tabel korelasi per fitur × per split × per horizon,
   dengan penanda visual (mis. warna merah) kalau tandanya berbalik.
4. **Sentimen berita bersifat reaktif, bukan memimpin harga** — skor sentimen FinBERT
   berkorelasi kuat dengan pergerakan harga PADA HARI YANG SAMA, tapi nyaris nol untuk
   memprediksi hari-hari berikutnya. Perlu: tabel korelasi sentimen vs return harga
   pada jarak 0-10 hari ke depan.
5. **Perbandingan dengan baseline sederhana** — akurasi model dibandingkan "selalu
   tebak mayoritas" dan "ikuti arah kemarin (persistence)", per split, per horizon,
   per model (A=OHLCV, B=FinBERT-LSTM). Perlu: tabel perbandingan.
6. *(opsional, prioritas rendah kalau waktu terbatas)* **Uji pergeseran distribusi
   (KS-test)** — bukti statistik formal bahwa distribusi fitur train vs test berbeda
   signifikan. Perlu: tabel KS-statistic + p-value per fitur.

**Bahasa/istilah di UI:** semua judul, label, dan keterangan yang akan dilihat pengguna
HARUS pakai Bahasa Indonesia sederhana-tapi-ilmiah — HINDARI istilah teknis mentah
seperti "regime shift", "sign-flip", "out-of-distribution", "KS-test" di teks yang
tampil ke pengguna. Gunakan padanan deskriptif, contoh:
- "regime shift" → "pergeseran pola pasar antar periode"
- "out-of-range/out-of-distribution" → "nilai di luar jangkauan data latihan"
- "sign-flip correlation" → "arah hubungan yang berbalik"
- "KS-test" → boleh tetap disebut tapi beri penjelasan singkat "(uji statistik
  perbedaan distribusi)"
Istilah teknis boleh muncul di tooltip/label kecil untuk ketertelusuran, tapi judul
section & narasi utama harus deskriptif biasa.

### Stack & konvensi yang WAJIB diikuti (hasil survei, jangan diasumsikan ulang)

**Frontend** (`ui-stock-prediction/`): React 19 + Vite + `react-router-dom` v7 +
Tailwind 4 + `plotly.js-dist-min` untuk chart. Tidak ada axios — HTTP call lewat
`src/utils/api.js` (`fetchJson`/`postJson`, otomatis unwrap `SuccessResponse.data`).
- Routing: tambah `<Route path="/data-information" element={<DataInformation />} />`
  di `src/App.jsx` (pola `<Route>` flat, lihat route lain yang sudah aktif).
- Sidebar: tambah 1 object ke `NAV_ITEMS` di `src/layout/Sidebar.jsx`
  (`{ to: "/data-information", label: "Data Information", icon: "<nama Material
  Symbols>" }`).
- **REUSE komponen yang sudah ada** di `src/components/data-analysis/` (mis.
  `TimeSeriesChart`, `StatsTable`, `CorrelationHeatmap`, `DistributionView`,
  `SummaryTable`/`DataPreviewTable`) dan `src/components/charts/` (`PlotlyChart`,
  `StatCard`) — JANGAN bangun ulang dari nol kalau bentuknya sudah cocok. Kalau perlu
  komponen baru (mis. time-series dengan 3 area berwarna, atau tabel korelasi dengan
  highlight baris yang berbalik tanda), buat scoped di folder baru
  `src/components/data-information/` mengikuti pola folder-per-fitur yang sudah ada.
- Halaman baru: `src/pages/DataInformation.jsx` — satu halaman scrollable dengan 5-6
  section (satu section = satu temuan di atas), tiap section fetch dari satu endpoint
  API baru saat mount (`useEffect`).

**Backend** (`stock_prediction/`): FastAPI + pola `EnvelopeRoute`
(`app/core/envelope.py`) — handler route cukup `return <schema>`, pembungkusan ke
`SuccessResponse` otomatis lewat `openapi_extra={"x-message": "..."}`. Pola referensi
LENGKAP ada di `app/api/v1/routes_data_analysis.py` +
`app/services/data_analysis_service.py` + `app/schemas/data_analysis.py` — ikuti
konvensi yang SAMA PERSIS:
- Tiap schema response WAJIB punya field `plot_hint: str` (default value, deskripsi
  jenis chart & sumbu yang dimaksud untuk frontend) — lihat contoh di
  `app/schemas/data_analysis.py`.
- Tambah field `note: str` untuk keterangan metodologi bila relevan.
- File baru: `app/schemas/data_information.py`, `app/services/data_information_service.py`,
  `app/api/v1/routes_data_information.py` (router baru `data_information_router`,
  prefix `/api/v1/data-information`, `route_class=EnvelopeRoute`, `tags=["Data
  Information"]`). Daftarkan di `app/api/v1/__init__.py` (ikuti pola registrasi router
  lain di file itu).

**Reuse logic — JANGAN duplikasi:**
- Split + capping outlier: reuse `models/lstm/notebook07_common.py::_load_split_capped()`
  — fungsi ini SUDAH mendukung parameter `horizon` (ditambahkan sesi sebelumnya, default
  1, backward-compatible). Karena sekarang akan dipakai oleh service PRODUKSI (bukan cuma
  notebook eksperimen), **promosikan jadi public**: rename `_load_split_capped` →
  `load_split_capped` (hapus underscore), update SEMUA pemanggil internal di
  `notebook07_common.py` sendiri dan pemanggil eksternal yang sudah ada
  (`notebooks/10_LSTM_horizon5_skripsi_scoped.ipynb`, `notebooks/11_diagnostic_data_analysis_horizon.ipynb`
  — cari-ganti nama fungsi di kedua file `.ipynb` itu juga, jangan sampai notebook rusak).
- Loader data mentah: `pipeline/feature_engineering/dataset_builder.py`
  (`load_joined()`, `load_ohlcv_only()`, `FEATURE_COLS`, `OHLCV_FEATURE_COLS`).
- Semua kalkulasi statistik (korelasi point-biserial, KS-test, rolling Up%, dst) harus
  memanggil ulang `scipy.stats`/`pandas`/`sklearn` PERSIS seperti di notebook 11 — port
  logic dari tiap "Bagian" notebook 11 ke fungsi service, bukan hardcode hasil.

### Endpoint yang harus dibuat (6 wajib + 1 opsional)

Semua di bawah prefix `/api/v1/data-information/`, method GET, tanpa autentikasi (samakan
dengan endpoint lain di app ini):

1. `GET /regime-overview?model=ohlcv|joined&horizon=1|5` — harga Close harian penuh +
   tanggal batas train/val/test + ringkasan (tanggal awal/akhir, % perubahan harga,
   harga min/max) per split. (Bagian A notebook 11)
2. `GET /label-balance?horizon=1|5` — Up%/Down% per split untuk kedua model (A & B),
   plus rolling Up% (window 60 hari) sepanjang waktu. (Bagian B)
3. `GET /scaling-range?model=ohlcv|joined&horizon=1|5` — per fitur: rentang scaled train,
   % baris val/test di luar [0,1], plus time series Close ternormalisasi. (Bagian C)
4. `GET /feature-label-correlation?model=ohlcv|joined&horizon=1|5` — korelasi
   point-biserial per fitur per split, dengan flag boolean `sign_flip` per fitur.
   (Bagian D)
5. `GET /sentiment-lag-correlation` — korelasi `sentiment_mean(t)` vs return Close
   `(t+k)` untuk k=0..10, keseluruhan data + per split. (Bagian F)
6. `GET /baseline-comparison` — tabel Always-Majority & Persistence baseline per
   split/horizon/model, DIGABUNG dengan metrik model sungguhan yang sudah tersimpan di
   `data/artifacts/lstm_weights/*_metadata.json` (baca file JSON yang sudah ada, seperti
   pola `notebooks/10_LSTM_horizon5_skripsi_scoped.ipynb` Bagian 4). (Bagian H +
   perbandingan model nyata)
7. *(opsional)* `GET /distribution-drift?model=ohlcv|joined&horizon=1|5` — KS-statistic +
   p-value per fitur (train vs test) + data histogram (bisa reuse schema `Histogram` yang
   sudah ada di `app/schemas/data_analysis.py`). (Bagian E)

### Batasan (non-goals)

- JANGAN melatih ulang model apa pun.
- JANGAN mengubah endpoint, service, atau komponen produksi yang sudah ada — ini murni
  penambahan (additive).
- Tidak perlu SSE/streaming — semua endpoint di atas GET biasa, respons langsung.
- JANGAN mengubah `dataset_builder.py`/`notebook07_common.py` selain rename
  `_load_split_capped` → `load_split_capped` yang diminta di atas.

### Verifikasi wajib sebelum lapor selesai

1. `pytest` di `stock_prediction/` lulus (tambahkan test baru untuk endpoint-endpoint
   ini mengikuti pola parametrized yang sudah ada di `tests/test_api/test_envelope.py`
   kelas `TestDataAnalysisEndpoints`). Laporkan jumlah pass/fail, termasuk 2 kegagalan
   pre-existing yang SUDAH diketahui tidak berkaitan (`test_default_ticker`,
   `test_sentiment_raw_analysis_endpoint[.../closing-price]`) — jangan anggap sebagai
   regresi baru kalau itu yang gagal.
2. Jalankan dev server frontend (pakai tool preview, BUKAN Bash) dan BACKEND-nya,
   navigasi ke tab "Data Information" baru, screenshot tiap section, pastikan tidak ada
   error di console/network.
3. **Sanity check angka**: bandingkan output UI dengan angka yang sudah dilaporkan
   sebelumnya (val split = periode turun ~-5.4%, Up% val ≈45% vs train/test ≈55-65%,
   10-13.5% harga test di luar [0,1], korelasi Close train negatif → test positif) — kalau
   angkanya beda jauh, curigai ada bug port logic dari notebook, JANGAN abaikan.

---

## Catatan tambahan untuk yang mendelegasikan (bukan bagian prompt di atas)

- File sumber kebenaran: `notebooks/11_diagnostic_data_analysis_horizon.ipynb` (sudah
  dieksekusi) dan memory `notebook11_diagnostic_regime_shift.md` (ringkasan angka).
- Kalau Sonnet ternyata butuh keputusan desain yang tidak dicakup prompt ini (mis. warna
  chart, apakah section jadi tab-dalam-tab atau satu halaman panjang), izinkan dia
  memilih default yang wajar dan laporkan pilihannya — jangan blocking.
- Perkiraan skala kerjaan: sebanding dengan fitur "combined/pipeline-steps" yang sudah
  pernah dibangun (2026-07-12, backend+frontend paralel 2 agent) — realistis 1 sesi kerja.
