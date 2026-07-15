# Backlog 037 — TiSesi: ganti `periode` → `cabang` (enum) & hapus `min_responden`/`max_responden`

> **Repo:** `anjab-abk-backend`
> **Status:** Sebagian SIAP DIEKSEKUSI — **satu keputusan migrasi data lama BUTUH KONFIRMASI USER** (nilai `cabang` untuk baris `ti_sesi` produksi yang sudah ada). Sisanya (schema, model, service, router, test, regen openapi) siap dieksekusi.
> **Blocked by:** — (tidak diblok)
> **Skill yang dipakai:** `backend-skill`, `backend-postgresql-skill` (migrasi Alembic), `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Lahir dari feedback user (foto tulisan tangan, 2026-07-14) atas form **"Mulai Analisis Jabatan"**
Task Inventory. Dua perubahan pada model `TiSesi` di sisi backend:

1. **`periode` → `cabang`.** Field `periode` (string `YYYY-MM`, wajib) diganti **sepenuhnya** oleh
   `cabang`: enum tetap 2 nilai `{"Bandung", "Semarang"}` (hardcoded, bukan relasi ke master data).
2. **Hapus `min_responden` & `max_responden`** dari `TiSesi` sepenuhnya, **dan buang aturan validasi
   422** yang menolak pembuatan sesi ketika jumlah anggota SME panel > `max_responden` (aturan yang
   baru ditambahkan di item 028). Konsekuensinya: konsep "batas atas jumlah responden" hilang dari TI
   — persis seperti keputusan yang sudah diambil untuk DCS/WCP (`CLAUDE.md` backend entri
   `[2026-07-12]`: "1 deployment = 1 studi; tidak ada lagi batas atas jumlah responden").

Ini **breaking change** untuk kontrak API (`openapi.json` berubah) → menuntut item lanjutan di web-app
(item 038, menyusul) dan audit MCP tool `buat_ti_sesi`/`ti_tambah_responden*`.

## Keputusan yang sudah dikunci

- `cabang` adalah **enum hardcoded 2 nilai**: `"Bandung"` dan `"Semarang"`. Bukan FK, bukan lookup ke
  master data. Pola: `CabangSesi = Literal["Bandung", "Semarang"]` (meniru `StatusSesi = Literal[...]`
  yang sudah ada di `schemas/sesi.py:10`).
- `cabang` **menggantikan** `periode` — bukan menambah di sampingnya. Tidak ada lagi kolom/field
  `periode` di `TiSesi` (model, schema Create/Update/Read, service, search field, in-memory `_Record`).
- `min_responden` dan `max_responden` **dihapus total** dari `TiSesi` (model + semua schema + service).
- Aturan 422 "panel > max_responden" (item 028) **dibuang**. Auto-populate responden dari SME panel
  saat create sesi **tetap ada** dan sekarang **selalu memasukkan SELURUH anggota panel** tanpa cap.
- Konsep cap `max_responden` juga **dicabut dari lapisan responden TI** (parameter fungsi + cabang
  `kapasitas_penuh`), karena tidak ada lagi sumber nilai cap. TI tidak lagi punya batas atas responden.
- **Scope = HANYA `TiSesi` (Task Inventory).** `OpmSesi` punya field `periode`/`min_responden`/
  `max_responden` yang paralel (`opm/schemas/sesi.py:28,35,38`) — **JANGAN disentuh** di item ini
  (satu item = satu concern; OPM adalah item terpisah bila diinginkan).

## Kondisi sekarang (verified — path:baris, dicek 2026-07-15 ✓; baris bisa bergeser, baca ulang)

### Field `periode`, `min_responden`, `max_responden` yang harus diubah/dihapus

| Lokasi | Baris ✓ | Isi |
|---|---|---|
| `models.py` `TiSesiModel` | `434` ✓ | `periode: Mapped[str] = mapped_column(String(7), nullable=False)` |
| `models.py` `TiSesiModel` | `437` ✓ | `min_responden ... Integer ... default=3` |
| `models.py` `TiSesiModel` | `438` ✓ | `max_responden ... Integer ... default=10` |
| `taskinv/schemas/sesi.py` `TiSesiCreate` | `23-29` ✓ | `periode: str` (wajib, `min/max_length=7`, `pattern=YYYY-MM`) |
| `taskinv/schemas/sesi.py` `TiSesiCreate` | `30-35` ✓ | `min_responden` (default 3) & `max_responden` (default 10) |
| `taskinv/schemas/sesi.py` `TiSesiUpdate` | `51` ✓ | `periode: str \| None` |
| `taskinv/schemas/sesi.py` `TiSesiUpdate` | `53-54` ✓ | `min_responden`/`max_responden` opsional |
| `taskinv/schemas/sesi.py` `TiSesiRead` | `66` ✓ | `periode: str` |
| `taskinv/schemas/sesi.py` `TiSesiRead` | `68-69` ✓ | `min_responden`/`max_responden` |
| `taskinv/services/sesi_sql.py` `_sesi_field_map` | `38` ✓ | `"periode": FieldSpec(column=TiSesiModel.periode)` (search) |
| `taskinv/services/sesi_sql.py` `_to_read` | `53,56-57` ✓ | `periode=`, `min_responden=`, `max_responden=` |
| `taskinv/services/sesi_sql.py` `create()` | `96-97` ✓ | validasi `min_responden > max_responden` → `ValidationAppError` |
| `taskinv/services/sesi_sql.py` `create()` | `98-107` ✓ | **dedup (jabatan_id, periode)** → `ConflictError` |
| `taskinv/services/sesi_sql.py` `create()` | `121-127` ✓ | **aturan 028 yang harus dibuang**: `len(anggota_ids) > data.max_responden` → 422 |
| `taskinv/services/sesi_sql.py` `create()` | `138,141-142` ✓ | isi `rec.periode/min/max` |
| `taskinv/services/sesi_sql.py` `create()` | `159-161` ✓ | `assign_ti_responden_banyak(..., max_responden=data.max_responden)` (auto-populate) |
| `taskinv/services/sesi_sql.py` `update()` | `170-173` ✓ | validasi `min > max` saat update |
| `taskinv/services/sesi.py` (in-memory) | `16,36,38-39,53,74,77-78,104-105,108-122,137-141,204` ✓ | `SEARCHABLE_FIELDS`, `_Record`, `_to_read`, `create` (min>max + dedup periode), `update` |

### Ripple `max_responden` di lapisan responden (WAJIB ikut dibereskan — kalau tidak, `sesi.max_responden` hilang → AttributeError di router)

| Lokasi | Baris ✓ | Isi |
|---|---|---|
| `api/v1/taskinv_responden.py` | `111` ✓ | `rsp_service.create(sesi_id, payload, sesi.max_responden)` |
| `api/v1/taskinv_responden.py` | `171` ✓ | `rsp_service.assign_banyak(sesi_id, anggota_valid, max_responden=sesi.max_responden)` |
| `taskinv/services/responden_sql.py` `assign_ti_responden_banyak` | `43-116` ✓ | param `max_responden`; cabang `kapasitas_penuh` di `99-101` |
| `taskinv/services/responden_sql.py` `SqlTiRespondenService.create` | `173-177` ✓ | param `max_responden` + cap `current >= max_responden` |
| `taskinv/services/responden_sql.py` `assign_banyak` | `192-196` ✓ | teruskan `max_responden` |
| `taskinv/services/responden.py` (Protocol + in-memory) | `37-41,90-95,109-138` ✓ | signature `max_responden` + cap + cabang `kapasitas_penuh` |

### Downstream yang membaca `sesi.periode` (akan pecah begitu kolom hilang — WAJIB diputuskan)

| Lokasi | Baris ✓ | Isi |
|---|---|---|
| `taskinv/services/analisis.py` | `124` ✓ | `periode=sesi.periode` → mengisi `TiHasilSesiRead.periode` |
| `taskinv/schemas/hasil.py` `TiHasilSesiRead` | `62` ✓ | `periode: str` |
| `taskinv/schemas/kuesioner.py` `TiKuesionerItemRead` | `34` ✓ | `sesi_periode: str` |
| `api/v1/taskinv_kuesioner.py` | `81` ✓ | `sesi_periode=sesi.periode` |

### Fakta pendukung

- **`min_responden` TI tidak dipakai sebagai cutoff analisis.** Grep di seluruh `taskinv/` → hanya
  dipakai di validasi `min > max` (yang ikut terhapus) dan disimpan/ditampilkan. **Berbeda dari DCS**
  yang memakai `min_responden` sebagai cutoff. ⇒ **Menghapus `min_responden` dari TI TIDAK berimplikasi
  ke logika analisis** — aman. ✓ (verified: nol kemunculan `min_responden` di `analisis.py`)
- Migrasi Alembic inkremental gaya Odoo, satu berkas/perubahan. Contoh terbaru + pola guard/backfill/
  downgrade: `migrations/versions/20260712_3b10e24fa970_dcs_wcp_hapus_sesi_instrumen_singleton.py` ✓
  (mencakup drop kolom `periode`/`max_responden` untuk DCS/WCP — **rujukan pola langsung**).
- Regen openapi: `python scripts/export_openapi.py openapi.json` (dijalankan dari root repo, script
  sudah sisipkan `src/` ke path) ✓. `openapi.json` jangan diedit tangan (`CLAUDE.md` "Jangan Sentuh").
- Penjaga migrasi: `tests/test_migrations.py::test_schema_matches_models` gagal bila model berubah
  tanpa revisi Alembic baru; `test_single_head` mencegah cabang divergen ✓.
- Test relevan: `tests/test_taskinv.py` — helper `_sesi_payload` (`32-40`, hardcode `periode` +
  `min/max_responden`), `_create_sesi` (`51-54`); `test_sesi_duplicate_conflict` (`142-145`, dedup
  periode); `test_sesi_min_gt_max_rejected` (`148-150`); `test_create_sesi_panel_melebihi_max_responden_ditolak`
  (`1183-1193`, **aturan 028 yang akan dibuang**); `test_create_sesi_panel_muat_semua_anggota`
  (`1196-1204`); banyak test lain memakai `periode=_uniq_periode()`/`min_responden`/`max_responden`
  di payload (mis. `892,898,956,988,1014-1016,1088-1090,1126-1128,1403,1505,1586,1616-1648,1758`). ✓
- **`CabangSesi` belum ada** di kode; `StatusSesi = Literal[...]` di `schemas/sesi.py:10` adalah pola acuan. ✓

## Langkah eksekusi

> Urutan disarankan: schema → model → service (sesi) → service (responden) → router → migrasi →
> downstream (hasil/kuesioner) → test → regen openapi. Semua di dalam satu repo `anjab-abk-backend`.

### Langkah 1 — Schema Pydantic (`taskinv/schemas/sesi.py`)

- Tambah alias tipe: `CabangSesi = Literal["Bandung", "Semarang"]` (dekat `StatusSesi`).
- `TiSesiCreate`: hapus `periode`, `min_responden`, `max_responden`. Tambah
  `cabang: CabangSesi = Field(description="Cabang lokasi kajian.", examples=["Bandung"])` (**wajib**,
  tanpa default — menggantikan `periode` yang juga wajib). `model_config = ConfigDict(extra="forbid")`
  sudah ada → payload lama yang masih mengirim `periode`/`min_responden`/`max_responden` akan **422**
  (ini benar & diinginkan; web-app item 038 menyesuaikan).
- `TiSesiUpdate`: hapus `periode`, `min_responden`, `max_responden`. Tambah
  `cabang: CabangSesi | None = Field(default=None, ...)`.
- `TiSesiRead`: hapus `periode`, `min_responden`, `max_responden`. Tambah `cabang: CabangSesi`.

### Langkah 2 — Model ORM (`models.py` `TiSesiModel`)

- Hapus baris `periode` (`434`), `min_responden` (`437`), `max_responden` (`438`).
- Tambah `cabang: Mapped[str] = mapped_column(String(20), nullable=False)` (enum ditegakkan di layer
  Pydantic; DB simpan string — konsisten dengan `status: String(20)`).

### Langkah 3 — Service sesi (`taskinv/services/sesi_sql.py` + `sesi.py` in-memory)

`sesi_sql.py`:
- `_sesi_field_map`: ganti entry `"periode"` menjadi `"cabang": FieldSpec(column=TiSesiModel.cabang)`.
- `_to_read`: `periode=rec.periode` → `cabang=rec.cabang`; hapus `min_responden=`/`max_responden=`.
- `create()`:
  - Hapus blok validasi `min > max` (`96-97`).
  - **Keputusan dedup (BUTUH KEPUTUSAN, lihat Risiko):** blok dedup `(jabatan_id, periode)` (`98-107`)
    memakai `periode`. Ganti kunci ke **`(jabatan_id, cabang)`** (rekomendasi default) ATAU hapus
    dedup. Rekomendasi: `(jabatan_id, cabang)` dengan pesan `f"Sesi untuk jabatan '{data.jabatan_id}'
    cabang '{data.cabang}' sudah ada."`.
  - **Hapus** blok aturan 028 (`121-127`) sepenuhnya.
  - `rec = TiSesiModel(...)`: `periode=data.periode` → `cabang=data.cabang`; hapus `min_responden=`/
    `max_responden=`.
  - `assign_ti_responden_banyak(self._s, rec.id, panel.partisipan_ids)` — **tanpa** `max_responden`
    (lihat Langkah 4).
