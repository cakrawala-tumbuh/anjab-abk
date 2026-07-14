# Backlog 023 — OPM: sesi "sudah ada" (409) untuk jabatan yang tidak muncul di listing `/opm`

> **Repo:** `anjab-abk-backend` (kemungkinan besar; butuh investigasi produksi sebelum eksekusi)
> **Status:** Menunggu investigasi produksi — BUKAN siap dieksekusi (lihat "Langkah eksekusi")
> **Blocked by:** —
> **Skill yang dipakai:** `backend-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Membuat Analisis Jabatan OPM baru gagal dengan `409 conflict` ("Sesi OPM untuk jabatan
'<jabatan_id>' sudah ada.") untuk **jabatan apa pun yang dicoba** — termasuk jabatan yang
baru saja diberi Analisis Jabatan Task Inventory dari nol hari ini — padahal halaman admin
`/opm` hanya menampilkan **2 baris total** untuk 2 jabatan yang berbeda. Ini memblokir alur
OPM sepenuhnya: admin tidak bisa membuat sesi baru, dan tidak bisa melihat/mengelola sesi
yang (menurut backend) sudah ada, karena tidak tahu ID-nya.

## Kondisi sekarang (verified)

Ditemukan saat simulasi end-to-end SOP TI + OPM di produksi (`anjab-abk.cantum-ypii.com`,
2026-07-14, via Playwright) — lihat konteks lengkap di bagian bawah `BACKLOG.md`.

| # | Fakta | Verifikasi |
|---|---|---|
| 1 | `POST /api/v1/opm/sesi` untuk `jabatan_id=jbt_67d83915` (Pembina OSIS) → `409 {"error":"conflict","message":"Sesi OPM untuk jabatan 'jbt_67d83915' sudah ada."}` | ✓ response body ditangkap langsung dari network |
| 2 | Sama untuk `jabatan_id=jbt_4c034eef` (Guru Mapel SMP) → 409 identik | ✓ |
| 3 | Sama untuk `jabatan_id=jbt_0e87bc6b` (Koordinator Pramuka) — jabatan yang **TI-nya baru dibuat & dianalisis dari nol hari yang sama**, jadi mustahil sudah punya OPM sesi dari studi lama | ✓ — ini yang menaikkan temuan dari "mungkin data lama" ke "sistemik" |
| 4 | Halaman `/opm` (admin) hanya menampilkan **2 baris**: `jbt_16548582` (status Teranalisis, 3 task) dan `jbt_b2482c0a` (status Terbuka, 158 task) — TIDAK ADA baris untuk `jbt_67d83915`/`jbt_4c034eef`/`jbt_0e87bc6b` | ✓ snapshot halaman |
| 5 | Tidak ada tool MCP `daftar_opm_sesi`/`cari_opm_sesi`/`detail_opm_sesi` — hanya `hapus_opm_sesi`/`opm_tambah_responden(_banyak)`/`opm_hapus_responden` (semua butuh `sesi_id` yang sudah diketahui) — tidak ada jalur aman untuk menemukan ID sesi "hantu" ini | ✓ — dicek via pencarian tool MCP |
| 6 | Kode `anjab-abk-web-app/src/app/(auth)/opm/page.tsx:17-25` — `fetchSesi()` memanggil `GET /api/v1/opm/sesi` dengan `limit: 100` (bukan default kecil), tanpa filter status/jabatan apa pun; render tanpa filter client-side | ✓ — dicek Explore agent |
| 7 | Kode `anjab-abk-backend/.../opm/services/sesi_sql.py:109-118` (`SqlOpmSesiService.list`) — **tidak ada `WHERE` sama sekali**, query `SELECT * FROM opm_sesi ORDER BY created_at DESC LIMIT :limit OFFSET :offset` murni | ✓ — dicek Explore agent |
| 8 | Pre-check create (`sesi_sql.py:145-149`) & constraint DB (`models.py:595`, `jabatan_id` `unique=True`) — keduanya kunci ke kolom `jabatan_id` yang **sama persis** dengan yang dipakai listing; tidak ada divergensi kondisi WHERE yang terlihat dari kode | ✓ — dicek Explore agent |
| 9 | ~~`GET /openapi.json` produksi melaporkan `info.version = "0.26.0"`, padahal `CHANGELOG.md` repo sudah `[0.33.0]` — mencurigakan (deployment lag?)~~ **→ KELIRU, DIKOREKSI 2026-07-14.** `__version__` **di-hardcode** `"0.26.0"` di `src/anjab_abk_backend/__init__.py:3` **di HEAD sendiri** dan tak pernah di-bump. Produksi melaporkan `0.26.0` **bukan** karena tertinggal, tapi karena konstanta itu basi. Perbandingan `openapi.json` produksi vs HEAD: **identik (v0.33.1)** — produksi TIDAK tertinggal. **`info.version` tidak boleh dipakai menilai versi deploy;** pakai perilaku endpoint | ✓ `grep __version__` + banding `openapi.json` prod vs HEAD, 2026-07-14 |

## Kemungkinan penyebab (belum terverifikasi — perlu akses live)

Karena review kode statis di titik 6-8 **tidak menunjukkan cacat logika** (listing tanpa
filter apa pun mengakses tabel yang sama persis dengan constraint create), penyebabnya
kemungkinan besar **di luar apa yang bisa diverifikasi lewat pembacaan kode**:

1. ~~**Environment/deployment drift**~~ — **DILEMAHKAN 2026-07-14 (lihat koreksi fakta #9 di
   bawah).** Dugaan ini bersandar pada version string `0.26.0` yang janggal. Ternyata
   `__version__` **di-hardcode** `"0.26.0"` di `src/anjab_abk_backend/__init__.py:3` dan tidak
   pernah di-bump — jadi `info.version` produksi **selalu** `0.26.0` berapa pun versi
   sebenarnya, dan **bukan bukti apa pun** soal drift. Pemeriksaan `openapi.json` produksi
   menunjukkan backend produksi **setara HEAD (v0.33.1)**. Skenario "2 instance beda versi &
   beda DB" jadi jauh lebih lemah — **jangan jadikan hipotesis utama lagi**, meski belum
   sepenuhnya gugur (topologi replica/DB belum diverifikasi langsung).
2. **Row nyata di DB, tersembunyi dari listing karena alasan non-kode** (mis. row dibuat
   langsung via SQL manual/migrasi data seed di masa lalu dengan kolom yang membuatnya lolos
   dari `ORDER BY created_at` LIMIT 100 tapi entah kenapa — kurang mungkin karena listing
   sudah pakai `limit=100` jauh di atas total sesi yang ada, dan tidak ada filter status).
3. **Idempotency-key cache internal** (`idem.reserve()` disebut di komentar kode
   `opm_sesi.py:73` sebagai kemungkinan sumber pesan lain, tapi Explore agent memverifikasi
   pesan 409 yang tertangkap benar-benar berasal dari `service.create()`, bukan dari cache
   idempotency).

## Langkah eksekusi

**JANGAN langsung menulis kode.** Langkah pertama WAJIB investigasi langsung ke lingkungan
produksi (butuh akses yang tidak dimiliki eksekusi berbasis-repo/Sonnet murni):

### Langkah 1 — Verifikasi ground truth database

Jalankan langsung di DB produksi (via akses admin/ops):
```sql
SELECT id, jabatan_id, status, created_at FROM opm_sesi ORDER BY created_at DESC;
```
Bandingkan jumlah baris riil vs. 2 baris yang tampil di UI. Cek juga apakah baris untuk
`jbt_67d83915`, `jbt_4c034eef`, `jbt_0e87bc6b` benar-benar ada.

### Langkah 2 — Verifikasi versi & topologi deployment backend

- Cek image/tag yang benar-benar berjalan di container produksi vs. commit `HEAD` repo lokal.
- Cek apakah ada lebih dari satu instance backend (replica) yang mengarah ke DB berbeda, atau
  cache/connection-pool yang stale.
- Konfirmasi `GET /openapi.json` produksi (`version` field) — apakah `0.26.0` cerminan versi
  runtime sungguhan atau sekadar string yang tidak ter-bump saat release (lihat fakta #9).

### Langkah 3 — Setelah akar masalah dikonfirmasi, baru tentukan perbaikan

Kemungkinan hasil dan tindak lanjutnya:
- **Bila row memang ada & DB konsisten** → bug ada di endpoint listing (`sesi_sql.py:109-118`
  atau frontend `page.tsx`) meski review statis tidak menemukannya — perlu debug lebih dalam
  (mis. exception ditelan diam-diam, response di-`transform` di lapisan lain yang belum
  ditemukan Explore agent).
- **Bila DB benar-benar hanya 2 baris** → bug ada di endpoint create/pre-check (409 salah
  positif) — kemungkinan besar di layer cache/idempotency atau di instance backend yang
  berbeda dari yang melayani listing.
- **Bila ada >1 instance/DB tidak sinkron** → ini murni isu infra/deployment, bukan kode;
  eskalasi ke pemilik deployment (`copier-docker-compose-skill`/ops), bukan item backlog kode.

## Kriteria penerimaan

- [ ] Root cause dikonfirmasi via akses live (bukan dugaan dari pembacaan kode statis)
- [ ] `POST /api/v1/opm/sesi` untuk jabatan yang belum pernah punya Analisis Jabatan OPM
      berhasil (201), tidak 409
- [ ] `GET /api/v1/opm/sesi` menampilkan SEMUA sesi OPM yang benar-benar ada di DB (verifikasi
      count cocok dengan query SQL langsung)
- [ ] Simulasi ulang: buat Analisis Jabatan OPM untuk salah satu dari 3 jabatan di atas
      (Pembina OSIS / Guru Mapel SMP / Koordinator Pramuka — ketiganya sudah punya TI
      Tahap 3/Teranalisis, siap dipakai sbg sumber) berhasil sampai ke halaman Hasil

## Skenario uji

- Test regresi baru di `anjab-abk-backend` yang membuktikan `list()` mengembalikan seluruh
  baris tanpa filter tersembunyi (harus sudah lulus berdasar temuan #7, tapi tambahkan test
  eksplisit jumlah baris vs `total` bila belum ada)
- Bila akar masalah di layer lain (cache/infra), test tidak relevan — dokumentasikan mitigasi
  infra sebagai gantinya

## Definition of done

- [ ] `make test` hijau di repo terkait (bila perubahan kode diperlukan)
- [ ] `CHANGELOG.md` diperbarui
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Update 2026-07-14 (sesi kedua) — bug dikonfirmasi masih terjadi, 2 jabatan baru

Simulasi ulang SOP TI + OPM dijalankan lagi pada hari yang sama, sengaja dengan **jabatan &
panel yang berbeda** dari percobaan pertama (Wali Kelas `jbt_59eb604e`, Guru Kelas SD
`jbt_1af01170` — bukan Pembina OSIS/Guru Mapel SMP/Koordinator Pramuka), untuk memastikan bug
409 bukan kebetulan terkait 3 jabatan spesifik sebelumnya.

- `POST /api/v1/opm/sesi` untuk `jabatan_id=jbt_1af01170` (Guru Kelas SD — TI baru sukses penuh
  sampai **Teranalisis** hari ini juga, jadi mustahil sudah punya OPM lama) → toast
  `"Sesi OPM untuk jabatan 'jbt_1af01170' sudah ada."`
- `POST /api/v1/opm/sesi` untuk `jabatan_id=jbt_59eb604e` (Wali Kelas) → 409 identik
- `GET /opm` (listing) tetap hanya menampilkan **2 baris** yang sama seperti percobaan pertama
  (`jbt_16548582`, `jbt_b2482c0a`) — kedua jabatan baru ini TIDAK PERNAH muncul
- Total sekarang **5 jabatan berbeda** (3 dari percobaan pertama + 2 ini) mengalami 409 yang
  sama, memperkuat kesimpulan bug **sistemik**, bukan terkait data lama jabatan tertentu

**Status backlog TIDAK berubah** — root cause tetap belum terverifikasi (masih butuh akses
produksi langsung sesuai "Langkah eksekusi" di atas), update ini hanya menambah bukti reproduksi.
Detail lengkap sesi kedua: memori `ti-opm-test-2-2026-07-14`.

## Risiko & catatan

- **Dampak bisnis langsung**: seluruh alur OPM (tahap terakhir sebelum ABK bisa dianalisis
  penuh untuk suatu jabatan) tidak bisa dijalankan untuk jabatan baru mana pun selama bug ini
  belum diperbaiki — ini **memblokir studi ANJAB/ABK YPII yang sedang berjalan**, bukan
  sekadar bug kosmetik.
- **3 sesi TI produksi ikut terpakai untuk simulasi ini** (data uji coba, bukan data asli):
  Pembina OSIS (`tises_01ff14d5`), Guru Mapel SMP (`tises_772a3442`), Koordinator Pramuka
  (`tises_c46aa659`) — ketiganya sudah **Teranalisis** dengan jawaban acak dari 2 partisipan
  per sesi (bukan seluruh anggota panel asli). `min_responden` masing-masing diset 2 (bukan
  default 3) untuk keperluan tes — **tidak dikembalikan** karena TI (beda dari DCS/WCP) bukan
  singleton; sesi baru bisa dibuat kapan saja untuk studi asli tanpa bentrok dengan sesi tes
  ini. Lihat detail penuh & daftar responden test di memory `ti-opm-test-run-2026-07-14`.
- **Jangan asumsikan 2 sesi OPM yang TERLIHAT di listing (`jbt_16548582`, `jbt_b2482c0a`)
  aman disentuh** — statusnya Teranalisis/Terbuka dengan data yang belum diverifikasi asli
  atau uji coba; jangan hapus/ubah tanpa konfirmasi eksplisit dari pemilik data.
- Item ini **secara eksplisit bukan "siap dieksekusi"** dalam pengertian normal template —
  langkah pertama adalah investigasi manusia dengan akses produksi, bukan penulisan kode oleh
  agen. Sonnet yang mengambil item ini harus berhenti di Langkah 1-2 dan melapor balik hasil
  temuan sebelum menulis kode apa pun.
