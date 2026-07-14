# Backlog 035 — Web app: 403/500 dari backend tampil sebagai crash "Server Components render", bukan pesan

> **Repo:** `anjab-abk-web-app`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Setelah backlog 026/031 menghapus penelanan-senyap (`?? []`), error API kini **dilempar** — itu
benar. Tapi di beberapa halaman lemparan itu **tidak tertangkap oleh error boundary yang ramah**,
sehingga pengguna melihat pesan mentah Next.js:

> **Terjadi kesalahan** — *An error occurred in the Server Components render. The specific message
> is omitted in production builds to avoid leaking sensitive details. A digest property is
> included…*

Itu bocoran internal framework, bukan pesan untuk pengguna. Dua kasus **berbeda sebabnya** tapi
bergejala sama, dan keduanya diamati langsung di produksi 2026-07-14 (Playwright).

## Kondisi sekarang (verified)

| # | Kasus | Fakta | Verifikasi |
|---|---|---|---|
| 1 | **403 — otorisasi bekerja benar, pesannya yang salah** | Partisipan **bukan anggota panel** (Theresia, anggota panel Pembina OSIS) membuka `/task-inventory/tahap2/tises_c456dffb` (sesi Koordinator Pramuka) → backend menolak (403, data TIDAK bocor ✓) tapi halaman **crash** dengan pesan Server Components di atas — bukan "Anda tidak berwenang" | ✓ diamati langsung |
| 2 | **500 — bug backend, halaman ikut mati total** | Sesi TI yang memicu 500 di `task-terpilih` (lihat **backlog 024**) → seluruh halaman detail sesi crash ("Gagal memuat detail analisis"), termasuk **tombol "Hapus paksa"** — admin **tidak punya jalan keluar lewat UI**; sesi hanya bisa dihapus lewat API | ✓ diamati langsung; penghapusan terpaksa via `DELETE` ber-token |
| 3 | Pola `TidakBerhak` **sudah ada** di repo (dibuat di backlog 026, dirender **di server** karena Next.js menyensor `error.message` di `error.tsx`) | ✓ lihat backlog 026 |

### Kenapa kasus 1 bukan sekadar kosmetik

Halaman Tahap 2 **memang punya** mode hanya-baca untuk anggota panel (terverifikasi bekerja:
anggota non-koordinator melihat tabel + banner *"Anda melihat hasil Tahap 2 sebagai anggota panel
(hanya-baca)"* tanpa tombol aksi ✓). Yang hilang hanyalah cabang **non-anggota** → 403 → panel
`TidakBerhak`. Jadi ini melengkapi fitur yang sudah dirancang, bukan menambah fitur baru.

### Kenapa kasus 2 lebih dari sekadar UX

Halaman detail sesi adalah **satu-satunya** tempat tombol "Hapus paksa analisis" berada. Ketika
halaman itu mati karena satu endpoint (`task-terpilih`) 500, admin kehilangan kemampuan menghapus
sesi rusak tersebut sama sekali. Halaman harus **tetap terender** meski satu bagian gagal.

## Langkah eksekusi

### Langkah 1 — 403 → panel `TidakBerhak` (kasus 1)

Di `src/app/(auth)/task-inventory/tahap2/[sesi_id]/page.tsx`: tangkap `ApiError` ber-`status === 403`
dan render panel `TidakBerhak` (pola dari 026), bukan melempar. Status lain tetap dilempar.

Sisir halaman lain yang bisa dibuka oleh partisipan bukan-peserta dengan pola yang sama
(kandidat: `task-inventory/tahap1/[responden_id]`, `tahap3/[responden_id]`, `opm/isi/[responden_id]`)
— **verifikasi dulu**, jangan pukul rata.

### Langkah 2 — degradasi parsial di halaman detail sesi (kasus 2)

`src/app/(auth)/task-inventory/[sesi_id]/page.tsx`: kegagalan `task-terpilih` / `hasil` **tidak
boleh** mematikan seluruh halaman. Pakai `GagalMuatSebagian` (helper yang sudah ada dari backlog
031) untuk **bagian** hasil/task-terpilih, sementara header + panel aksi admin (termasuk "Hapus
paksa") **tetap terender**.

Prinsipnya: data yang menentukan **aksi pemulihan** admin tidak boleh bergantung pada data yang
sedang rusak.

## Kriteria penerimaan

- [ ] Non-anggota panel membuka Tahap 2 → panel "Tidak berwenang" (+`X-Request-ID`), bukan crash.
- [ ] Anggota panel tetap melihat mode hanya-baca (regresi — sudah bekerja hari ini, jangan rusak).
- [ ] Koordinator tetap bisa memutuskan & menyimpan (regresi).
- [ ] Detail sesi dengan `task-terpilih` 500 → header + tombol "Hapus paksa" **tetap terender**,
      bagian hasil menampilkan penanda gagal.
- [ ] `make test` hijau, `npm run build` sukses.

## Risiko & catatan

Setelah **backlog 024** diperbaiki, kasus 2 tidak akan mudah dipicu lagi — tapi perbaikan ini tetap
perlu: ia yang memastikan bug backend **berikutnya** tidak mengunci admin dari UI-nya sendiri.
Jangan tutup item ini hanya karena 024 sudah beres.
