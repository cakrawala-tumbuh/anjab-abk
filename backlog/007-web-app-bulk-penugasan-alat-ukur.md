# Backlog 007 — Web app: UI penugasan massal (bulk) untuk TS, TI, OPM

> **Repo:** `anjab-abk-web-app`
> **Status:** Menunggu (blocked by 005)
> **Blocked by:** [005](005-backend-bulk-penugasan-alat-ukur.md)
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`, `dokumentasi-penggunaan-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Item [005](005-backend-bulk-penugasan-alat-ukur.md) (backend) dan [006](006-mcp-bulk-penugasan-alat-ukur.md)
(MCP) menambahkan endpoint bulk-assign idempoten untuk TS/TI/OPM. Tanpa perubahan di web-app,
admin yang bekerja lewat UI (bukan MCP/API langsung) **tidak mendapat manfaat apa pun** dari
endpoint baru itu — halaman admin TI (`tambah-responden.tsx`) dan OPM
(`opm/[sesi_id]/tambah-responden.tsx`) masih formulir satu-dropdown-satu-submit, dan Time Study
tidak punya UI bulk sama sekali (hanya `/time-study/buat` untuk satu partisipan per kunjungan
halaman).

Ini persis situasi yang pernah dialami WCP/DCS sebelum backlog item 003: backend bulk saja tidak
cukup, dibutuhkan komponen frontend baru (checkbox multi-select) supaya admin benar-benar bisa
menugaskan banyak partisipan dalam satu submit. Item 003 secara eksplisit mengunci "Halaman TI &
OPM tidak disentuh" — jadi gap ini memang belum pernah digarap untuk TI/OPM/TS.

Tujuan item ini: tambahkan UI bulk-assign (pola sama seperti `wcp/assign-responden.tsx` /
`dcs/assign-responden.tsx`) untuk TI, OPM, dan TS — **berdampingan** dengan form single yang
sudah ada (tidak menghapus/mengganti, mengikuti prinsip yang sama dengan item 005/006: manual
mekanisme tidak boleh hilang).

## Keputusan yang sudah dikunci

1. **Form single yang sudah ada TETAP ADA, tidak diganti** (beda dari migrasi WCP/DCS yang
   sepenuhnya mengganti `tambah-responden.tsx` dengan `assign-responden.tsx` karena endpoint
   single WCP/DCS memang dihapus di backend). Untuk TI/OPM/TS, endpoint single backend tetap ada
   (lihat item 005) — jadi form bulk baru ditambahkan **sebagai form kedua**, ditampilkan
   berdampingan dengan form single di halaman yang sama (TI, OPM), atau sebagai halaman baru
   terpisah dengan link dari halaman listing (TS, karena TS memang tidak punya konsep
   per-sesi/per-halaman "tambah responden" — assign selalu terjadi di halaman `/time-study/buat`
   atau halaman baru yang setara).
