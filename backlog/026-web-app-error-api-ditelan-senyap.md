# Backlog 026 — Web app: halaman Tahap 1/Tahap 3 menelan error API secara senyap (`?? []`) & error mentah untuk non-pemilik

> **Repo:** `anjab-abk-web-app`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Terkait:** backlog **024** (Tahap 3 menampilkan 0 task) — item ini adalah **sebab kenapa
> bug 024 tampil sebagai "0 task" alih-alih pesan error**, tapi keduanya berdiri sendiri.
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Dua cacat penanganan error di halaman partisipan Task Inventory:

1. **Error ditelan senyap.** Di `tahap3/[responden_id]/page.tsx`, daftar task diambil dengan
   `terpilih = (ttRes.data ?? []) as TiTaskTerpilihRead[]` — **respons gagal apa pun**
   (401/403/422/500) menghasilkan array kosong, dan halaman merender **"Ditandai dikerjakan:
   0 dari 0 task"** dengan daftar kosong, **tanpa pesan error apa pun**. Partisipan melihat
   formulir yang tampak sah tapi kosong; admin tidak punya petunjuk bahwa ada yang salah. Pola
   `?? []` yang sama juga dipakai untuk `detail` di berkas itu, dan untuk `catalog`/`terpilih`
   di `tahap1/[responden_id]/page.tsx`.
