# Backlog 032 — Web app: ±20 berkas jalur baca masih `toApiError(null, reqId)` (membuang pesan & status backend), + 1 pengecualian 026 yang menelan semua status

> **Repo:** `anjab-abk-web-app`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Dua utang yang **sengaja tidak dikerjakan** oleh agen pelaksana backlog **031** — dilaporkan terus
terang alih-alih diam-diam diperluas ke dalam diff-nya. Keduanya nyata, keduanya kecil, dan keduanya
melanggar invariant yang sudah dikunci di `CLAUDE.md` web-app.

### Utang 1 — `toApiError(null, reqId)` membuang pesan & status backend (±20 berkas)

Berkas-berkas ini **melempar** saat gagal (jadi **tidak** menelan error — di luar cakupan 026/031),
tapi memakai pola lama `toApiError(null, reqId)` yang **membuang dua hal sekaligus**: pesan error
dari backend **dan** status HTTP-nya. Akibatnya pengguna melihat pesan generik, dan kode pemanggil
tidak bisa membedakan 401 dari 403 dari 500 — padahal `CLAUDE.md` sendiri melarang ini untuk jalur
baca, dan penggantinya (`apiErrorDari(res)`, dari backlog 026) sudah ada dan sudah dipakai di
berkas-berkas yang tersentuh 026/029/030/031.

Ini yang membuat pesan 422 backend 028 ("Jumlah anggota SME panel (11) melebihi max_responden (10)")
**berisiko tidak sampai utuh** di jalur-jalur yang belum dimigrasikan.

### Utang 2 — pengecualian 026 di Tahap 2 menelan **semua** status, bukan hanya 404

`sayaRes.data?.id ?? null` di jalur Tahap 2 didaftarkan sebagai **pengecualian sah** di backlog 026
(dengan alasan: 404 wajar untuk admin yang bukan partisipan). Tapi implementasinya **menelan semua
status** — **401 pun jadi `null`**, bukan hanya 404. Instruksi eksekusi 031 melarang menyentuhnya
(agar pengecualian 026 tidak diregresikan), jadi agen mengunci saja lewat daftar `PENGECUALIAN` di
jaring pengaman supaya tetap **terlihat**. Sekarang saatnya ditinjau benar.

## Kondisi sekarang (verified)

| # | Fakta | Verifikasi |
|---|---|---|
| 1 | ±20 berkas jalur baca masih memakai `toApiError(null, reqId)`; berkas yang tersentuh 026/029/030/031 sudah dimigrasikan ke `apiErrorDari(res)` | ✓ audit agen pelaksana 031, 2026-07-14 |
| 2 | `toApiError(null, …)` membuang pesan backend **dan** status HTTP; `apiErrorDari(res)` mempertahankan keduanya + `X-Request-ID` (`src/lib/api/errors.ts`, dari 026) | ✓ dibaca langsung |
| 3 | Berkas-berkas ini **melempar** (tidak menelan) → **bukan** bug telan-senyap, jadi memang di luar cakupan 026/031 | ✓ idem |
| 4 | `sayaRes.data?.id ?? null` (Tahap 2) menelan **semua** status termasuk 401, bukan hanya 404 sebagaimana diklaim alasan pengecualiannya di 026 | ✓ agen 031, dilaporkan terus terang |
| 5 | Jaring pengaman `src/test/jaring-pengaman-jalur-baca.test.ts` (dari 031) sudah mengunci keduanya lewat daftar `PENGECUALIAN` yang eksplisit — jadi tidak bisa hilang dari radar | ✓ |

## Keputusan yang sudah dikunci

- **Utang 1 adalah refactor mekanis** — nilainya tinggi, risikonya rendah, tapi diff-nya lebar.
  Kerjakan sebagai item sendiri (persis alasan agen 031 tidak menyeretnya masuk): mengganti pola di
  ±20 berkas di tengah diff 031 akan mengaburkan review perubahan yang substantif.
- **Utang 2 harus dipersempit, bukan dihapus.** Pengecualiannya **sah** untuk 404 (admin bukan
  partisipan adalah kondisi normal) — yang salah adalah cakupannya. Perbaikannya: **hanya 404** yang
  jadi `null`; 401/403/5xx melempar. Jangan menghapus pengecualiannya sama sekali (itu akan
  mematikan halaman Tahap 2 untuk admin).
- Setelah keduanya beres, **kurangi daftar `PENGECUALIAN`** di jaring pengaman 031 sesuai kenyataan
  baru — jangan biarkan daftar itu membusuk jadi izin permanen.

## Langkah eksekusi

### Langkah 1 — Migrasikan `toApiError(null, …)` → `apiErrorDari(res)`

`grep -rn "toApiError(null" src/app` — untuk setiap kemunculan di **jalur baca**, ganti dengan
`apiErrorDari(res)`. Pastikan `res` (objek respons openapi-fetch) memang tersedia di scope; bila
tidak, itu tanda pemanggilnya perlu dirapikan lebih dulu.

Bila ada pemakaian `toApiError` yang **sah** (mis. jalur non-HTTP), pertahankan dan catat alasannya.
Bila nol yang tersisa, **hapus** ekspor `toApiError` — mengikuti pola 029 yang menghapus ekspor
klien `api` telanjang agar pola lamanya mustahil dipakai lagi.

### Langkah 2 — Persempit pengecualian Tahap 2 ke 404 saja

Ubah `sayaRes.data?.id ?? null` menjadi: **404 → `null`**; status lain → `throw apiErrorDari(res)`.
Tambah test: admin (404) → halaman tetap render; partisipan dengan 401 → **error terlihat**, bukan
`null` senyap.

### Langkah 3 — Rapikan daftar `PENGECUALIAN` jaring pengaman

Perbarui `src/test/jaring-pengaman-jalur-baca.test.ts`: buang entri yang sudah tidak berlaku.

## Kriteria penerimaan

- [ ] `grep -rn "toApiError(null" src/app` → nol (atau hanya kemunculan yang alasannya dicatat)
- [ ] Pesan error backend (mis. 422 dari backlog 028) tampil **utuh** ke pengguna di seluruh jalur
      baca, lengkap dengan `X-Request-ID`
- [ ] Tahap 2: admin (404) tetap bisa membuka halaman; 401/403/5xx → error terlihat, bukan `null`
- [ ] Daftar `PENGECUALIAN` di jaring pengaman menyusut sesuai kenyataan

## Skenario uji

- Test: jalur baca yang dimigrasikan → backend balas 422 dgn pesan → assert pesan **backend** yang
  tampil (bukan pesan generik) + status + `X-Request-ID`.
- Test: Tahap 2, `GET /partisipan/saya` → 404 → halaman render (admin). → 401 → melempar.
- `make test` hijau + `npm run build` sukses.

## Definition of done

- [ ] `make test` hijau, `npm run build` sukses
- [ ] `CHANGELOG.md` diperbarui
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- Lahir sebagai **utang yang dilaporkan terus terang** oleh agen pelaksana 031 (2026-07-14), bukan
  dari laporan pengguna. Agen itu sengaja **tidak** memperluas diff-nya dengan refactor mekanis di
  luar mandat — keputusan yang benar; item ini menagihnya.
- Utang 2 adalah pengingat bahwa **daftar pengecualian bisa berbohong**: alasan yang ditulis di 026
  ("404 sah") **tidak sama** dengan yang dilakukan kode (menelan semua status). Saat menambah
  pengecualian, verifikasi implementasinya benar-benar sesempit alasannya.