2. **Response envelope backend bulk BUKAN array datar** seperti WCP/DCS
   (`response_model=list[XxxRead]`), melainkan `{created: XxxRead[], skipped: [{partisipan_id,
   alasan}]}` (lihat item 005 Keputusan #2). UI **wajib** menampilkan ringkasan setelah submit:
   jumlah berhasil (`created.length`) DAN daftar yang dilewati (`skipped`) dengan alasan
   berbahasa manusia — bukan diam-diam mengabaikan `skipped` seperti pola WCP/DCS (yang atomik,
   tidak punya konsep skip).
3. **Mapping kode alasan → label Bahasa Indonesia, dipakai identik di ketiga form baru** (TS, TI,
   OPM) — jangan buat variasi teks per form:
   ```
   sudah_terdaftar          → "Sudah terdaftar"
   duplikat_input           → "Duplikat dalam input"
   bukan_anggota_sme_panel  → "Bukan anggota SME panel"
   kapasitas_penuh          → "Kapasitas sesi penuh"
   ```
4. **Daftar partisipan yang ditampilkan di checkbox list bulk TI/OPM mengikuti filter yang SAMA
   dengan form single yang sudah ada** (anggota SME panel jabatan sesi ini yang belum jadi
   responden) — jangan tampilkan partisipan di luar filter itu, karena backend akan skip mereka
   dengan `bukan_anggota_sme_panel` (percuma ditampilkan sebagai opsi). TS tidak punya filter
   panel — tampilkan semua partisipan yang belum punya `TsPenugasanRead` aktif.
5. **Jalankan `npm run gen:api` di awal eksekusi** (butuh `anjab-abk-backend` sudah menjalankan
   endpoint baru dari item 005 — baik lokal maupun lewat `openapi/openapi.json` yang sudah
   diperbarui) untuk memunculkan tipe `BulkAssignResult`/`BulkSkipped` generated di
   `src/lib/api/schema.ts`. **Nama tipe generated untuk generic Pydantic (`BulkAssignResult[T]`)
   belum diketahui pasti sebelum generate** — kemungkinan pola `BulkAssignResult_TsPenugasanRead_`
   atau serupa (openapi-typescript biasa menyuffix nama generic dengan parameter tipenya). Jangan
   menebak nama tipe di kode — **cek langsung isi `schema.ts` setelah `gen:api`** untuk nama
   pastinya, baru referensikan di komponen baru.

## Kondisi sekarang (verified)

**Form single yang sudah ada — TIDAK diubah, hanya jadi referensi pola & tetap dirender:**

| Alat ukur | File form single | Endpoint yang dipanggil | Filter partisipan sumber dropdown |
|---|---|---|---|
| TI | `src/app/(auth)/task-inventory/[sesi_id]/tambah-responden.tsx` (86-97: `<select>` tunggal + field nama + submit) | `POST /api/v1/task-inventory/sesi/{sesi_id}/responden`, body `{partisipan_id, nama}` | dihitung di `task-inventory/[sesi_id]/page.tsx:98-101` — anggota SME panel jabatan sesi (`smePanel.partisipan_ids`), TIDAK difilter "belum jadi responden" (TI mengizinkan pilih siapa saja anggota panel meski mungkin race) |
| OPM | `src/app/(auth)/opm/[sesi_id]/tambah-responden.tsx` (87-99: `<select>` tunggal + submit) | `POST /api/v1/opm/sesi/{sesi_id}/responden`, body `{partisipan_id, jabatan_label, nama}` | dihitung di `opm/[sesi_id]/page.tsx:97-99` (`partisipanTersedia`) — anggota SME panel jabatan sesi DIKURANGI yang sudah jadi responden (`respondenPartisipanIds`) |
| TS | `src/app/(auth)/time-study/buat/ts-penugasan-form.tsx` (satu halaman penuh, bukan komponen inline) | `POST /api/v1/time-study/penugasan`, body `{partisipan_id, aktif: true, catatan}` | seluruh partisipan (`time-study/page.tsx:16-27`), tanpa filter SME panel (TS tidak berbasis jabatan) — filter "belum punya penugasan aktif" TIDAK ada di form ini sekarang (backend yang menolak duplikat via 409) |

**Referensi pola bulk yang SUDAH ADA dan terbukti bekerja (WCP, tiru persis untuk komponen
baru)** — `src/app/(auth)/wcp/assign-responden.tsx` (identik `dcs/assign-responden.tsx`):
- State: `useState<Set<string>>(new Set())` untuk id terpilih (baris 22).
- `toggle(id)` / `selectAll()` / `clearAll()` (baris 28-43).
- Checkbox list dengan `max-h-72 overflow-y-auto` (baris 103-121), satu `<label>` per partisipan
  berisi `<input type="checkbox">` + nama + jabatan.
- Tombol submit tunggal `Tugaskan Terpilih (${selected.size})`, disabled saat `submitting ||
  selected.size === 0` (baris 123-131).
- `onSubmit` (baris 45-63): `client.POST(..., { body: { partisipan_ids: Array.from(selected) }
  })`, lalu `router.refresh()` — **item ini WAJIB memperluas pola `onSubmit` untuk membaca
  `data.created`/`data.skipped` dari response dan menampilkannya**, bukan sekadar
  `router.refresh()` seperti WCP/DCS (WCP/DCS tidak butuh ini karena atomik, tidak punya
  `skipped`).

**Halaman induk yang akan merender form baru (props yang sudah tersedia untuk diteruskan):**
- `task-inventory/[sesi_id]/page.tsx:69-101` — variabel `partisipan` (sudah terfilter anggota
  panel) & `smePanel` sudah dihitung di `fetchPageData`, tinggal diteruskan sebagai prop baru.
- `opm/[sesi_id]/page.tsx:46-74, 97-99` — variabel `partisipanTersedia` sudah dihitung persis
  seperti yang dibutuhkan form bulk.
- `time-study/page.tsx:14-28` — `fetchPageData` mengembalikan `penugasan` & `partisipan`; item
  ini perlu menambah filter partisipan yang BELUM punya `TsPenugasanRead` (partisipan tidak ada
  di `penugasan.map(p => p.partisipan_id)`) di halaman/komponen baru.

**Risiko regresi E2E yang perlu DIVERIFIKASI (bukan dipastikan pecah, beda dari fixture backend
di item 005):** `e2e/opm.spec.ts` — `pastikanSMEPanel` (baris 273) dipanggil SEBELUM
`bukaAtauBuatTiSesi` (baris 277), pola urutan yang sama dengan yang menyebabkan fixture backend
pecah. TAPI berbeda dari fixture backend (`_opm_common.py`, yang pakai 2 partisipan anonim +
2 partisipan panel terpisah): di sini hanya ADA SATU partisipan (`PARTISIPAN_NAMA`), dan
`daftarkanRespondenPartisipan` (baris 117-133) sudah punya guard idempoten (baris 121: `if
(await respRow.isVisible(...)) return;`) — bila auto-populate TI (item 005) sudah membuat
responden untuk partisipan itu duluan, fungsi ini akan mendeteksi row sudah ada dan tidak
mengklik "+ Daftarkan" lagi, sehingga total responden tetap 1 seperti sebelumnya. **Kemungkinan
besar TIDAK pecah**, tapi WAJIB dijalankan ulang (`make e2e`, spec OPM) setelah item 005 live
untuk memastikan — bila ternyata pecah, perbaikannya: pindahkan `pastikanSMEPanel` ke SETELAH
`bekukanTiSampaiTahap3` (sebelum `bukaAtauBuatOpmSesi` dipanggil di test berikutnya), sama
seperti perbaikan `_opm_common.py` di item 005.

Semua nomor baris di atas WAJIB dicek ulang oleh agen pelaksana sebelum mengedit (baris bisa
bergeser sejak rencana ini ditulis).

## Langkah eksekusi

### Langkah 0 — Regenerate tipe API

`npm run gen:api` (butuh `openapi/openapi.json` sudah mencerminkan endpoint baru dari item 005 —
salin ulang dari backend atau fetch dari instance backend yang sudah menjalankan kode item 005).
Cek `src/lib/api/schema.ts` untuk nama tipe `BulkAssignResult`/`BulkSkipped` generated yang
sebenarnya — pakai nama itu di langkah-langkah berikut (JANGAN menebak).

### Langkah 1 — Util mapping alasan skip (dipakai bersama ketiga form baru)

Tambah helper kecil, mis. `src/lib/format/bulk-skip-alasan.ts`:

```ts
const ALASAN_LABEL: Record<string, string> = {
  sudah_terdaftar: "Sudah terdaftar",
  duplikat_input: "Duplikat dalam input",
  bukan_anggota_sme_panel: "Bukan anggota SME panel",
  kapasitas_penuh: "Kapasitas sesi penuh",
};

export function formatAlasanSkip(alasan: string): string {
  return ALASAN_LABEL[alasan] ?? alasan;
}
```

### Langkah 2 — TI: `assign-responden-banyak.tsx`

File baru: `src/app/(auth)/task-inventory/[sesi_id]/assign-responden-banyak.tsx`. Salin struktur
`wcp/assign-responden.tsx` (checkbox multi-select + `Set<string>` + select-all/clear-all), ganti:
- Props: `sesiId: string`, `partisipan: PartisipanRead[]` (partisipan yang diteruskan HARUS
  sudah terfilter sama seperti prop `partisipan` yang sudah dipakai `tambah-responden.tsx` saat
  ini — tidak perlu filter tambahan).
- `onSubmit`: `client.POST("/api/v1/task-inventory/sesi/{sesi_id}/responden/bulk", { params: {
  path: { sesi_id: sesiId } }, body: { partisipan_ids: Array.from(selected) } })`.
- Setelah sukses: simpan `data.created`/`data.skipped` ke state lokal, render ringkasan di atas
  checkbox list — "N responden berhasil ditambahkan." + (bila `skipped.length > 0`) daftar
  `partisipan_id` (map ke nama lewat `partisipan` prop) + `formatAlasanSkip(s.alasan)` per baris
  yang dilewati — lalu `router.refresh()` supaya halaman induk (daftar responden) ikut update.
  Kosongkan `selected` setelah submit (seperti WCP).

`task-inventory/[sesi_id]/page.tsx`: render `<AssignRespondenBanyak sesiId={sesi.id}
partisipan={partisipan} />` **setelah** `<TambahResponden ... />` yang sudah ada (baris ~220-224),
dengan heading pemisah kecil, mis. `<h3 className="mt-6 text-sm font-medium text-gray-500">Atau
tugaskan banyak sekaligus</h3>` sebelum komponen baru. Guard render sama seperti form single
(hanya saat `sesi.status` `DRAFT`/`TAHAP1`).

### Langkah 3 — OPM: `assign-responden-banyak.tsx`

Sama seperti Langkah 2, file baru `src/app/(auth)/opm/[sesi_id]/assign-responden-banyak.tsx`:
- Props: `sesiId: string`, `partisipan: PartisipanRead[]` (teruskan `partisipanTersedia` yang
  sudah dihitung di `page.tsx`).
- `onSubmit`: `POST /api/v1/opm/sesi/{sesi_id}/responden/bulk`, body `{partisipan_ids}` — TIDAK
  perlu `jabatan_label`/`nama` (backend meresolusi otomatis, beda dari form single OPM yang
  mewajibkan `jabatan_label`).
- Render di `opm/[sesi_id]/page.tsx` setelah `<TambahResponden ... />` yang sudah ada, guard
  status sama (`DRAFT`/`OPEN`).

### Langkah 4 — TS: halaman bulk baru

TS tidak punya komponen `tambah-responden.tsx` yang bisa ditambahi form kedua (assign terjadi
inline di `/time-study/buat`) — buat **halaman baru** `src/app/(auth)/time-study/tugaskan-banyak/page.tsx`
+ komponen `ts-penugasan-bulk-form.tsx` di folder yang sama:
- `page.tsx`: `fetchPageData` mirip `time-study/page.tsx` (fetch `penugasan`, `partisipan`,
  `jabatan`), filter partisipan yang belum punya penugasan: `const assignedIds = new
  Set(penugasan.map(p => p.partisipan_id)); const tersedia = partisipan.filter(p =>
  !assignedIds.has(p.id))`.
- `ts-penugasan-bulk-form.tsx`: checkbox multi-select (pola sama seperti `wcp/assign-responden.tsx`,
  termasuk tampilan jabatan per baris seperti yang sudah dilakukan `wcp/assign-responden.tsx`
  baris 116-118), field tambahan `catatan` (textarea, opsional, diterapkan ke SELURUH batch —
  samakan dengan skema backend `TsPenugasanBulkCreate`), `onSubmit` memanggil
  `POST /api/v1/time-study/penugasan/bulk`, body `{partisipan_ids, aktif: true, catatan}`.
  Tampilkan ringkasan `created`/`skipped` sama seperti Langkah 2-3, lalu `router.refresh()` +
  arahkan balik ke `/time-study` (bukan ke satu detail penugasan seperti form single, karena
  hasil bulk banyak baris).
- `time-study/page.tsx` (baris ~47-52): tambah link kedua di sebelah "+ Tugaskan Partisipan":
  `<Link href="/time-study/tugaskan-banyak">+ Tugaskan Banyak Sekaligus</Link>`.
- Tambah `loading.tsx`/`error.tsx` untuk route baru (wajib per konvensi repo — lihat
  "Konvensi & Invariants" di `CLAUDE.md`).

### Langkah 5 — Update `CLAUDE.md` (Revisi Desain)

Tambah entri baru di bagian "Revisi Desain" `anjab-abk-web-app/CLAUDE.md`, gaya sama seperti
entri `[2026-07-12] DCS & WCP: hapus sesi...` yang sudah ada — deskripsikan form bulk baru untuk
TI/OPM/TS, bahwa form single TETAP ADA (beda dari migrasi DCS/WCP), dan bentuk response
`{created, skipped}` yang perlu ditangani UI.

### Langkah 6 — Update `docs-usage/`

Sesuai `dokumentasi-penggunaan-skill` (wajib per "Alur Kerja & Definition of Done" di
`CLAUDE.md`): tambah/perbarui halaman panduan pengguna untuk fitur "tugaskan banyak sekaligus" di
TI, OPM, TS.

### Langkah 7 — Test unit baru

`src/test/` (Vitest + Testing Library), mengikuti pola test yang sudah ada untuk
`wcp/assign-responden.tsx` bila ada (cek dulu apakah komponen itu sudah punya test — bila ada,
tiru strukturnya; bila tidak ada, buat test baru untuk SEMUA komponen baru sekaligus, jangan
biarkan tanpa test):
- Render checkbox list dari `partisipan` prop.
- Pilih beberapa, klik submit → assert body request memuat `partisipan_ids` yang benar.
- Response dengan `skipped` non-kosong → assert alasan tampil dengan label yang benar
  (`formatAlasanSkip`).
- "Pilih semua"/"Batalkan pilihan" bekerja seperti pola WCP/DCS.

### Langkah 8 — Verifikasi E2E

Jalankan `make e2e` untuk spec yang menyentuh TI+SME panel (`e2e/opm.spec.ts`, dan spec lain yang
disebut namanya di komentar `PERIODE_TI` seperti `tahap1.spec.ts` bila ada) setelah backend item
005 sudah live di stack E2E. Bila `e2e/opm.spec.ts` pecah karena auto-populate TI (lihat "Kondisi
sekarang" di atas), perbaiki dengan memindahkan `pastikanSMEPanel` (baris ~273) ke SETELAH
`bekukanTiSampaiTahap3` selesai, sebelum test berikutnya memakai panel itu — pola sama dengan
perbaikan `_opm_common.py` di item 005.

## Kriteria penerimaan

- [ ] Admin bisa memilih banyak partisipan sekaligus (checkbox) dan menugaskan dalam satu submit
      di halaman TI, OPM, dan halaman baru Time Study.
- [ ] Form single yang sudah ada (TI, OPM, `/time-study/buat`) tetap berfungsi tanpa perubahan
      perilaku.
- [ ] Setelah submit bulk, admin melihat berapa yang berhasil DAN daftar yang dilewati beserta
      alasannya dalam Bahasa Indonesia (bukan kode mentah seperti `bukan_anggota_sme_panel`).
- [ ] Daftar partisipan yang ditampilkan di checkbox TI/OPM konsisten dengan filter yang sudah
      dipakai form single (anggota SME panel, belum jadi responden untuk OPM).
- [ ] `npm run build` sukses, tidak ada error TypeScript dari tipe generated baru.

## Skenario uji

Lihat Langkah 7 (unit) dan Langkah 8 (E2E). `make test` (lint + typecheck + unit via Docker) dan
`npm run build` harus sukses sebelum dianggap selesai.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-web-app` dan `npm run build` sukses
- [ ] `docs-usage/` diperbarui (Langkah 6)
- [ ] `CHANGELOG.md` diperbarui
- [ ] `CLAUDE.md` (`anjab-abk-web-app`) diperbarui — entri "Revisi Desain" baru (Langkah 5)
- [ ] E2E terverifikasi hijau (Langkah 8), termasuk spec yang berisiko (`e2e/opm.spec.ts`)
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Blocked by 005** — nama tipe generated (`BulkAssignResult_...`) dan bentuk pasti response
  hanya bisa dipastikan setelah backend item 005 selesai dan `openapi.json` diperbarui. Jangan
  mulai menulis komponen sebelum `npm run gen:api` dijalankan ulang.
- Risiko regresi `e2e/opm.spec.ts` (lihat "Kondisi sekarang") kemungkinan besar TIDAK terjadi
  berkat guard idempoten yang sudah ada, tapi tetap WAJIB diverifikasi — jangan diasumsikan aman
  tanpa menjalankan `make e2e`.
- Pertimbangkan (di luar lingkup wajib, opsional bila ada waktu): tombol "Pilih semua anggota
  panel yang belum jadi responden" sudah otomatis tercakup lewat "Pilih semua" pada checkbox
  list yang sudah difilter ke anggota panel — tidak perlu tombol terpisah "assign dari panel"
  karena filter yang ada sudah menyetarakannya.
