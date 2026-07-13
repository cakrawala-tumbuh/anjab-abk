# Backlog 003 — Web app: hapus UI sesi DCS & WCP, tambah halaman hasil agregat

> **Repo:** `anjab-abk-web-app`
> **Status:** Menunggu (blocked by 001)
> **Blocked by:** 001 — butuh `openapi.json` backend baru untuk regen `schema.ts`.
> **Skill:** `frontend-development-skill`, `automated-test-skill`, `dokumentasi-penggunaan-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Menghapus seluruh permukaan UI "sesi" dari DCS & WCP. Alur admin turun dari **4 langkah** (buat sesi →
isi form → buka sesi → tambah responden satu per satu) jadi **1 langkah**: buka `/dcs`, pilih
partisipan, assign. Sekalian **menutup gap yang sudah ada**: DCS & WCP saat ini tidak punya halaman
hasil agregat maupun tombol "Jalankan Analisis" sama sekali (tidak seperti OPM/TI) — `transisi-sesi.tsx`
malah menyuruh user "jalankan analisis dari backend".

## Keputusan yang sudah dikunci

1. `/dcs` **bukan lagi listing sesi**, melainkan **halaman instrumen tunggal**: status + daftar responden
   + form assign + tombol Tutup/Buka-ulang + tombol Jalankan Analisis.
2. Form assign responden **multi-select** (bulk), bukan satu-per-submit seperti sekarang.
3. Route `/dcs/buat` dan `/dcs/[sesi_id]` **dihapus**.
4. **Tambah** `/dcs/hasil` — halaman hasil agregat (mean/stdev per subskala, Cronbach alpha, risk flag,
   K-Index). Ini fitur baru, bukan sekadar pemindahan.
5. Halaman pengisian partisipan `/dcs/isi/[responden_id]` **tidak berubah** (tidak pernah menyentuh sesi).
6. Halaman TI & OPM **tidak disentuh**. Perubahan terminologi TI/OPM ada di item 004, terpisah.

## Kondisi sekarang (verified per 2026-07-12)

| Fakta | Lokasi |
|---|---|
| Listing sesi DCS (tabel, `limit: 100`) | `src/app/(auth)/dcs/page.tsx` ✓ |
| Form buat sesi (periode, min/max responden, catatan) | `src/app/(auth)/dcs/buat/page.tsx`, `dcs-sesi-form.tsx` ✓ |
| Detail sesi: transisi, tambah/hapus responden | `src/app/(auth)/dcs/[sesi_id]/page.tsx`, `transisi-sesi.tsx`, `tambah-responden.tsx`, `hapus-responden.tsx` ✓ |
| Tambah responden = **1 partisipan per submit**, tidak ada bulk | `dcs/[sesi_id]/tambah-responden.tsx` ✓ |
| `transisi-sesi.tsx` DCS/WCP **tidak punya** tombol "Jalankan Analisis"; teksnya menyuruh jalankan dari backend & "lihat hasil di halaman laporan" — **halaman itu tidak ada** | `dcs/[sesi_id]/transisi-sesi.tsx` ✓ |
| Hasil per-responden (satu-satunya halaman hasil DCS) | `dcs/[sesi_id]/hasil-responden/[responden_id]/page.tsx` ✓ |
| Pengisian partisipan (tidak menyentuh sesi) | `dcs/isi/[responden_id]/page.tsx`, `dcs-form.tsx` ✓ |
| WCP: struktur file **identik** DCS | `src/app/(auth)/wcp/**` ✓ |
| "Kuesioner Saya" — partisipan tidak pernah memilih sesi; kartu diberi label `sesi_catatan ?? sesi_periode` + badge `sesi_status` | `src/app/(auth)/kuesioner/page.tsx:59-64` ✓ |
| Menu sidebar admin per alat ukur | `src/components/shell/sidebar.tsx` (`NAV_ADMIN`) ✓ |
| **Acuan pola tanpa sesi** (baca dulu!) | `src/app/(auth)/time-study/**` — listing penugasan + toggle aktif ✓ |
| Master data DCS/WCP (`/master-data/dcs`, `/master-data/wcp`) | **tidak terpengaruh** ✓ |

## Langkah eksekusi

### Langkah 1 — Regen tipe API

Setelah item 001 merge: salin `openapi.json` backend terbaru ke `openapi/` dan regen `schema.ts`
(jangan menyalin tipe manual — patuhi `frontend-development-skill`). Semua tipe di bawah harus datang
dari sana: `DcsInstrumenRead`, `DcsRespondenRead`, `DcsRespondenCreate`, hasil agregat DCS/WCP.

### Langkah 2 — `/dcs` jadi halaman instrumen (bukan listing)

Tulis ulang `src/app/(auth)/dcs/page.tsx`. Isinya:

- **Kartu status**: badge `OPEN | CLOSED | ANALYZED`, `min_responden`, `catatan`, jumlah responden
  ber-submit vs total (mis. "4 dari 7 sudah mengisi — minimal 6 untuk analisis").
- **Tabel responden**: nama, jabatan, status submit, aksi hapus (hapus hanya bila belum submit).
- **Form assign** (`assign-responden.tsx`, komponen baru menggantikan `tambah-responden.tsx`):
  **multi-select partisipan** → satu submit → `POST /dcs/responden` dengan `partisipan_ids`.
  Sembunyikan partisipan yang sudah ter-assign dari daftar pilihan.
- **Aksi instrumen** (`aksi-instrumen.tsx`, menggantikan `transisi-sesi.tsx`):
  - `OPEN` → tombol **"Tutup Pengisian"** (konfirmasi: setelah ditutup partisipan tidak bisa mengisi lagi)
  - `CLOSED` → tombol **"Jalankan Analisis"** (aktif hanya bila submit ≥ `min_responden`; kalau kurang,
    tampilkan alasan disable) + tombol **"Buka Ulang"**
  - `ANALYZED` → tautan **"Lihat Hasil"** ke `/dcs/hasil`
- **Edit `min_responden`/`catatan`** → `PATCH /dcs/instrumen` (form kecil, boleh inline).

Hapus: `dcs/buat/` (seluruh direktori), `dcs/[sesi_id]/page.tsx`, `transisi-sesi.tsx`,
`tambah-responden.tsx`. Pindahkan `hapus-responden.tsx` ke `dcs/`.

### Langkah 3 — Pindahkan & tambah halaman hasil

- Pindah: `dcs/[sesi_id]/hasil-responden/[responden_id]/` → `dcs/hasil-responden/[responden_id]/`
  (konten sama, hanya buang `sesi_id` dari param & fetch).
- **Baru**: `dcs/hasil/page.tsx` — hasil agregat dari `GET /dcs/hasil`. Tampilkan per subskala: mean,
  stdev, Cronbach alpha, `risk_flag`; plus `k_index` di tingkat atas. Tiru tata letak
  `opm/[sesi_id]/hasil/page.tsx` yang sudah ada — jangan bikin bahasa visual baru.
  Halaman ini hanya bisa diakses saat status `ANALYZED`; selain itu redirect ke `/dcs`.
- Wajib ada `loading.tsx` + `error.tsx` di tiap route baru (pola repo).

### Langkah 4 — Cermin untuk WCP

`src/app/(auth)/wcp/**` — sama persis, minus K-Index (K-Index hanya ada di hasil DCS).

### Langkah 5 — "Kuesioner Saya"

`src/app/(auth)/kuesioner/page.tsx`: kartu DCS & WCP kini memakai `instrumen_status` + `catatan`
(field `sesi_*` sudah tidak ada). Karena instrumen singleton, **maksimal satu kartu DCS dan satu kartu
WCP** per partisipan — bug lama "kartu ganda kalau di-assign ke >1 sesi" hilang dengan sendirinya.
Pastikan tidak ada lagi `.map()` yang mengasumsikan banyak sesi.

### Langkah 6 — Dokumentasi & test

- `docs-usage/`: perbarui panduan pengguna DCS & WCP (alur admin berubah total) — pakai
  `dokumentasi-penggunaan-skill`.
- `CHANGELOG.md`.
- `CLAUDE.md` web-app: catat alur baru.

## Kriteria penerimaan

- [ ] Tidak ada route `/dcs/buat`, `/dcs/[sesi_id]`, `/wcp/buat`, `/wcp/[sesi_id]`.
- [ ] Admin baru bisa membuat 6 partisipan mengisi DCS **tanpa pernah menyentuh konsep sesi**, dalam
      satu halaman.
- [ ] Admin bisa menjalankan analisis DCS **dari UI** (sekarang tidak bisa sama sekali).
- [ ] `/dcs/hasil` menampilkan alpha & K-Index setelah analisis.
- [ ] Halaman TI & OPM tidak berubah perilakunya.
- [ ] Tidak ada `schema.ts` yang di-edit tangan.

## Skenario uji

Unit (vitest) + E2E (Playwright), lewat `make test` (Docker) sesuai `automated-test-skill`.

1. **E2E alur admin DCS**: login admin → `/dcs` → assign 6 partisipan sekaligus → tabel menampilkan 6
   baris → (seed jawaban) → "Tutup Pengisian" → "Jalankan Analisis" → `/dcs/hasil` menampilkan alpha.
2. **E2E partisipan**: `/kuesioner` menampilkan tepat satu kartu DCS → "Isi Sekarang" → submit → kartu
   berubah jadi "sudah diisi".
3. Tombol "Jalankan Analisis" **disabled** saat submit < `min_responden`, dengan alasan tertulis.
4. `/dcs/hasil` diakses saat status `OPEN` → redirect ke `/dcs`.
5. E2E WCP: versi ringkas dari (1).
6. Hapus/perbarui E2E lama yang membuat sesi DCS/WCP — cek `e2e/` untuk spec yang menyentuh
   `/dcs/buat`. **Catatan**: memory proyek mencatat `kuesioner.spec.ts` punya isu pre-existing
   (`buatSekolah` gagal select jenjang, race condition dropdown). Kalau spec itu masih merah, itu
   **bukan** regresi dari item ini — jangan dikejar di sini.

## Definition of done

- [ ] `make test` hijau (kecuali kegagalan pre-existing yang sudah tercatat)
- [ ] `docs-usage` + `CHANGELOG.md` + `CLAUDE.md` diperbarui
- [ ] Submodule di repo induk di-bump

## Risiko & catatan

- Item ini **tidak boleh** dimulai sebelum 001 merge — `schema.ts` yang di-regen dari openapi lama akan
  menyesatkan seluruh pekerjaan.
- Multi-select partisipan: cek dulu apakah repo sudah punya komponen multi-select di
  `src/components/` sebelum menulis yang baru.
- Bila endpoint bulk (`partisipan_ids`) ternyata belum ada di openapi hasil 001, **jangan** akali dengan
  loop `POST` di klien — kembalikan dulu ke item 001.
