# Backlog 012 — Title halaman terduplikasi "— ANJAB-ABK — ANJAB-ABK"

> **Repo:** `anjab-abk-web-app`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Temuan simulasi end-to-end Task Inventory di deployment YPII (`anjab-abk.cantum-ypii.com`,
2026-07-13, panel Kepala Sekolah): document title di hampir semua halaman dalam grup `(auth)`
menampilkan pola `"<Judul> — ANJAB-ABK — ANJAB-ABK"` — kata "ANJAB-ABK" dobel di akhir. Terlihat
di tab browser, riwayat browser, dan bookmark. Halaman Dashboard (yang tidak mengekspor `metadata`
sendiri) tidak terkena — hanya menampilkan "ANJAB-ABK" tunggal, sesuai `default` dari root layout.

## Keputusan yang sudah dikunci

- Root layout (`src/app/layout.tsx`) **tetap** memegang satu-satunya `title.template: "%s — ANJAB-ABK"`
  — ini benar dan tidak diubah. Grup `(auth)` (`src/app/(auth)/layout.tsx`) memang **tidak**
  mendefinisikan `metadata` sendiri, jadi bukan kasus dua level template bertumpuk.
- Akar masalah: 30 halaman di bawah `(auth)` menulis string `title` **manual** yang sudah
  menyertakan `"— ANJAB-ABK"` di akhir, sehingga template root menambahkannya sekali lagi.
  Halaman `master-data/*` **tidak** kena bug ini — title-nya sudah benar berakhiran
  `"— Master Data"` (bukan "— ANJAB-ABK"), jadi jangan disentuh.
- Perbaikan = hapus akhiran `" — ANJAB-ABK"` dari 30 string title berikut, biarkan template root
  yang menambahkannya. **Jangan** ganti pola jadi object `{ template, default }` per halaman —
  cukup string biasa tanpa suffix, konsisten dengan pola `master-data/*` yang sudah benar.

## Kondisi sekarang (verified)

30 file dengan title manual berakhiran `"— ANJAB-ABK"` (hasil `grep -rn "title:.*ANJAB-ABK" src/app`,
dikurangi `layout.tsx`):

| File | Baris | Title sekarang |
|---|---|---|
| `src/app/(auth)/time-study/isi/[penugasan_id]/[log_id]/edit/page.tsx` | 11 | `"Edit Log Harian — Time Study — ANJAB-ABK"` |
| `src/app/(auth)/time-study/[penugasan_id]/page.tsx` | 15 | `"Detail Penugasan Time Study — ANJAB-ABK"` |
| `src/app/(auth)/time-study/tugaskan-banyak/page.tsx` | 12 | `"Tugaskan Banyak Sekaligus — Time Study — ANJAB-ABK"` |
| `src/app/(auth)/time-study/page.tsx` | 12 | `"Time Study — ANJAB-ABK"` |
| `src/app/(auth)/wcp/page.tsx` | 17 | `"WCP — ANJAB-ABK"` |
| `src/app/(auth)/time-study/isi/[penugasan_id]/page.tsx` | 11 | `"Time Study — Log Harian — ANJAB-ABK"` |
| `src/app/(auth)/partisipan/page.tsx` | 8 | `"Partisipan — ANJAB-ABK"` |
| `src/app/(auth)/partisipan/tambah/page.tsx` | 8 | `"Tambah Partisipan — ANJAB-ABK"` |
| `src/app/(auth)/wcp/hasil-responden/[responden_id]/page.tsx` | 12 | `"Hasil WCP Responden — ANJAB-ABK"` |
| `src/app/(auth)/dcs/page.tsx` | 17 | `"DCS — ANJAB-ABK"` |
| `src/app/(auth)/dcs/hasil/page.tsx` | 8 | `"Hasil DCS — ANJAB-ABK"` |
| `src/app/(auth)/dcs/isi/[responden_id]/page.tsx` | 9 | `"Isi Kuesioner DCS — ANJAB-ABK"` |
| `src/app/(auth)/dcs/hasil-responden/[responden_id]/page.tsx` | 12 | `"Hasil DCS Responden — ANJAB-ABK"` |
| `src/app/(auth)/kuesioner/page.tsx` | 15 | `"Kuesioner Saya — ANJAB-ABK"` |
| `src/app/(auth)/opm/page.tsx` | 8 | `"Analisis Jabatan — OPM — ANJAB-ABK"` |
| `src/app/(auth)/opm/buat/page.tsx` | 9 | `"Mulai Analisis Jabatan — OPM — ANJAB-ABK"` |
| `src/app/(auth)/time-study/buat/page.tsx` | 11 | `"Tugaskan Partisipan — Time Study — ANJAB-ABK"` |
| `src/app/(auth)/opm/[sesi_id]/page.tsx` | 18 | `"Detail Sesi OPM — ANJAB-ABK"` |
| `src/app/(auth)/opm/[sesi_id]/hasil/page.tsx` | 8 | `"Hasil OPM — ANJAB-ABK"` |
| `src/app/(auth)/opm/isi/[responden_id]/page.tsx` | 9 | `"Isi Kuesioner OPM — ANJAB-ABK"` |
| `src/app/(auth)/task-inventory/tahap1/[responden_id]/page.tsx` | 9 | `"Tahap 1 — Seleksi Relevansi — ANJAB-ABK"` |
| `src/app/(auth)/time-study/isi/[penugasan_id]/tambah/page.tsx` | 6 | `"Tambah Log Harian — Time Study — ANJAB-ABK"` |
| `src/app/(auth)/task-inventory/buat/page.tsx` | 9 | `"Mulai Analisis Jabatan — Task Inventory — ANJAB-ABK"` |
| `src/app/(auth)/task-inventory/tahap2/[sesi_id]/page.tsx` | 14 | `"Tahap 2 — Review Koordinator — ANJAB-ABK"` |
| `src/app/(auth)/task-inventory/page.tsx` | 9 | `"Analisis Jabatan — Task Inventory — ANJAB-ABK"` |
| `src/app/(auth)/partisipan/[id]/page.tsx` | 9 | `"Detail Partisipan — ANJAB-ABK"` |
| `src/app/(auth)/wcp/hasil/page.tsx` | 8 | `"Hasil WCP — ANJAB-ABK"` |
| `src/app/(auth)/task-inventory/tahap3/[responden_id]/page.tsx` | 14 | `"Tahap 3 — Detailing — ANJAB-ABK"` |
| `src/app/(auth)/wcp/isi/[responden_id]/page.tsx` | 9 | `"Isi Kuesioner WCP — ANJAB-ABK"` |
| `src/app/(auth)/task-inventory/[sesi_id]/page.tsx` | 22 | `"Detail Analisis Jabatan — Task Inventory — ANJAB-ABK"` |

