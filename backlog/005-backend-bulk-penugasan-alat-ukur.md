# Backlog 005 — Backend: penugasan massal (bulk) partisipan untuk TS, TI, OPM

> **Repo:** `anjab-abk-backend`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `backend-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Saat ini penugasan partisipan ke alat ukur ANJAB/ABK tidak konsisten:

- **WCP & DCS** sudah bulk (`POST /{wcp|dcs}/responden` menerima `partisipan_ids: list[str]`,
  atomik) — **tidak disentuh** oleh item ini.
- **TS (Time Study)** hanya single (`POST /time-study/penugasan`, satu `partisipan_id`/panggilan).
- **TI (Task Inventory)** hanya single (`POST .../sesi/{id}/responden`), dan meski jabatan TI
  punya SME panel, anggotanya **tidak** otomatis jadi responden — admin harus menambahkan satu
  per satu, padahal OPM (alat ukur sejenis, juga jabatan+SME-panel) **sudah** auto-assign semua
  anggota panel saat sesi dibuat (`SqlOpmSesiService.create()`).
- **OPM** backend sudah auto-assign dari panel saat sesi dibuat, tapi endpoint tambah-manual
  (single) yang sudah ada di backend belum punya rekan bulk.

Tujuan item ini: (1) tambahkan mekanisme penugasan **massal** untuk TS, TI, OPM (WCP/DCS sudah
punya, tidak diubah); (2) TI ikut auto-assign anggota SME panel saat sesi dibuat, menyusul pola
yang sudah ada di OPM; (3) endpoint manual (single) yang sudah ada **tidak dihapus/diubah
kontraknya** — bulk ditambahkan berdampingan. Item lanjutan `006` (repo `anjab-abk-mcp`)
meng-expose endpoint baru dari item ini sebagai MCP tool.

## Keputusan yang sudah dikunci

1. **TI: auto-populate best-effort saat sesi dibuat.** `SqlTiSesiService.create()` akan mencari
   `SMEPanelModel` untuk `jabatan_id` sesi; jika ada panel dengan ≥1 anggota, semua anggotanya
   langsung dibuat sebagai `TiRespondenModel`. Jika tidak ada panel/panel kosong, sesi tetap
   dibuat kosong seperti sekarang (TI harus tetap bisa dipakai tanpa panel / responden anonim
   tanpa `partisipan_id`, tidak seperti OPM yang mewajibkan panel saat create — itu TIDAK diubah).
2. **Endpoint bulk baru (TS, TI, OPM) bersifat idempoten/skip-on-conflict**, bukan atomik
   all-or-nothing seperti WCP/DCS. Tiap `partisipan_id` yang sudah terdaftar/tidak valid
   dilewati (skip) dan dilaporkan alasannya; sisanya tetap berhasil dibuat. Response envelope
   seragam: `{created: [...], skipped: [{partisipan_id, alasan}]}`.
3. **Urutan pengecekan per `partisipan_id` di SEMUA endpoint bulk (TS/TI/OPM) — WAJIB persis
   urutan ini, jangan divariasikan antar modul:**
   1. Dedup terhadap payload itu sendiri (id yang sudah muncul sebelumnya di list yang sama) →
      skip `duplikat_input`. Lakukan ini **di awal, dalam satu pass**, sebelum pengecekan lain
      apa pun — supaya id yang duplikat DAN sekaligus bukan anggota panel hanya dilaporkan
      sekali (`duplikat_input`), bukan double-report.
   2. *(khusus TI & OPM)* Bukan anggota SME panel jabatan sesi → skip `bukan_anggota_sme_panel`.
   3. Sudah punya row responden/penugasan (di sesi ybs untuk TI/OPM; global untuk TS) → skip
      `sudah_terdaftar`.
   4. *(khusus TI & OPM)* Kapasitas sesi (`jumlah responden sesi saat ini, TERMASUK yang baru
      dibuat dalam batch yang sama sejauh ini` `>= max_responden`) → skip `kapasitas_penuh`.
   5. Lolos semua → buat row baru, tambahkan ke `created`.

   Konsekuensi untuk implementasi TI (lihat Langkah 3): karena helper bersama
   `assign_ti_responden_banyak` dipakai juga oleh endpoint bulk manual yang butuh langkah #2
   (panel-filter) SEBELUM langkah #3/#4, endpoint bulk manual TI harus melakukan dedup (#1) dan
   panel-filter (#2) sendiri di layer endpoint TERLEBIH DAHULU (satu pass atas `partisipan_ids`
   mentah, urutan #1 lalu #2), baru memanggil `assign_ti_responden_banyak` dengan daftar id yang
   sudah unik dan sudah pasti anggota panel — helper itu sendiri baru menjalankan #3/#4. Untuk
   OPM, `assign_banyak` menjalankan seluruh 5 langkah dalam SATU fungsi/SATU loop (tidak dipecah
   endpoint vs service) karena OPM tidak butuh berbagi logika ini dengan jalur lain seperti TI.
4. **String alasan skip harus identik lintas modul** — jangan buat variasi per modul:
   `sudah_terdaftar`, `duplikat_input`, `bukan_anggota_sme_panel`, `kapasitas_penuh`.
5. **Tidak perlu migrasi Alembic** — tidak ada tabel/kolom baru, hanya service/schema/endpoint baru.

## Kondisi sekarang (verified)

| Alat ukur | Backend single (verified) | Backend bulk sekarang |
|---|---|---|
| TS | `ts/services/penugasan_sql.py:63-79`, endpoint `POST /api/v1/time-study/penugasan` (`api/v1/ts_penugasan.py:52-73`) | tidak ada |
| TI | `taskinv/services/responden_sql.py:96-112`, endpoint `POST /api/v1/task-inventory/sesi/{sesi_id}/responden` (`api/v1/taskinv_responden.py:58-103`) | tidak ada |
| OPM | `opm/services/responden_sql.py:81-118`, endpoint `POST /api/v1/opm/sesi/{sesi_id}/responden` (`api/v1/opm_responden.py:59-92`) | tidak ada |
| WCP/DCS | — | ✓ sudah bulk atomik (`wcp/services/responden_sql.py:115-132`, `dcs/services/responden_sql.py:115-132`) — referensi gaya, tidak diubah |

Auto-assign dari panel saat sesi dibuat **sudah ada** di OPM (`opm/services/sesi_sql.py:125-244`,
step insert ~221-241, dipicu panel lookup ~136-142) — ini jadi template untuk TI. TI hari ini
sama sekali tidak menyentuh `sme_panel` di `SqlTiSesiService.create()`
(`taskinv/services/sesi_sql.py:94-120`).

`SMEPanelModel`/`SMEPanelAnggotaModel` (`models.py:179-207`) — satu partisipan bisa jadi anggota
banyak panel (M2M via `sme_panel_anggota`), tanpa FK sungguhan ke `partisipan`/dari
`ti_responden`/`opm_responden` (semua `partisipan_id` adalah string biasa, tanpa constraint DB).

**Pola konkret yang WAJIB ditiru persis (verified, bukan tebakan):**
- **Generic response model sudah terbukti aman dipakai** di codebase ini: `Page[T]` (di
  `schemas/common.py:21-25`) sudah dipakai sebagai `response_model=Page[XxxRead]` di
  `api/v1/taskinv_detil_tugas.py:95,163` dan `api/v1/partisipan.py:103`. `BulkAssignResult[T]`
  yang baru ditambahkan ke `schemas/common.py` mengikuti pola `Page[T]` itu persis (class
  `Generic[T]` + `response_model=BulkAssignResult[XxxRead]` di endpoint) — tidak perlu trik lain.
- **Prefix ID row baru — pakai persis prefix yang sudah dipakai fungsi `create()` single di file
  yang sama, jangan membuat prefix baru:**
  - TS: `f"tpn_{uuid.uuid4().hex[:8]}"` (lihat `ts/services/penugasan_sql.py:72`).
  - TI: `f"trsp_{uuid.uuid4().hex[:8]}"` (lihat `taskinv/services/responden_sql.py:103`).
  - OPM: `f"oprs_{uuid.uuid4().hex[:8]}"` (lihat `opm/services/responden_sql.py:111`).
- **Pengecekan kapasitas `max_responden` — pola sudah ada, tiru gaya variabelnya:** TI
  single-create memakai pola `if current >= max_responden:` (`taskinv/services/responden_sql.py:96-100`);
  OPM single-create memakai `if current_count >= max_responden:` (`opm/services/responden_sql.py:85-91`).
  Versi bulk harus menghitung `current`/`current_count` SEKALI di awal fungsi (via `COUNT`
  terhadap tabel responden untuk `sesi_id` itu), lalu increment counter lokal itu (bukan query
  ulang ke DB) setiap kali satu row berhasil dibuat dalam loop yang sama — ini yang dimaksud
  "termasuk yang baru dibuat dalam batch yang sama" pada aturan urutan pengecekan di atas.

**Fixture test yang akan pecah oleh Langkah 3 (auto-populate TI) — perbaikan WAJIB, bagian dari
item ini, bukan opsional:**
- `tests/_opm_common.py::_setup_jabatan_panel_ti` (baris 42-106) membuat SME panel (baris 52-58)
  **sebelum** sesi TI (baris 66-77), lalu memanggil `mulai-tahap2` (baris 93) **tanpa**
  `paksa=true`. Begitu auto-populate aktif, sesi TI akan otomatis punya 2 responden tambahan
  (anggota panel) yang tidak submit seleksi → `submitted(2) < total(4)` → `mulai-tahap2` gagal
  422. **Perbaikan:** pindahkan blok pembuatan panel (baris 52-58) ke akhir helper, setelah
  `mulai-tahap3` (setelah baris 97), sebelum `return`. Helper dipakai oleh `test_opm_sesi.py`,
  `test_opm_responden.py`, `test_opm_analisis.py` — semua harus tetap lulus.
- `tests/test_opm_responden.py::test_kuesioner_saya_hanya_open` (baris ~234-298, panel dibuat
  baris ~252-254 sebelum sesi TI baris ~261-264) — pindahkan pembuatan panel ke setelah
  `mulai-tahap3` (sebelum sesi OPM dibuat, baris ~274; OPM tetap butuh panel ada saat itu).

Semua nomor baris di atas WAJIB dicek ulang oleh agen pelaksana sebelum mengedit (baris bisa
bergeser sejak rencana ini ditulis).

## Langkah eksekusi

### Langkah 1 — Response envelope bersama

`src/anjab_abk_backend/schemas/common.py` (pola sama seperti `Page[T]` yang sudah ada di file
ini): tambah

```python
class BulkSkipped(BaseModel):
    partisipan_id: str
    alasan: str  # "sudah_terdaftar" | "duplikat_input" | "bukan_anggota_sme_panel" | "kapasitas_penuh"

