# Backlog 033 — TI Tahap 3: "isian standar" bocor & tidak pernah benar-benar diterapkan (durasi)

> **Repo:** `anjab-abk-web-app` (+ keputusan data di `anjab-abk-backend`)
> **Status:** Siap dieksekusi (Langkah 1); Langkah 2 butuh keputusan produk
> **Blocked by:** —
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Halaman **Isi Tahap 3** (`/task-inventory/tahap3/{responden_id}`) menawarkan checkbox
**"Setuju dengan isian standar"** per task: bila dicentang, isian CalHR standar dari katalog
dipakai apa adanya dan field-nya dikunci. Ditemukan **dua cacat** pada mekanisme ini saat
simulasi SOP TI+OPM di produksi (2026-07-14, Playwright, jabatan Koordinator Pramuka).

## Kondisi sekarang (verified)

Diamati langsung di produksi dengan mencacah seluruh `input/select` di halaman beserta
atribut `disabled`-nya (bukan pembacaan kode):

| # | Fakta | Verifikasi |
|---|---|---|
| 1 | Saat **"Setuju dengan isian standar" TERCENTANG**, seluruh field task itu `disabled` — `Sumber Bukti`, `Kondisi`, `Frekuensi`, `Jam/minggu`, `Jam peak`, `AI Mode`, `VA Type`, dan `Ada risiko DCS` — **KECUALI `Durasi/kali (menit)` yang tetap `disabled=false`** | ✓ dicacah di 4 blok task terkunci; keempatnya konsisten |
| 2 | Nilai `Durasi/kali (menit)` pada SEMUA blok standar = **60**, padahal label petunjuknya berbeda-beda per task: *"petunjuk standar: <15 menit"*, *"1-2 jam"*, *"4-8 jam"*, *"Bervariasi"* | ✓ dicacah; 60 di semua blok |
| 3 | Katalog menyimpan `std_durasi_per_kali` sebagai **teks bebas** (`str | None`, mis. `"4-8 jam"`), sedangkan field form adalah **numerik menit** | ✓ `TiCatalogRead.std_durasi_per_kali: str | None` (`taskinv/schemas/catalog.py`); ditampilkan sebagai teks petunjuk |
| 4 | Field standar lain (`std_jam_per_minggu`, `std_peak4w_hours`) memang numerik dan terisi dari katalog | ✓ |

### Kenapa ini penting

Fakta 2 berarti **"Setuju dengan isian standar" menghasilkan angka yang bertentangan dengan
standar yang ditampilkannya sendiri**: responden diberi tahu standarnya "<15 menit", menyetujuinya,
dan yang tersimpan adalah **60 menit**. Durasi ikut masuk agregasi ABK
(`durasi_per_kali_mean`) → **data beban kerja bias secara diam-diam**, tanpa satu pun tanda di UI.

Fakta 1 memperparah: karena field itu satu-satunya yang tidak terkunci, responden bisa mengubahnya
**sambil tetap mengklaim "setuju dengan isian standar"** — dua sumber kebenaran yang saling
bertentangan pada satu task.

## Langkah eksekusi

### Langkah 1 — tutup kebocoran `disabled` (siap dieksekusi)

Di komponen form Tahap 3 (`src/app/(auth)/task-inventory/tahap3/…`), field
**`Durasi/kali (menit)`** harus mengikuti flag `setuju_standar` yang **sama** dengan field lain
di blok task itu. Cari prop `disabled` yang hilang/tertinggal pada input durasi.

Tambahkan test regresi: centang "Setuju dengan isian standar" → **semua** field task itu `disabled`,
termasuk durasi (uji lewat `toBeDisabled()`, bukan snapshot).

### Langkah 2 — putuskan semantik durasi standar (BUTUH KEPUTUSAN PRODUK)

Akar masalah fakta 2: `std_durasi_per_kali` **tidak dapat dipetakan** ke menit numerik karena
memang teks bebas. Nilai 60 sekarang adalah **default diam-diam**, bukan standar.

Opsi (pilih salah satu — jangan diputuskan sendiri oleh agen pelaksana):

- **(A) Jangan prefill durasi saat setuju-standar.** Kosongkan & wajibkan responden mengisi
  angkanya, dengan teks standar tetap tampil sebagai petunjuk. Paling jujur; menghapus angka palsu.
- **(B) Tambah kolom numerik baru di katalog** (mis. `std_durasi_menit: float | None`) di samping
  teks bebas yang sudah ada, lalu prefill dari situ. Butuh migrasi Alembic + pengisian data 
  untuk ±800 uraian tugas.
- **(C) Parse teks → menit** (mis. `"1-2 jam"` → 90 sebagai titik tengah). **Tidak disarankan** —
  teks bebas tidak terbatas ("Bervariasi", "Sesuai kebutuhan") dan hasil parse akan menyesatkan
  dengan cara yang lebih sulit dideteksi daripada bug sekarang.

Sampai Langkah 2 diputuskan, **Langkah 1 tetap layak dikerjakan sendiri** — ia menghilangkan
kontradiksi "terkunci tapi bisa diubah", meski angka 60-nya belum benar.

## Kriteria penerimaan

- [ ] Langkah 1: dengan "Setuju dengan isian standar" tercentang, TIDAK ADA field task itu yang
      dapat diedit (termasuk durasi). Test regresi gagal sebelum perbaikan.
- [ ] Langkah 2: keputusan produk dicatat di sini sebelum kode ditulis.
- [ ] `make test` hijau, `npm run build` sukses.

## Risiko & catatan

Data Tahap 3 yang **sudah terlanjur terkumpul** memakai durasi 60 palsu (termasuk data uji coba
2026-07-14, dan data studi asli bila sudah ada) **tidak otomatis terkoreksi** oleh perbaikan ini.
Bila sudah ada studi sungguhan yang mengisi Tahap 3 dengan "setuju standar", nilai
`durasi_per_kali_mean`-nya patut ditinjau ulang sebelum dipakai sebagai dasar ABK.
