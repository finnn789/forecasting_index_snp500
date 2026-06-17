Eksekusi rancangan "notebook03-part-a-b-plan" dari Ruflo memory
(namespace stock_prediction). Implementasikan PART A+B ke
notebooks/03_LSTM_experiment.ipynb menggunakan 2 agent Sonnet
SEKUENSIAL:

- Agent 1 → PART A: tambah indikator teknikal (pakai
  compute_technical_indicators) dalam bentuk stasioner, update
  FEATURE_COLS (10 fitur), scaling fit train-only.
- Agent 2 → PART B: model kecil (hidden 32, 1 layer) + dropout 0.5
  + weight_decay 1e-4, class weight, seed ensemble (5 seed) di
  evaluasi & walk-forward, plot kurva train-vs-val AUC, tabel
  baseline (LSTM vs always-Up vs random).

Aturan: JANGAN eksekusi cell apa pun. Setelah tiap agent, verifikasi
sendiri logika kritis (anti-leakage, stasioneritas, shift1, no
'verbose' di ReduceLROnPlateau, outputs cell kosong). Artefak versi
v5. HANYA implementasi — JANGAN buat draf Bab Tinjauan Pustaka.