class BulkAssignResult(BaseModel, Generic[T]):
    created: list[T]
    skipped: list[BulkSkipped]
```

### Langkah 2 — TS bulk

`ts/schemas/penugasan.py`: tambah `TsPenugasanBulkCreate{partisipan_ids: list[str]
(min_length=1), aktif: bool=True, catatan: str|None}`.

`ts/services/penugasan.py` (Protocol) + `penugasan_sql.py`: tambah `create_banyak(partisipan_ids,
*, aktif, catatan) -> BulkAssignResult[TsPenugasanRead]` — loop per id, skip `duplikat_input` (id
berulang dalam payload) dan `sudah_terdaftar` (sudah ada row `TsPenugasanModel` untuk partisipan
itu — TS punya `UNIQUE` DB constraint asli di kolom ini, jadi bungkus tiap insert dengan
`session.begin_nested()` + tangkap `IntegrityError` → skip, bukan gagal total).

`api/v1/ts_penugasan.py`: tambah `POST /api/v1/time-study/penugasan/bulk`
(`response_model=BulkAssignResult[TsPenugasanRead]`, admin-only, sejajar dengan endpoint single
yang ada, ditaruh persis setelahnya).

### Langkah 3 — TI: helper bulk bersama + auto-populate saat create + endpoint bulk manual

Bagian paling penting — logika insert-banyak-responden **satu implementasi**, dipakai baik oleh
auto-populate maupun endpoint bulk manual (jangan duplikasi):

- `taskinv/services/responden_sql.py`: tambah **fungsi level-modul** (bukan method service, agar
  bisa dipanggil langsung dari `sesi_sql.py` tanpa instansiasi service):
  `assign_ti_responden_banyak(session, sesi_id, partisipan_ids, *, max_responden) ->
  BulkAssignResult[TiRespondenRead]` — insert per id, skip `duplikat_input`, `sudah_terdaftar`
  (sudah ada `TiRespondenModel` untuk `(sesi_id, partisipan_id)` itu — cukup pre-check, TI tidak
  punya UNIQUE constraint DB di sini), `kapasitas_penuh` (jumlah responden sesi sudah
  `>= max_responden`, lihat aturan counter di "Kondisi sekarang"). Fungsi ini **tidak**
  memvalidasi keanggotaan panel — pemanggil yang menyaring `partisipan_ids` sebelum memanggil.
- `taskinv/services/sesi_sql.py`, di `create()` (baris ~94-120): setelah `self._s.add(rec)`,
  sebelum `self._s.flush()` yang sudah ada, tambahkan: cari `SMEPanelModel` dengan
  `jabatan_id == data.jabatan_id`; jika ada dan `panel.anggota` tidak kosong, panggil
  `assign_ti_responden_banyak(self._s, rec.id, panel.partisipan_ids, max_responden=data.max_responden)`.
  Tidak perlu try/except — kegagalan di sini tidak fatal karena hanya jalan bila panel ada.
- `taskinv/schemas/responden.py`: tambah `TiRespondenBulkCreate{partisipan_ids: list[str]
  (min_length=1)}`.
- `api/v1/taskinv_responden.py`: tambah `POST /api/v1/task-inventory/sesi/{sesi_id}/responden/bulk`
  — endpoint ini (beda dari auto-populate) melakukan dedup (#1) dan **menyaring keanggotaan
  panel di layer endpoint** (#2) TERLEBIH DAHULU dalam satu pass atas `partisipan_ids` mentah
  (pola sama seperti endpoint single yang sudah ada di baris 89-102: cari panel by
  `sesi.jabatan_id`, `partisipan_id` yang bukan anggota → skip dengan alasan
  `bukan_anggota_sme_panel`), baru memanggil `assign_ti_responden_banyak` dengan daftar id yang
  sudah unik & sudah pasti anggota panel (helper itu sendiri hanya menjalankan langkah #3/#4).
  Cek status sesi harus `DRAFT`/`TAHAP1` (sama seperti precondition create single) — tolak (422)
  seluruh request bila tidak, jangan per-id skip untuk precondition sesi ini.
- `taskinv/services/responden.py` (Protocol) + in-memory impl: tambah method wrapper
  `assign_banyak(...)` yang delegasi ke fungsi modul di atas.

### Langkah 4 — OPM bulk

`opm/schemas/responden.py`: tambah `OpmRespondenBulkCreate{partisipan_ids: list[str]
(min_length=1)}` (tanpa `nama`/`jabatan_label` — diresolusi otomatis dari
`PartisipanModel`/`JabatanModel`, mengikuti pola auto-populate OPM yang sudah ada, bukan pola
single-create manual yang minta field itu).

`opm/services/responden.py` (Protocol) + `responden_sql.py`: tambah `assign_banyak(sesi_id,
partisipan_ids, *, max_responden, jabatan_id) -> BulkAssignResult[OpmRespondenRead]` — validasi
keanggotaan panel + kapasitas + idempotensi (seluruh 5 langkah urutan pengecekan) **di dalam
service ini sendiri, satu fungsi/satu loop** (beda dari TI: OPM's single-create juga sudah
melakukan validasi panel di service layer, bukan endpoint — ikuti konvensi modul masing-masing,
jangan diseragamkan paksa dengan TI).

`api/v1/opm_responden.py`: tambah `POST /api/v1/opm/sesi/{sesi_id}/responden/bulk`, cek status
sesi `DRAFT`/`OPEN` (422 seluruh request bila tidak, sama seperti precondition TI).

### Langkah 5 — Perbaiki 2 fixture test

Lihat detail lengkap di bagian "Kondisi sekarang" di atas (`_setup_jabatan_panel_ti` dan
`test_kuesioner_saya_hanya_open`). Wajib dilakukan sebelum menjalankan test TI/OPM secara penuh
— kalau tidak, hampir seluruh suite OPM akan gagal begitu Langkah 3 (auto-populate) aktif.

### Langkah 6 — Test baru

- `test_ts_penugasan.py`: bulk happy-path campuran baru+sudah-ada; `duplikat_input`; payload
  kosong ditolak 422 (Pydantic `min_length`); admin-only.
- `test_taskinv.py`: sesi dibuat untuk jabatan dengan panel berisi anggota → responden otomatis
  muncul untuk semua anggota (assert `GET .../responden` — mirip gaya assert
  `test_opm_sesi.py::test_create_sesi_ok`); sesi untuk jabatan tanpa panel → tetap kosong
  (no-op); sesi untuk panel tanpa anggota → tetap kosong; endpoint bulk manual: happy path, skip
  `sudah_terdaftar`, skip `bukan_anggota_sme_panel`, skip `kapasitas_penuh`, skip
  `duplikat_input`, admin-only.
- `test_opm_responden.py`: endpoint bulk manual — happy path + keempat skip case + admin-only.
- Jalankan ulang suite OPM penuh (`test_opm_sesi.py`, `test_opm_responden.py`,
  `test_opm_analisis.py`) untuk memastikan fixture yang diperbaiki di Langkah 5 tidak merusak
  assersi lain.

## Kriteria penerimaan

- [ ] `POST /api/v1/time-study/penugasan/bulk` bisa dipanggil dengan banyak `partisipan_id`
      sekaligus; yang sudah terdaftar/duplikat dilewati (dilaporkan di `skipped`), sisanya dibuat.
- [ ] `POST /api/v1/task-inventory/sesi/{sesi_id}/responden/bulk` bekerja sama seperti di atas,
      plus menyaring non-anggota SME panel dan kapasitas `max_responden`.
- [ ] `POST /api/v1/opm/sesi/{sesi_id}/responden/bulk` bekerja sama seperti TI.
- [ ] Membuat sesi TI baru untuk jabatan yang sudah punya SME panel berisi anggota → anggota
      panel otomatis muncul sebagai responden TANPA panggilan tambahan apa pun.
- [ ] Membuat sesi TI baru untuk jabatan tanpa panel (atau panel kosong) → sesi tetap dibuat
      kosong seperti perilaku sebelumnya (tidak error, tidak berubah).
- [ ] Endpoint single (manual) yang sudah ada — `POST /time-study/penugasan`,
      `POST .../task-inventory/sesi/{id}/responden`, `POST .../opm/sesi/{id}/responden` — tidak
      berubah kontraknya sama sekali.
- [ ] `_setup_jabatan_panel_ti` dan `test_kuesioner_saya_hanya_open` diperbaiki urutannya dan
      seluruh suite OPM tetap lulus.
- [ ] Tidak ada migrasi Alembic baru yang ditambahkan (tidak dibutuhkan).

## Skenario uji

Lihat daftar lengkap di Langkah 6. Semua harus lulus via `make test` (lint + unit di dalam
Docker, sesuai `anjab-abk-backend/CLAUDE.md` — perintah sama di lokal dan CI).

## Definition of done

- [ ] `make test` hijau di `anjab-abk-backend`
- [ ] `CHANGELOG.md` diperbarui
- [ ] `CLAUDE.md` (`anjab-abk-backend`) diperbarui — tambah entri "Revisi Desain" baru
      mendeskripsikan endpoint bulk TS/TI/OPM + auto-populate TI, mengikuti gaya entri
      `[2026-07-12] DCS & WCP: hapus entitas sesi...` yang sudah ada
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **A4 (perbaikan fixture) bukan opsional** — tanpa memindahkan pembuatan SME panel ke setelah
  `mulai-tahap3` di kedua fixture yang disebutkan, hampir seluruh suite test OPM akan gagal
  begitu auto-populate TI (Langkah 3) aktif. Ini konsekuensi tak terhindarkan dari Keputusan #1,
  bukan bug baru.
- Duplikat `TiRespondenModel`/`OpmRespondenModel` untuk `(sesi_id, partisipan_id)` yang sama
  tetap mungkin terjadi bila endpoint single (existing, tidak disentuh) dipanggil untuk
  partisipan yang sudah di-auto-populate/bulk-assign — tidak ada UNIQUE constraint DB untuk ini,
  sama seperti sebelumnya. Ini celah pre-existing, bukan regresi dari item ini — jangan
  ditambal di sini (di luar lingkup), cukup dicatat.
- TS bulk memakai `begin_nested()` (SAVEPOINT) per baris — cukup untuk ukuran batch wajar
  (puluhan partisipan). Bila batch sangat besar (ratusan+) di masa depan, pertimbangkan
  `INSERT ... ON CONFLICT DO NOTHING` — di luar lingkup item ini.
- Repo `anjab-abk-mcp` (item `006`) bergantung pada endpoint baru di item ini — pastikan item ini
  selesai & `make test` hijau sebelum mengeksekusi `006`.
