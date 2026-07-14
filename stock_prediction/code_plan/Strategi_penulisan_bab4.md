# Strategi Penulisan Bab 4 — Perhitungan Manual Indikator Teknikal

> Dokumen ini berisi strategi penyajian perhitungan manual (RSI, EMA, MACD,
> Bollinger Bands, dll.) untuk Bab 4 skripsi, supaya tidak menghabiskan
> banyak halaman tapi tetap membuktikan pemahaman metodologi ke dosen
> penguji. Sumber kode: `pipeline/feature_engineering/technical_indicators.py`.

---

## 1. Pola penyajian (berlaku untuk semua indikator)

Jangan tulis perhitungan manual untuk seluruh baris data (1.552 hari) —
itu bisa puluhan halaman dan tidak menambah nilai akademis. Pakai pola
4 langkah ini untuk **setiap** indikator:

1. **Rumus** — tulis definisi matematis sekali.
2. **Contoh hitung tangan** — 1–2 langkah manual, pakai data asli, untuk
   membuktikan pemahaman.
3. **Tabel ringkas** — hasil untuk ~10 baris pertama (dari sistem, bukan
   dihitung ulang manual satu-satu).
4. **Rujukan ke Lampiran** — tabel lengkap semua baris + cuplikan kode
   ditaruh di Lampiran, bukan di badan Bab 4.

Kalimat penutup standar tiap subbab:

> *"Perhitungan untuk seluruh N baris data mengikuti prosedur rekursif
> yang sama, diimplementasikan pada `technical_indicators.py` dan
> divalidasi kesesuaiannya dengan perhitungan manual di atas (lihat
> Lampiran X untuk tabel lengkap)."*

---

## 2. Catatan penting sebelum menulis RSI

Kode di `_rsi()` pakai smoothing **Wilder/EWM** via
`series.ewm(com=period-1, adjust=False).mean()`, **bukan** RSI "buku
teks" yang menunggu genap 14 hari baru muncul nilai pertama. Konsekuensi:

- Baris ke-0 s.d. ke-5 (pada data GSPC) bernilai **NaN**, bukan karena
  "masa pemanasan 14 hari", tapi karena **belum ada satu pun hari
  turun** dalam rentang tersebut (AvgLoss = 0 → RS tak terhingga →
  RSI tak terdefinisi).
- Kalau dosen membandingkan dengan RSI versi textbook (rata-rata
  sederhana 14 hari pertama), angkanya akan **sedikit beda** dari versi
  EWM ini. Jelaskan di awal subbab bahwa skripsi ini pakai metode
  Wilder/EWM sesuai implementasi kode — supaya konsisten antara
  perhitungan manual dan output sistem.

---

## 3. RSI-14 — rumus & contoh hitung tangan

### Rumus

```
Δ(t)       = Close(t) − Close(t−1)
Gain(t)    = max(Δ(t), 0)                Loss(t) = max(−Δ(t), 0)
AvgGain(t) = α·Gain(t) + (1−α)·AvgGain(t−1)      α = 1/14
AvgLoss(t) = α·Loss(t) + (1−α)·AvgLoss(t−1)
RS(t)      = AvgGain(t) / AvgLoss(t)
RSI(t)     = 100 − [100 / (1 + RS(t))]
```

### Contoh hitung tangan (data GSPC, mulai 2018-01-02)

**Langkah 1 — inisialisasi (baris pertama jadi "benih" rekursi):**
```
AvgGain(1) = Gain(1) = 17.2500     (2018-01-03, Close naik 2695.81 → 2713.06)
AvgLoss(1) = Loss(1) = 0.0000
```

**Langkah 2 — rekursi (baris ke-2, α = 1/14 ≈ 0.0714):**
```
Gain(2) = 10.9299   (2018-01-04, Close naik 2713.06 → 2723.99)
AvgGain(2) = 0.0714 × 10.9299 + 0.9286 × 17.2500
           = 0.7804 + 16.0181
           = 16.7985   (sistem: 16.7986, selisih pembulatan)
```

**Baris pertama RSI muncul (baris ke-6, hari pertama harga TURUN):**
```
AvgGain(6) = 14.1032   AvgLoss(6) = 0.2186   (hasil rekursi baris 1→6)
RS(6)  = 14.1032 / 0.2186 = 64.5233
RSI(6) = 100 − [100 / (1 + 64.5233)] = 100 − 1.5262 = 98.4738
```

### Tabel ringkas 10 data pertama

| # | Date | Close | Gain | Loss | AvgGain | AvgLoss | RS | RSI |
|---|---|---|---|---|---|---|---|---|
| 0 | 2018-01-02 | 2695.81 | – | – | – | – | – | – |
| 1 | 2018-01-03 | 2713.06 | 17.2500 | 0.0000 | 17.2500 | 0.0000 | – | – |
| 2 | 2018-01-04 | 2723.99 | 10.9299 | 0.0000 | 16.7986 | 0.0000 | – | – |
| 3 | 2018-01-05 | 2743.15 | 19.1599 | 0.0000 | 16.9672 | 0.0000 | – | – |
| 4 | 2018-01-08 | 2747.71 | 4.5601 | 0.0000 | 16.0810 | 0.0000 | – | – |
| 5 | 2018-01-09 | 2751.29 | 3.5801 | 0.0000 | 15.1881 | 0.0000 | – | – |
| 6 | 2018-01-10 | 2748.23 | 0.0000 | 3.0601 | 14.1032 | 0.2186 | 64.5233 | 98.4738 |
| 7 | 2018-01-11 | 2767.56 | 19.3301 | 0.0000 | 14.4766 | 0.2030 | 71.3261 | 98.6174 |
| 8 | 2018-01-12 | 2786.24 | 18.6799 | 0.0000 | 14.7768 | 0.1885 | 78.4058 | 98.7406 |
| 9 | 2018-01-16 | 2776.42 | 0.0000 | 9.8201 | 13.7213 | 0.8764 | 15.6558 | 93.9961 |

---

## 4. Indikator lain — pola yang sama, belum dikerjakan

Belum dihitung manual (siap dikerjakan kalau diperlukan, ikuti pola
Bagian 1):

- **EMA-20 / EMA-50** — `_ema()`, rata-rata bergerak berbobot eksponensial,
  formula lebih sederhana dari RSI (tidak perlu Gain/Loss).
- **MACD (12,26,9)** — selisih EMA-12 dan EMA-26, lalu di-EMA lagi (9).
- **Bollinger Bands (20, 2σ)** — rata-rata bergerak 20 hari ± 2×std.
- **Volatility-20** — std dari daily return, rolling 20 hari.

---

## 5. Struktur subbab di Bab 4 (ringkas, hemat halaman)

1. Subbab formula (semua indikator, ringkas).
2. Subbab contoh perhitungan (hitung tangan RSI di atas jadi contoh utama,
   ulangi pola singkat untuk 1 indikator lain kalau dosen minta variasi).
3. Tabel ringkas 10 baris per indikator.
4. Kalimat rujukan ke Lampiran + kode sumber.