2. **Error mentah untuk non-pemilik.** Saat pengguna yang **bukan** pemilik `responden_id`
   membuka halaman Tahap 1, halaman menampilkan **"Gagal memuat Tahap 1."** + pesan digest
   React mentah ("An error occurred in the Server Components render… A digest property is
   included…"), bukan 403/404 yang rapi. Bandingkan dengan Tahap 2 yang sudah menangani ini
   dengan benar (mode baca-saja untuk anggota panel, `notFound()` untuk non-anggota — lihat
   `docs-usage/ik/task-inventory.md` bagian D ✓).

Ini bertentangan langsung dengan prinsip yang sudah dikunci di repo ini pada backlog **017**
(entri `[2026-07-14]` di `CLAUDE.md` web-app ✓): *"error ditelan"* dan *"pesan sukses bohong"*
adalah bug yang secara eksplisit sudah diberantas di call-site **mutasi** — tapi jalur **baca**
di Server Component belum ikut dibereskan.

## Kondisi sekarang (verified)

| # | Fakta | Verifikasi |
|---|---|---|
| 1 | `src/app/(auth)/task-inventory/tahap3/[responden_id]/page.tsx` — `fetchPageData()`: `responden` & `sesi` **melempar** bila gagal (`if (!respRes.data) throw toApiError(...)`), tapi `terpilih` memakai `(ttRes.data ?? [])` dan `detail` memakai `(detailRes.data ?? [])` → **gagal = senyap** | ✓ dibaca langsung |
| 2 | Endpoint `GET /api/v1/task-inventory/sesi/{sesi_id}/task-terpilih` **bisa** mengembalikan 403 (`authorize_sesi_access()`, `anjab-abk-backend/src/anjab_abk_backend/api/v1/taskinv_hasil.py:78` ✓) dan 422 (bila status sesi belum TAHAP3, `taskinv_hasil.py:79-82` ✓) — keduanya saat ini tampil sebagai "0 task", bukan error | ✓ dibaca langsung di backend |
| 3 | `src/app/(auth)/task-inventory/tahap1/[responden_id]/page.tsx` — `catalog` (`catalogRes.data ?? []`) dan `terpilih` (`?? []`) memakai pola telan-senyap yang sama | ✓ dibaca langsung |
| 4 | Reproduksi produksi 2026-07-14: sesi TI Wali Kelas (`tises_434a8864`) berstatus TAHAP3 dengan **19 task terpilih** (dikonfirmasi di halaman admin & dropdown OPM), tapi **seluruh 7 responden** melihat "0 dari 0 task" di halaman Tahap 3 — tanpa satu pun pesan error di layar maupun di console | ✓ Playwright, lihat backlog 024 |
| 5 | Reproduksi produksi 2026-07-14: login sebagai partisipan A lalu membuka URL Tahap 1 milik partisipan B → **"Gagal memuat Tahap 1."** + teks digest React mentah | ✓ Playwright, snapshot halaman |
| 6 | Pembanding yang **sudah benar**: `tahap2/[sesi_id]/page.tsx` memisahkan peran (admin / koordinator / anggota panel read-only / bukan anggota → `notFound()`) dan tidak memakai `?? []` untuk data kritis | ✓ dibaca langsung |

## Keputusan yang sudah dikunci

- **Jangan** "memperbaiki" ini dengan menampilkan daftar kosong + banner peringatan. Bila data
  task **gagal diambil**, halaman harus **gagal secara terlihat** (error boundary dengan pesan
  yang bisa ditindaklanjuti), karena merender formulir kosong yang tampak sah adalah bentuk
  *notifikasi bohong* — persis yang dilarang backlog 017.
- **Bedakan dua kondisi yang sah** dari kondisi error:
  - Sesi **belum** TAHAP3 → sudah ditangani (halaman hanya memanggil `task-terpilih` bila
    status ∈ TAHAP3/CLOSED/ANALYZED) — pertahankan.
  - Sesi TAHAP3 tapi task terpilih **benar-benar 0** (koordinator menolak semua) → kondisi sah,
    tampilkan pesan eksplisit ("Tidak ada task final untuk sesi ini"), **bukan** formulir kosong.
  - Panggilan **gagal** (4xx/5xx) → lempar, tampilkan error.
- `X-Request-ID` wajib ikut tampil di pesan error (pola `notifyGagal`/`ApiError.requestId` yang
  sudah ada), supaya user bisa menyebutkannya saat melapor.

## Langkah eksekusi

### Langkah 1 — Hentikan telan-senyap di Tahap 3

Di `tahap3/[responden_id]/page.tsx` `fetchPageData()`, ubah pengambilan `terpilih` & `detail`
agar **melempar** saat respons gagal, mengikuti pola `responden`/`sesi` yang sudah ada di berkas
yang sama:

```ts
const ttRes = await client.GET("/api/v1/task-inventory/sesi/{sesi_id}/task-terpilih", { ... });
if (!ttRes.data) throw toApiError(null, ttRes.response.headers.get("x-request-id"));
terpilih = ttRes.data as TiTaskTerpilihRead[];
```

Catatan: `?? []` untuk `detail` (isian CalHR yang sudah tersimpan) **juga** harus melempar —
responden yang belum mengisi tetap mendapat `200` dengan array kosong, jadi array kosong yang sah
tetap terbedakan dari kegagalan.

### Langkah 2 — Hal yang sama di Tahap 1

Idem untuk `catalog` dan `terpilih` di `tahap1/[responden_id]/page.tsx`.

### Langkah 3 — Kondisi "0 task final" yang sah

Di komponen Tahap 3, bila `terpilih.length === 0` **dan** status sesi TAHAP3/CLOSED/ANALYZED,
render pesan eksplisit (mis. kotak kuning: *"Tidak ada task final pada analisis ini — koordinator
tidak menyetujui satu pun task partial. Hubungi administrator."*) alih-alih formulir kosong
dengan tombol Simpan/Kirim yang menyesatkan.

### Langkah 4 — 403 rapi untuk non-pemilik (Tahap 1 & Tahap 3)

Tangkap `ForbiddenError`/403 dari `toApiError` dan render halaman "tidak berhak" yang rapi
(atau `notFound()`), mengikuti perlakuan Tahap 2. Jangan biarkan bocor jadi digest error React.
Periksa `error.tsx` di kedua route — kemungkinan cukup membedakan status di sana.

### Langkah 5 — Audit pola `?? []` di seluruh jalur baca

`grep -rn "\.data ?? \[\]" src/app` — tinjau **setiap** kemunculan: mana yang menelan kegagalan
data kritis, mana yang memang aman (data opsional). Perbaiki yang kritis. Catat pola larangan di
`CLAUDE.md` web-app agar tidak muncul lagi.

## Kriteria penerimaan

- [ ] Halaman Tahap 3 dengan endpoint `task-terpilih` gagal (403/500) → menampilkan **error yang
      terlihat** beserta `X-Request-ID`, **bukan** "0 dari 0 task"
- [ ] Halaman Tahap 3 dengan 0 task final yang sah → pesan eksplisit, bukan formulir kosong
- [ ] Partisipan membuka URL Tahap 1/Tahap 3 milik orang lain → halaman "tidak berhak"/404 yang
      rapi, **bukan** digest error React mentah
- [ ] Alur normal (sesi Guru Kelas SD di produksi, 15 task) tetap berjalan seperti sekarang
- [ ] `grep -rn "\.data ?? \[\]" src/app` → tidak ada lagi kemunculan yang menelan data kritis

## Skenario uji

- `src/test/` — test baru untuk `fetchPageData` Tahap 3: mock `client.GET` mengembalikan
  `{data: undefined, response: 403}` untuk `task-terpilih` → assert **melempar** (bukan
  mengembalikan `[]`).
- Test komponen: `terpilih = []` + status TAHAP3 → merender pesan "tidak ada task final", dan
  tombol "Kirim Detail" **tidak** aktif.
- E2E/`vitest` sesuai pola berkas test yang sudah ada (`transisi-sesi.test.tsx`,
  `review-form.test.tsx`).
- `make test` hijau + `npm run build` sukses.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-web-app`, `npm run build` sukses
- [ ] `CHANGELOG.md` diperbarui
- [ ] `CLAUDE.md` web-app diperbarui: tambah invariant "jalur baca Server Component dilarang
      memakai `?? []` untuk data kritis — gagal harus melempar" (sejajar dengan aturan toast
      dari backlog 017)
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Item ini tidak memperbaiki backlog 024.** Setelah 026 selesai, sesi Wali Kelas
  (`tises_434a8864`) akan menampilkan **pesan error yang jelas** alih-alih "0 task" senyap — itu
  justru yang akan **mengungkap** penyebab sebenarnya (403? 500? 422?) dan mempercepat 024.
  Kerjakan 026 **lebih dulu**, lalu buka lagi halaman Tahap 3 sesi itu untuk membaca error yang
  sesungguhnya.
- Perubahan ini membuat halaman yang tadinya "berhasil dirender kosong" menjadi **gagal
  terlihat**. Itu **disengaja** — tapi berarti bila ada sesi produksi lain yang diam-diam
  mengalami masalah yang sama, ia akan mulai menampilkan error setelah deploy. Itu perbaikan,
  bukan regresi; siapkan penjelasannya untuk user.