- `update()`: hapus blok validasi `min > max` (`170-173`). `changes` loop tetap generik (akan menerima
  `cabang`).

`sesi.py` (in-memory `_Record`, `TiSesiService` Protocol, `InMemoryTiSesiService`):
- `SEARCHABLE_FIELDS` (`16`): ganti `"periode"` → `"cabang"`.
- `_Record` (`36,38-39`): `periode` → `cabang`; hapus `min_responden`/`max_responden`.
- `_to_read` (`74,77-78`): sesuaikan.
- `create` (`104-122`): hapus validasi `min>max`; ganti dedup ke `cabang`; isi `rec.cabang`.
- `update` (`137-141`): hapus validasi `min>max`.

### Langkah 4 — Lapisan responden: cabut cap `max_responden` (`taskinv/services/responden_sql.py`, `responden.py`, router)

Konsep batas atas responden dicabut dari TI (tidak ada lagi sumber nilai cap):

- `assign_ti_responden_banyak` (`responden_sql.py:43-116`): hapus parameter `max_responden`; hapus
  blok `if current >= max_responden: skipped ... "kapasitas_penuh"; continue` (`99-101`) dan variabel
  `current` bila jadi tak terpakai. Skip lain (`duplikat_input`, `sudah_terdaftar`) tetap.
