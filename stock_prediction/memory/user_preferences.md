# User Preferences & Collaboration Rules

## Bahasa Komunikasi
- **Bahasa Indonesia** — semua komunikasi dengan user dalam Bahasa Indonesia

## Aturan Eksekusi (WAJIB)
- **Konfirmasi sebelum eksekusi** — tampilkan rencana dulu, tunggu persetujuan user
- **Tanya dulu sebelum menambah folder baru** — jangan buat folder tanpa izin

## Preferensi Output
- Plot/visualisasi → **kembalikan sebagai JSON** (bukan gambar inline di notebook/API)
- Setiap langkah pipeline → **log dengan `logging.INFO`**
- Feature engineering → dibuat **mirip struktur EDA** di notebook

## Preferensi Dokumentasi
- Hal-hal penting dicatat langsung di `CLAUDE.md` selama sesi berlangsung
- User menyediakan folder `memory/` di project untuk catatan sesi

## Manajemen Token Jupyter MCP
- Gunakan `insert_cell` (tanpa eksekusi) untuk markdown
- Batasi jumlah cell yang dieksekusi per giliran
- Untuk plot besar → simpan ke file, jangan tampilkan inline
- Pisahkan cell besar menjadi cell-cell kecil yang terfokus
