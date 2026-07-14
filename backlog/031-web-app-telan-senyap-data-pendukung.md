# Backlog 031 — Web app: ~30 `?? []` / `?? null` tersisa di jalur baca **data pendukung** (dropdown & label)

> **Repo:** `anjab-abk-web-app`
> **Status:** Siap dieksekusi
> **Blocked by:** — (tapi lihat "Risiko & catatan": nilainya naik tajam begitu backend 025 di-deploy)
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Backlog **026** memberantas pola telan-senyap `?? []` di jalur baca Server Component, tapi cakupannya
**sengaja dibatasi** pada data *domain inti*: Task Inventory Tahap 1/2/3 dan jalur kuesioner. Backlog
**029** menutup satu-satunya kasus di Client Component.

Yang **belum** tersentuh: **~30 kemunculan `?? []` / `?? null` pada fetch data *pendukung*** —
daftar jabatan, sekolah, partisipan, dan sejenisnya yang dipakai untuk mengisi **dropdown** dan
**melabeli** ID. Bila fetch-nya gagal, halaman tetap dirender: dropdown-nya kosong (admin mengira
"belum ada jabatan"), atau label jatuh kembali ke ID mentah (`jbt_xxxxx`) — **tanpa pesan error apa
pun**. Kelas bug yang sama dengan 026/029, hanya dampaknya lebih halus.

Ini **bukan** temuan teoretis: backend **025** kini menuntut token di seluruh endpoint baca. Setiap
jalur yang tokennya kurang/kedaluwarsa akan mulai mengembalikan 401 — dan seluruh ~30 titik ini akan
menelannya diam-diam.

## Kondisi sekarang (verified)

| # | Fakta | Verifikasi |
|---|---|---|
| 1 | ~30 `?? []` / `?? null` tersisa di jalur baca data pendukung, mis. `time-study/page.tsx`, `partisipan/page.tsx`, `dcs/page.tsx`, `wcp/page.tsx`, `opm/[sesi_id]/page.tsx`, dan sebagian besar halaman `master-data/*` | ✓ audit agen pelaksana 029, 2026-07-14 |
| 2 | Semuanya fetch data pendukung (isi dropdown / label ID), **bukan** data yang sudah tersimpan milik pengguna — jadi tidak menyembunyikan data yang sudah ada seperti bug 029 | ✓ idem |
| 3 | Backlog 026 **secara eksplisit** hanya menyasar Tahap 1/2/3 + jalur kuesioner — sisa ini di luar cakupannya, bukan kelalaian | ✓ lihat Langkah 5 di `backlog/026-*.md` |
| 4 | Backend 025 kini menuntut token di **seluruh** endpoint baca (32 GET + 9 `POST .../search`) → 401 jadi mungkin di semua jalur ini | ✓ backlog 025, `make test` hijau 621 test |
| 5 | Invariant yang melarang pola ini **sudah dikunci** di `CLAUDE.md` web-app (dari 026 & 029) — kode ini melanggarnya, tinggal ditegakkan | ✓ |

## Keputusan yang sudah dikunci

- **Jangan pukul rata jadi "semua harus melempar".** Bedakan per kasus, seperti yang sudah dilakukan
  026: ada kekosongan yang **sah** (daftar memang belum berisi) dan ada yang **kegagalan**. Untuk
  data pendukung, kegagalan fetch dropdown **tidak selalu** layak menggagalkan seluruh halaman —
  tapi ia **tidak boleh senyap**.
- Pola yang diikuti: **404 sah → `[]`/`null`; 401/403/5xx → melempar atau tampil sebagai error yang
  terlihat.** Ini persis pengecualian yang sudah dikunci 026 untuk `/partisipan/saya` dan
  `.../seleksi` kunjungan pertama — jangan diregresikan.