- `SqlTiRespondenService.create` (`173-177`): hapus parameter `max_responden` + blok cap.
- `SqlTiRespondenService.assign_banyak` (`192-196`): hapus `max_responden`.
- `responden.py` (Protocol `37-41` + `InMemoryTiRespondenService.create` `90-95` + `assign_banyak`
  `109-138`, termasuk cabang `kapasitas_penuh` `136-138`): samakan — buang `max_responden` & cap.
- Router `api/v1/taskinv_responden.py`: `111` → `rsp_service.create(sesi_id, payload)`; `171` →
  `rsp_service.assign_banyak(sesi_id, anggota_valid)`.
- Catatan: string alasan `"kapasitas_penuh"` di `schemas/common.py`/OPM tetap dipakai OPM — **jangan
  hapus definisinya**, hanya berhenti memakainya di jalur TI.

### Langkah 5 — Migrasi Alembic (satu berkas baru)

1. Setelah model diubah, jalankan `make migration m="ti_sesi ganti periode jadi cabang hapus min max responden"`.
2. **Review & sesuaikan** berkas hasil autogenerate. Isi minimal:
   - `op.add_column("ti_sesi", sa.Column("cabang", sa.String(20), nullable=...))` — lihat keputusan
     backfill di Risiko.
   - **Backfill baris lama** (`ti_sesi` produksi punya `periode` mis. `"2026-07"`, TANPA `cabang`):
     `UPDATE ti_sesi SET cabang = :nilai` dengan `:nilai` = **KEPUTUSAN USER** (Bandung/Semarang).
     Baru setelah backfill → `op.alter_column("ti_sesi", "cabang", nullable=False)`.
   - `op.drop_column("ti_sesi", "periode")`, `op.drop_column("ti_sesi", "min_responden")`,
     `op.drop_column("ti_sesi", "max_responden")`.
   - `downgrade()`: best-effort (tambah kembali kolom, `periode` di-restore sebagai `nullable=True`
     karena nilai tak diketahui — konvensi `3b10e24fa970`). Hapus `cabang`.