Verifikasi pembanding (BENAR, tidak disentuh): `src/app/(auth)/master-data/**/page.tsx` (mis.
`master-data/sekolah/page.tsx:8` → `"Sekolah — Master Data"`) — tidak menyertakan "ANJAB-ABK",
jadi title akhirnya benar `"Sekolah — Master Data — ANJAB-ABK"` (tunggal).

Root layout — **jangan diubah**, sebagai acuan pola yang benar:

```tsx
// src/app/layout.tsx:6-9
export const metadata: Metadata = {
  title: {
    default: "ANJAB-ABK",
    template: "%s — ANJAB-ABK",
  },
```

## Langkah eksekusi

### Langkah 1 — Hapus akhiran " — ANJAB-ABK" dari 30 file di atas

Untuk tiap file pada tabel "Kondisi sekarang", ubah string `title` dengan menghapus akhiran
`" — ANJAB-ABK"` (mempertahankan sisa string apa adanya). Contoh:

```diff
- export const metadata = { title: "Detail Analisis Jabatan — Task Inventory — ANJAB-ABK" };
+ export const metadata = { title: "Detail Analisis Jabatan — Task Inventory" };
```

Baca ulang tiap file sebelum mengedit — baris bisa bergeser sejak tabel ini ditulis. Lakukan
pencarian ulang dengan `grep -rn "title:.*ANJAB-ABK" src/app --include="*.tsx" | grep -v layout.tsx`
untuk memastikan seluruh kandidat tercakup (jumlah 30 di atas adalah snapshot saat backlog ini
ditulis — kalau ada halaman baru ditambahkan sejak itu, ikutkan juga bila polanya sama).

### Langkah 2 — Verifikasi tidak ada regresi di halaman lain

Grep ulang setelah edit: `grep -rn "ANJAB-ABK — ANJAB-ABK" src/app` harus kosong. Grep
`grep -rln "title:.*ANJAB-ABK" src/app --include="*.tsx" | grep -v layout.tsx` juga harus kosong
(tidak ada lagi title manual yang menyebut ANJAB-ABK).

### Langkah 3 — Cek test yang menegaskan title lama

Cari test (Vitest) yang meng-assert title string lama (mis. `toHaveTitle` atau cek `metadata.title`)
dan sesuaikan ekspektasinya ke title baru tanpa akhiran.

## Kriteria penerimaan

- [ ] Tab browser di setiap halaman `(auth)` menampilkan title tunggal, mis.
      `"Detail Analisis Jabatan — Task Inventory — ANJAB-ABK"` (bukan dobel).
- [ ] Halaman `master-data/*` tidak berubah (title tetap berakhiran "— Master Data").
- [ ] Halaman Dashboard tidak berubah (masih "ANJAB-ABK" tunggal, tanpa metadata sendiri).
- [ ] Tidak ada lagi occurrence string `"ANJAB-ABK — ANJAB-ABK"` di seluruh `src/app`.

## Skenario uji

- Tidak perlu test baru khusus — ini perbaikan string statis. Bila ada test unit yang sudah
  meng-assert title halaman (cek `grep -rn "toHaveTitle\|metadata.title" src/test` atau folder test
  terkait), update ekspektasinya.
- Jalankan `make test` (lint + unit) untuk memastikan tidak ada breakage TypeScript/test lain.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-web-app`
- [ ] `npm run build` sukses
- [ ] `CHANGELOG.md` diperbarui
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- Perubahan murni string metadata, tidak menyentuh logika/komponen — risiko sangat rendah, tidak
  ada kemungkinan efek samping ke API atau state aplikasi.
- Ditemukan lewat simulasi Playwright manual (bukan e2e otomatis), 2026-07-13. Jumlah 30 file adalah
  hasil grep saat backlog ditulis — agen pelaksana WAJIB grep ulang sebelum eksekusi untuk
  menangkap halaman baru yang mungkin ditambahkan sejak itu.