- Halaman yang **data intinya berhasil dimuat** tapi **data pendukungnya gagal** sebaiknya tetap
  dirender, dengan **penanda gagal yang terlihat** pada bagian yang terdampak (mis. dropdown
  dinonaktifkan + pesan "Gagal memuat daftar jabatan"), bukan dropdown kosong yang tak terbedakan
  dari "memang belum ada data".

## Langkah eksekusi

### Langkah 1 — Inventarisasi ulang & klasifikasi

`grep -rnE "\.data \?\? \[\]|\.data\?\.items \?\? \[\]|\.data \?\? null" src/app` — daftarkan
**setiap** kemunculan, lalu klasifikasikan tiap satu: (a) kekosongan sah, (b) kegagalan yang ditelan,
(c) campuran (404 sah + 4xx/5xx kegagalan). Tulis hasil klasifikasinya di laporan — jangan langsung
mengubah.

Catatan: pola `.data?.items ?? []` **tidak tertangkap** grep 026 (`\.data ?? \[\]`) — itulah kenapa
sebagian lolos. Pastikan grep Langkah 1 mencakup varian ini.

### Langkah 2 — Terapkan per klasifikasi

Untuk (b) dan (c): pakai `apiErrorDari(res)` + `GagalMuat` (Server Component) atau `notifyGagal`
(Client Component) — helper-nya sudah ada dari 026 & 029, jangan bikin baru.

### Langkah 3 — Tegakkan lewat jaring pengaman

Setelah bersih, tambahkan pengecekan (test atau skrip lint) yang membuat pola ini **tidak bisa
kembali** — sejajar dengan penghapusan ekspor klien `api` telanjang di 029 (yang membuat pola
telanjang mustahil diperkenalkan lagi). Pertimbangkan aturan ESLint kustom atau test grep.

## Kriteria penerimaan

- [ ] Setiap `?? []` / `?? null` di jalur baca sudah diklasifikasikan **dan** ditangani sesuai kelasnya
- [ ] Fetch dropdown/label yang gagal → **penanda gagal terlihat**, bukan dropdown kosong senyap
- [ ] Kekosongan yang sah tetap tampil sebagai state kosong yang tenang (tanpa error palsu)
- [ ] Pengecualian 404 yang sudah dikunci 026 (`/partisipan/saya`, `.../seleksi`) **tidak diregresikan**
- [ ] Ada jaring pengaman yang mencegah pola ini kembali

## Skenario uji

- Test: fetch daftar jabatan → 401 → assert penanda gagal terender **dan** dropdown tidak tampil
  sebagai "kosong biasa".
- Test: fetch daftar jabatan → 200 dengan 0 item → assert state kosong yang sah, tanpa error.
- Test regresi: `/partisipan/saya` → 404 → tetap `null`, tidak melempar (jangan regresikan 026).
- `make test` hijau + `npm run build` sukses.

## Definition of done

- [ ] `make test` hijau, `npm run build` sukses
- [ ] `CHANGELOG.md` diperbarui
- [ ] `CLAUDE.md` web-app: pertajam invariant 026 agar eksplisit mencakup **data pendukung** dan
      varian `.data?.items ?? []`
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- Item ini lahir sebagai **temuan sampingan agen pelaksana 029** (2026-07-14), bukan dari laporan
  pengguna.
- **Nilainya naik tajam setelah backend 025 di-deploy**: sebelum 025, endpoint baca tidak menuntut
  token, sehingga 401 praktis tidak pernah terjadi dan pola ini jarang tergigit. Setelah 025, setiap
  jalur bertoken kurang/kedaluwarsa akan menelan 401 secara senyap. **Pertimbangkan mengerjakan ini
  sebelum atau bersamaan dengan deploy 025.**
- Dampaknya lebih halus dari 029 (yang menyembunyikan anggota panel yang sudah ada). Di sini yang
  hilang adalah *pilihan* di dropdown dan *keterbacaan* label — tapi konsekuensinya bisa serius:
  admin yang melihat dropdown jabatan kosong bisa menyimpulkan "master data belum diisi" dan
  membuat duplikat.