3. `alembic upgrade head` (via harness test / lokal) untuk verifikasi rantai.

### Langkah 6 — Downstream `periode` (hasil & kuesioner)

`analisis.py:124` `periode=sesi.periode` akan pecah. Putuskan (BUTUH KEPUTUSAN kecil, lihat Risiko):
- **Rekomendasi:** ganti `periode` → `cabang` di `TiHasilSesiRead` (`hasil.py:62`) & `TiKuesionerItemRead.sesi_periode`
  → `sesi_cabang` (`kuesioner.py:34`), lalu `analisis.py:124` `cabang=sesi.cabang` dan
  `taskinv_kuesioner.py:81` `sesi_cabang=sesi.cabang`. Ini menambah perubahan kontrak (sudah breaking
  di web-app), jadi konsisten.
- Alternatif minimal: hapus field `periode`/`sesi_periode` tanpa pengganti. Pilih salah satu, catat di
  CHANGELOG. (Rekomendasi: ganti ke `cabang`, jangan sekadar hapus — cabang berguna di UI hasil/kuesioner.)

### Langkah 7 — Test

- `tests/test_taskinv.py`:
  - `_sesi_payload` (`32-40`): buang `periode`/`min_responden`/`max_responden`, tambah `"cabang": "Bandung"`.
    Ganti/hapus helper `_uniq_periode` (`18-19`) — dedup kini `(jabatan_id, cabang)`; test dedup harus
    memakai jabatan yang sama + cabang sama.
  - `test_sesi_duplicate_conflict` (`142-145`): sesuaikan ke `cabang` (dua create jabatan sama, cabang
    sama → 409).
  - `test_sesi_min_gt_max_rejected` (`148-150`): **hapus** (aturan tak ada lagi).
  - `test_create_sesi_panel_melebihi_max_responden_ditolak` (`1183-1193`): **hapus** ATAU ubah jadi
    penegasan bahwa panel besar (mis. 11 anggota) kini **berhasil** dibuat & seluruh 11 jadi responden
    (regresi positif — buktikan cap benar-benar hilang).
  - Semua payload lain yang menyertakan `periode`/`min_responden`/`max_responden`
    (`892,898,956,988,1014-1016,1088-1090,1126-1128,1403,1586,1616-1648`) → ganti ke `cabang`; PATCH
    `min_responden` (`1505,1758`) → PATCH `cabang` atau hapus assertion.
  - Tambah test baru: create dengan `cabang` invalid (mis. `"Jakarta"`) → 422; Read mengembalikan
    `cabang`; search by `cabang`.
