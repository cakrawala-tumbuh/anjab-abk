# Backlog 018 — Backend: assign responden DCS & WCP kembalikan `BulkAssignResult` (dengan `skipped[]`)

> **Repo:** `anjab-abk-backend`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `backend-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

`POST /api/v1/dcs/responden` dan `POST /api/v1/wcp/responden` menerima banyak `partisipan_ids`
sekaligus, tapi hanya mengembalikan **daftar responden yang berhasil dibuat** — partisipan yang
di-*skip* (sudah terdaftar, tidak memenuhi syarat, dll.) hilang tanpa jejak dari response.

Akibatnya web app tidak bisa memberi tahu user apa pun soal yang di-skip: memilih 10 partisipan lalu
7 di antaranya di-skip terlihat **persis sama** dengan sukses penuh — bahkan hasil **0 dibuat** pun
tidak bisa dibedakan. Ini melanggar prinsip yang sedang ditegakkan di item **017** (setiap
penyimpanan data harus punya notifikasi yang jujur ke user).

Endpoint bulk lain sudah benar dan menjadi acuan: TI, OPM, dan Time Study semuanya mengembalikan
`BulkAssignResult` yang memuat `created[]` **dan** `skipped[]` beserta alasannya.

## Keputusan yang sudah dikunci

1. Response DCS/WCP diseragamkan ke **`BulkAssignResult`** generik yang sudah ada — **jangan** membuat
   skema baru dengan bentuk berbeda.
2. Alasan skip memakai **enum alasan yang sudah dipakai** endpoint bulk TI/OPM/TS. Web app sudah punya
   `formatAlasanSkip()` yang memetakannya ke Bahasa Indonesia — enum baru berarti web app harus ikut
   berubah, hindari kecuali memang ada alasan skip yang khas DCS/WCP.
3. **Breaking change diterima.** Response berubah dari `DcsRespondenRead[]` menjadi objek
   `BulkAssignResult`. Konsumen (`anjab-abk-web-app`, `anjab-abk-mcp`) menyesuaikan setelahnya — lihat
   item **019**. Tidak perlu jalur kompatibilitas / versi endpoint baru: ini deployment tunggal per
   studi, ketiga repo dirilis bersama.
4. Status code tetap **201**.

## Kondisi sekarang (verified)

✓ Dibaca dari `anjab-abk-web-app/openapi/openapi.json` pada 2026-07-13:

| Endpoint | Response 201 sekarang |
|---|---|
| `POST /api/v1/dcs/responden` | `array` of `DcsRespondenRead` — **tanpa `skipped`** |
| `POST /api/v1/wcp/responden` | `array` of `WcpRespondenRead` — **tanpa `skipped`** |
| `POST /api/v1/opm/sesi/{sesi_id}/responden/bulk` | `BulkAssignResult_OpmRespondenRead_` ✓ acuan |

Agen pelaksana **wajib** membaca ulang di repo backend:

- Router & service DCS: `app/dcs/` (cari handler `responden_create`).
- Router & service WCP: `app/wcp/`.
- Skema `BulkAssignResult` generik + enum alasan skip: cari lewat
  `grep -rn "BulkAssignResult\|AlasanSkip" app/` — pola persisnya ada di implementasi bulk TI/OPM/TS
  (item **005**).
- Constraint yang relevan: `dcs/services/responden_sql.py` memaksa satu partisipan hanya boleh jadi
  responden di **seluruh** sesi DCS (global) — ini sumber utama skip "sudah terdaftar".

## Langkah eksekusi

### Langkah 1 — Samakan service DCS & WCP dengan pola bulk TI/OPM/TS

Ubah service `responden_create` DCS & WCP agar, alih-alih men-skip diam-diam, ia mengumpulkan tiap
`partisipan_id` yang tidak jadi dibuat ke dalam daftar `skipped` beserta alasannya, dan mengembalikan
`BulkAssignResult` (`created` + `skipped`).

Baca implementasi bulk OPM lebih dulu dan **tiru strukturnya persis** — termasuk penamaan field dan
enum alasan.

### Langkah 2 — Ubah response_model router DCS & WCP

`response_model=list[DcsRespondenRead]` → `response_model=BulkAssignResult[DcsRespondenRead]`
(sesuaikan dengan bentuk generic yang dipakai OPM). Idem WCP.

### Langkah 3 — Regenerasi `openapi.json`

Jalankan perintah regenerasi OpenAPI yang berlaku di repo (lihat `Makefile`). Diff yang diharapkan
**hanya** menyentuh dua endpoint di atas + skema `BulkAssignResult_DcsRespondenRead_` /
`BulkAssignResult_WcpRespondenRead_` baru.

## Kriteria penerimaan

- [ ] `POST /api/v1/dcs/responden` dan `POST /api/v1/wcp/responden` mengembalikan objek dengan field
      `created[]` dan `skipped[]`, status 201.
- [ ] Tiap entri `skipped` memuat `partisipan_id` + `alasan` (enum yang sama dengan bulk TI/OPM/TS).
- [ ] Partisipan yang sudah terdaftar sebagai responden DCS → muncul di `skipped`, **bukan** hilang.
- [ ] `openapi.json` diregenerasi; diff terbatas pada dua endpoint tsb + skema barunya.

## Skenario uji

- Assign 3 partisipan, 0 sudah terdaftar → `created` 3, `skipped` kosong.
- Assign 3 partisipan, 2 sudah terdaftar → `created` 1, `skipped` 2 dengan alasan "sudah terdaftar".
- Assign 2 partisipan, **semua** sudah terdaftar → `created` kosong, `skipped` 2, tetap **201**
  (bukan 4xx — ini bukan error, hanya nihil hasil).
- Idem untuk WCP.

Perintah: `make test` di `anjab-abk-backend`.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-backend`
- [ ] `openapi.json` diregenerasi
- [ ] `CHANGELOG.md` diperbarui — tandai sebagai **breaking change** pada response dua endpoint
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Breaking change** — begitu ini dirilis, `dcs/assign-responden.tsx` & `wcp/assign-responden.tsx` di
  web app akan menerima objek padahal mengharapkan array. Item **019** harus menyusul di rilis yang
  sama; jangan rilis 018 sendirian ke deployment yang sudah jalan.
- Cek juga apakah `anjab-abk-mcp` memanggil kedua endpoint ini (`grep -rn "dcs/responden\|wcp/responden"`
  di repo MCP). Bila ya, MCP butuh item penyesuaian sendiri — **satu item = satu repo**.
