# Backlog 034 — OPM: kolom "Jabatan" menampilkan ID mentah (`jbt_…`), bukan nama jabatan

> **Repo:** `anjab-abk-backend` (kemungkinan besar) / `anjab-abk-web-app` — tentukan di Langkah 1
> **Status:** Siap dieksekusi
> **Blocked by:** — (independen dari 023, tapi verifikasi akhirnya butuh OPM bisa dibuat → 023)
> **Skill yang dipakai:** `backend-skill`, `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Di halaman **daftar** `/opm` dan **detail** `/opm/{sesi_id}`, jabatan ditampilkan sebagai **ID
internal mentah** (mis. `jbt_16548582`) alih-alih nama jabatan ("Koordinator Pramuka"). Ini
persis kelas bug yang sudah diperbaiki untuk DCS & WCP di **backlog 022** — OPM terlewat.

## Kondisi sekarang (verified)

Diamati di produksi 2026-07-14 (Playwright) sebelum data OPM lama dihapus:

| # | Fakta | Verifikasi |
|---|---|---|
| 1 | `/opm` — tabel menampilkan baris dengan kolom **Jabatan** berisi `jbt_16548582` dan `jbt_b2482c0a` | ✓ `innerText` tabel |
| 2 | `/opm/{sesi_id}` — subteks header berbunyi **"Jabatan: jbt_16548582"** | ✓ `innerText` main |
| 3 | Pesan error create OPM juga memakai ID mentah: *"Sesi OPM untuk jabatan 'jbt_0e87bc6b' sudah ada."* | ✓ — lihat backlog 023 |
| 4 | Preseden perbaikan sudah ada: revisi `[2026-07-14]` di `anjab-abk-backend/CLAUDE.md` menyuntikkan `JabatanService` ke `SqlDcsRespondenService`/`SqlWcpRespondenService` untuk meresolusi `jabatan_label` | ✓ backlog 022 (Selesai) |

## Langkah eksekusi

### Langkah 1 — tentukan lapisan yang salah (WAJIB dulu, jangan menebak)

Periksa apakah `OpmSesiRead` sudah mengekspos `jabatan_nama` (seperti `TiSesiRead` yang punya
`jabatan_nama` sejak revisi `[2026-06-25]`):

- **Bila `OpmSesiRead` TIDAK punya `jabatan_nama`** → perbaikan di **backend**: tambahkan field
  (pola `TiSesiRead`), isi dari `JabatanService` di `list()`/`get()`, regenerasi `openapi.json`,
  lalu web-app pakai `jabatan_nama`.
  Catatan: `_to_read(rec, jabatan.nama)` di `opm/services/sesi_sql.py:244` sudah menerima nama
  jabatan pada jalur `create()` — cek apakah jalur `list()`/`get()` meneruskannya juga.
- **Bila `OpmSesiRead` SUDAH punya `jabatan_nama`** → perbaikan murni di **web-app**: halaman
  `/opm` & `/opm/{id}` merender field yang salah (`jabatan_id`, bukan `jabatan_nama`).

### Langkah 2 — perbaiki di lapisan yang terbukti salah

Ikuti pola yang sudah ada (jangan bikin helper baru): `JabatanService` via DI, fallback ke ID
mentah + `logger.warning` bila jabatan tidak ditemukan — persis `SqlDcsRespondenService` (022).

### Langkah 3 — pesan error ikut memakai nama

`opm/services/sesi_sql.py` — pesan `ConflictError`/`ValidationAppError` yang menyebut
`data.jabatan_id` sebaiknya menyebut nama jabatan (objek `jabatan` sudah di-`get()` di baris
127-129, jadi namanya sudah tersedia — tidak perlu query tambahan).

## Kriteria penerimaan

- [ ] `/opm` dan `/opm/{id}` menampilkan **nama jabatan**, bukan `jbt_…`.
- [ ] Pesan error create OPM menyebut nama jabatan.
- [ ] Jabatan yang tidak ditemukan → fallback ID mentah + warning, tidak crash.
- [ ] `make test` hijau; bila `openapi.json` berubah, tipe web-app & MCP diregenerasi.

## Risiko & catatan

Verifikasi end-to-end di produksi **baru mungkin setelah backlog 023 diperbaiki** (sekarang sesi
OPM tidak bisa dibuat sama sekali). Perbaikan kode & unit test tetap bisa jalan lebih dulu.