- `tests/test_migrations.py`: tidak perlu diubah (otomatis memverifikasi schema↔model & single head).
- Bila ada test yang meng-assert `periode` di hasil/kuesioner → sesuaikan (Langkah 6).

### Langkah 8 — Regen openapi + dokumentasi

- `python scripts/export_openapi.py openapi.json`.
- `CHANGELOG.md` di bawah `## [Unreleased]`: catat breaking change (rename field + drop field) + bump
  versi (minor, pra-1.0).
- `CLAUDE.md` backend: tambah entri Revisi Desain `[2026-07-15] TI: periode → cabang, hapus min/max_responden`.

## Kriteria penerimaan

- [ ] `TiSesiCreate`/`Update`/`Read`, `TiSesiModel`, kedua service (SQL + in-memory), dan search field
      **tidak lagi** mengandung `periode`, `min_responden`, `max_responden`; mengandung `cabang`.
- [ ] `POST /task-inventory/sesi` dengan `{"jabatan_id","cabang":"Bandung"}` → 201; body Read memuat `cabang`.
- [ ] `cabang` di luar `{"Bandung","Semarang"}` → 422.
- [ ] Payload lama yang menyertakan `periode`/`min_responden`/`max_responden` → 422 (`extra="forbid"`).
- [ ] Panel SME dengan > 10 anggota → sesi **tetap dibuat**, **seluruh** anggota jadi responden (cap hilang).
- [ ] Tidak ada `AttributeError` `sesi.max_responden`/`sesi.periode` di jalur responden/hasil/kuesioner.
- [ ] Migrasi Alembic baru ada (satu berkas), `alembic upgrade head` sukses, `test_migrations.py` hijau.
- [ ] `openapi.json` diregenerasi & mencerminkan `cabang` (tanpa `periode`/`min`/`max_responden` di TiSesi).

## Skenario uji

`make test` (lint ruff + pytest PostgreSQL di Docker; identik lokal & CI). Fokus:
- `tests/test_taskinv.py` disesuaikan (Langkah 7) — hijau.
- `tests/test_migrations.py::test_schema_matches_models` & `::test_single_head` — hijau (bukti model↔migrasi konsisten).
- Test baru: enum invalid → 422; panel besar → semua jadi responden; search `cabang`.
- Test `tests/test_auth_guards.py` tidak terdampak (tidak ada endpoint baru).

## Definition of done

- [ ] `make test` hijau (lint + unit) di `anjab-abk-backend`.
- [ ] `openapi.json` diregenerasi (`python scripts/export_openapi.py openapi.json`).
- [ ] `CHANGELOG.md` diperbarui (breaking change + bump versi).
- [ ] `CLAUDE.md` backend diperbarui (entri Revisi Desain baru — perubahan model/alur).
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`; buat item lanjutan **038 (web-app)** & audit MCP
      (`buat_ti_sesi`, `ti_tambah_responden*`) karena `openapi.json` berubah.

## Risiko & catatan

- **[BUTUH KONFIRMASI USER — pemblokir migrasi] Nilai `cabang` untuk baris `ti_sesi` produksi lama.**
  Deployment YPII sudah punya sesi TI dengan `periode` (mis. `"2026-07"`) dan **tanpa** `cabang`.
  Kolom `cabang` `NOT NULL` menuntut nilai untuk setiap baris lama. YPII punya **dua** cabang (berkas
  `Form_SME_Panel_YPII_Bandung` & `..._Semarang` ada di working tree) → nilai default **tidak bisa
  ditebak**. **JANGAN mengarang.** Opsi: (a) user menetapkan satu nilai backfill global (Bandung ATAU
  Semarang); (b) user memetakan per-sesi; (c) kolom dibuat `nullable=True` sementara (menyalahi
  "wajib" di produk — kurang disukai). Aturan user (memory): **data transaksi produksi jangan disentuh
  sembarangan** — backfill hanya setelah nilai dikonfirmasi.
- **[KEPUTUSAN kecil] Kunci uniqueness sesi.** Saat ini `(jabatan_id, periode)`. Rekomendasi:
  `(jabatan_id, cabang)`. Karena satu jabatan biasanya terikat satu cabang, ini efektif ~= satu sesi TI
  per jabatan. Bila itu tak diinginkan, dedup bisa dibuang. Pilih eksplisit; jangan biarkan menabrak.
- **[KEPUTUSAN kecil] Downstream `periode` di hasil & kuesioner** (Langkah 6): ganti ke `cabang`
  (rekomendasi) vs hapus. Apa pun pilihannya, `analisis.py:124`, `hasil.py:62`, `kuesioner.py:34`,
  `taskinv_kuesioner.py:81` **wajib** ikut diubah — kalau tidak, `POST /sesi/{id}/analisis` &
  `GET /kuesioner/saya` akan `AttributeError` (500) begitu kolom `periode` hilang.
- **Breaking change kontrak** — web-app (form "Mulai Analisis Jabatan" TI) & MCP tool `buat_ti_sesi`
  masih mengirim `periode`/`min_responden`/`max_responden` → akan 422 setelah deploy. Rilis backend &
  penyesuaian klien (item 038 + MCP) harus dikoordinasikan (backend dulu → regen `openapi.json` →
  klien menyusul), pola sama dengan item 018/019.
- **`OpmSesi` sengaja tidak disentuh** — punya `periode`/`min_responden`/`max_responden` paralel
  (`opm/schemas/sesi.py`). Bila produk juga ingin OPM pakai `cabang`, itu item terpisah.
- `min_responden` TI **tidak** dipakai sebagai cutoff analisis (berbeda dari DCS) → penghapusannya
  bersih, tanpa dampak ke statistik. Sudah diverifikasi (nol kemunculan di `analisis.py`).
