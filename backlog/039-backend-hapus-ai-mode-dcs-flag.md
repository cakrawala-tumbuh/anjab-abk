# Backlog 039 — Backend: hapus tuntas `ai_mode` (AiMode) & `dcs_flag` dari CalHR

> **Repo:** `anjab-abk-backend`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `backend-skill`, `backend-postgresql-skill` (migrasi), `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Feedback user (foto, 2026-07-14) pada halaman Task Inventory **Tahap 3**: dua opsi isian
CalHR harus **DIHILANGKAN** dari produk — **"AI mode"** dan **"Resiko DCS"**. Keputusan produk
sudah terkunci: **hapus tuntas**, bukan sekadar sembunyikan di UI.

Item ini adalah bagian **BACKEND**. Dua field yang dihapus dari kontrak CalHR:

- **`ai_mode`** — enum `AiMode` (`Human-led` / `Co-Pilot` / `AI-assisted`) di isian detail Tahap 3.
- **`dcs_flag`** — `bool` ("Ada risiko DCS") di isian detail Tahap 3.

Keduanya punya **pasangan nilai standar di master** (`std_ai_mode`, `std_dcs_flag` — prefill Tahap 3)
dan **agregat di hasil analisis** (`ai_mode_dist`, `dcs_flag_count`). Semua ikut dihapus, karena
membiarkan sebagiannya menyisakan kontrak setengah jadi (master menyimpan standar untuk field yang
tak lagi ada; hasil melaporkan distribusi field yang tak lagi diisi).

Item **040 (web-app)** menyusul dan **blocked by 039** — web app meregenerasi tipe dari
`openapi.json` yang berubah di item ini (breaking change).

## Keputusan yang sudah dikunci

1. **Hapus, bukan sembunyikan.** Field dilenyapkan dari schema, model ORM, dan DB (DROP kolom) —
   bukan sekadar `exclude` di response atau `disabled` di UI.
2. **Cakupan penuh, semua turunan ikut:** isian per-entri (`ai_mode`, `dcs_flag`), nilai standar
   master (`std_ai_mode`, `std_dcs_flag`), dan agregat hasil (`ai_mode_dist`, `dcs_flag_count`).
3. **Enum `AiMode` dihapus total** dari `calhr.py` — **hanya boleh** setelah dipastikan tidak ada
   pemakai lain (lihat "Kondisi sekarang": terverifikasi 5 importer, semuanya di modul CalHR/master
   yang disentuh item ini). Bila di kemudian hari ditemukan pemakai lain, **jangan** hapus enum-nya —
   turunkan cakupan dan lapor.
4. **`VaType`, `SumberBukti`, `Kondisi` TIDAK disentuh.** `va_type` tetap ada; `va_type_dist` di hasil
   tetap ada. Hanya `ai_mode`/`dcs_flag` yang dibuang.
5. **Migrasi Alembic baru (satu berkas)** yang men-DROP 4 kolom (2 tabel). Ikuti mekanisme inkremental
   gaya Odoo — **jangan** edit revisi lama. Head saat ini = `3b10e24fa970`.
6. **`openapi.json` HARUS diregenerasi** (`python scripts/export_openapi.py openapi.json`). Ini
   breaking change yang menjadi dependency item 040.
7. **Data transaksi produksi TIDAK boleh diasumsikan kosong.** Kolom `ti_detail.ai_mode`/`dcs_flag`
   kemungkinan sudah terisi (ada sesi TI Teranalisis di produksi YPII). DROP kolom = data hilang
   permanen; ini konsekuensi yang diterima (lihat Risiko), tapi wajib dikonfirmasi sadar, bukan
   ditabrak diam-diam.

## Kondisi sekarang (verified)

Semua path relatif ke `anjab-abk-backend/`. Baris bisa bergeser — **baca ulang sebelum edit**.

### Enum sumber (akan dihapus)

| Lokasi | Fakta | ✓ |
|---|---|---|
| `src/anjab_abk_backend/taskinv/schemas/calhr.py:9` | `AiMode = Literal["Human-led", "Co-Pilot", "AI-assisted"]` | ✓ |
| `src/anjab_abk_backend/taskinv/schemas/calhr.py:10` | `VaType = Literal[...]` — **TETAP**, jangan sentuh | ✓ |

**Importer `AiMode` (grep `AiMode` di `src/` → 5 berkas, semuanya modul CalHR/master):** ✓
`schemas/calhr.py` (definisi), `schemas/detail.py`, `schemas/catalog.py`, `schemas/hasil.py`,
`schemas/uraian_tugas.py`. **Tidak ada pemakai di luar Task Inventory** (mis. tidak dipakai
anjab/abk/core). Aman dihapus setelah 4 importer di bawah dibersihkan.

### Isian per-entri (Tahap 3)

| Lokasi | Fakta | ✓ |
|---|---|---|
| `schemas/detail.py:7` | `from .calhr import AiMode, Kondisi, SumberBukti, VaType` — buang `AiMode` | ✓ |
| `schemas/detail.py:24` | `TiDetailItem.ai_mode: AiMode = Field(...)` | ✓ |
| `schemas/detail.py:26` | `TiDetailItem.dcs_flag: bool = Field(default=False, ...)` | ✓ |
| `schemas/detail.py:63` | `TiDetailRead.ai_mode: AiMode` | ✓ |
| `schemas/detail.py:65` | `TiDetailRead.dcs_flag: bool` | ✓ |
| `services/detail.py:26,28` | dataclass row in-memory: `ai_mode: str`, `dcs_flag: bool` | ✓ |
| `services/detail.py:85,87,103,105` | assign/insert `ai_mode`/`dcs_flag` (upsert & create in-memory) | ✓ |
| `services/detail_sql.py:35,37` | mapping ORM→Read: `ai_mode=rec.ai_mode`, `dcs_flag=rec.dcs_flag` | ✓ |
| `services/detail_sql.py:74,76,92,94` | upsert (`existing.ai_mode`/`.dcs_flag`) & insert baris baru | ✓ |

### Nilai standar master

| Lokasi | Fakta | ✓ |
|---|---|---|
| `schemas/catalog.py:7` | import `AiMode` (buang) | ✓ |
| `schemas/catalog.py:47,49` | `TiCatalogRead.std_ai_mode: AiMode \| None`, `std_dcs_flag: bool \| None` | ✓ |
| `schemas/uraian_tugas.py:18` | import `AiMode` (buang) | ✓ |
| `schemas/uraian_tugas.py:84,86` | `UraianTugasCreate.std_ai_mode`, `.std_dcs_flag` | ✓ |
| `schemas/uraian_tugas.py:121,123` | `UraianTugasUpdate.std_ai_mode`, `.std_dcs_flag` | ✓ |
| `schemas/uraian_tugas.py:164,166` | `UraianTugasRead.std_ai_mode`, `.std_dcs_flag` | ✓ |
| `services/uraian_tugas.py:80,82` | dataclass row in-memory: `std_ai_mode`, `std_dcs_flag` | ✓ |
| `services/uraian_tugas.py:151,153` | create in-memory meng-assign keduanya | ✓ |
| `services/uraian_tugas_sql.py:69,71` | mapping ORM→Read | ✓ |
| `services/uraian_tugas_sql.py:152,154` | create ORM meng-assign keduanya | ✓ |
| `services/catalog.py:166,168` | build `TiCatalogRead` dari `ut.std_ai_mode`/`ut.std_dcs_flag` | ✓ |

### Agregasi / hasil analisis

| Lokasi | Fakta | ✓ |
|---|---|---|
| `schemas/hasil.py:7` | import `AiMode` (buang) | ✓ |
| `schemas/hasil.py:27,29` | `TiHasilTaskRead.std_ai_mode`, `.std_dcs_flag` (echo standar master) | ✓ |
| `schemas/hasil.py:48` | `TiHasilTaskRead.ai_mode_dist: dict[str, int]` | ✓ |
| `schemas/hasil.py:50` | `TiHasilTaskRead.dcs_flag_count: int` | ✓ |
| `services/analisis.py:49,51` | isi `std_ai_mode`/`std_dcs_flag` dari `cat` (di `compute_task_terpilih`) | ✓ |
| `services/analisis.py:88,90,92-93` | akumulasi `dcs_count`, `ai_dist[d.ai_mode] += 1`, `if d.dcs_flag` | ✓ |
| `services/analisis.py:112,114` | isi `ai_mode_dist=ai_dist`, `dcs_flag_count=dcs_count` | ✓ |

> Catatan: `services/analisis.py:49,51` mengisi `std_ai_mode`/`std_dcs_flag` untuk objek
> `TiTaskTerpilihRead`/hasil task. Cek nama field target di `schemas/hasil.py` (`std_ai_mode` di
> `hasil.py:27`) & pastikan semua yang men-set field ini ikut dibuang.

### Model ORM & migrasi

| Lokasi | Fakta | ✓ |
|---|---|---|
| `src/anjab_abk_backend/models.py:533` | `TiDetailModel.ai_mode: Mapped[str] = mapped_column(String(20), nullable=False)` | ✓ |
| `src/anjab_abk_backend/models.py:535` | `TiDetailModel.dcs_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)` | ✓ |
| `src/anjab_abk_backend/models.py:423` | `TiUraianTugasModel.std_ai_mode: Mapped[str \| None] = ...(String(20), nullable=True)` | ✓ |
| `src/anjab_abk_backend/models.py:425` | `TiUraianTugasModel.std_dcs_flag: Mapped[bool \| None] = ...(Boolean, nullable=True)` | ✓ |
| `migrations/versions/` head | `3b10e24fa970` (down chain terverifikasi, tak direferensikan sbg `down_revision` mana pun) | ✓ |
| `migrations/versions/*b2bbd3afbe65*`, `*0c932069e90e*` | kolom-kolom ini **muncul** di initial schema & revisi "tambah nilai standar CalHR" — JANGAN diedit; buat revisi DROP baru | ✓ |

### Seed / katalog (tidak terdampak — dikonfirmasi negatif)

- `src/anjab_abk_backend/taskinv/seed.py` — grep `ai_mode`/`dcs_flag`/`AiMode` → **nihil**. ✓
- `scripts/seed_catalog.py`, `scripts/purge_task_catalog.py` — nihil. ✓
- **Tidak ada** `taskinv/services/seed.py` (yang ada: `taskinv/seed.py`, `dcs/seed.py`, `wcp/seed.py`,
  `seed_db.py`) — tidak satupun menyentuh `ai_mode`/`dcs_flag`. ✓

### Test yang menyebut field ini (grep `tests/`)

| Lokasi | Peran | Perlakuan |
|---|---|---|
| `tests/test_taskinv.py:496,498` | `_ditem()` isi detail Tahap 3 | buang 2 baris |
| `tests/test_taskinv.py:540,542` | `_STD_MASTER` (payload uraian tugas std) | buang 2 baris |
| `tests/test_taskinv.py:563,565` | `_detail_item_dari_standar()` | buang 2 baris |
| `tests/test_taskinv.py:665,695,738,754` | item detail di berbagai test | buang baris `ai_mode` |
| `tests/test_taskinv.py:721` | `@pytest.mark.parametrize("field", ["sumber_bukti", "ai_mode", "va_type"])` | **hapus `"ai_mode"`** dari daftar (sisakan `sumber_bukti`, `va_type`) |
| `tests/test_taskinv_master.py:562,564` | `_STD_PAYLOAD` | buang 2 baris |
| `tests/test_taskinv_master.py:632` | `test_uraian_tugas_std_invalid_enum` kirim `std_ai_mode: "Ngawur"` → 422 | **ganti field uji** ke enum lain yg masih ada, mis. `std_sumber_bukti: "Ngawur"` atau `std_va_type: "Ngawur"` |
| `tests/test_sesi_cascade.py:112` | insert `TiDetailModel(..., ai_mode="MANDIRI", ...)` langsung via ORM | buang argumen `ai_mode=` |

> `tests/test_taskinv.py` juga akan perlu penyesuaian assert bila ada test yang memeriksa
> `ai_mode_dist`/`dcs_flag_count` di hasil — grep ulang `ai_mode_dist`/`dcs_flag_count` di `tests/`
> saat eksekusi (saat ini penulisan backlog: kemunculan di `tests/` = definisi payload di atas, bukan
> assert hasil; tetap verifikasi ulang setelah edit schema hasil).

## Langkah eksekusi

Urutan disarankan: schema → service → model → migrasi → enum → test → regen openapi.

### Langkah 1 — Schema Pydantic

1. `schemas/detail.py`: hapus `ai_mode`/`dcs_flag` dari `TiDetailItem` (baris ~24,26) dan
   `TiDetailRead` (baris ~63,65); rapikan import `AiMode` (baris 7).
2. `schemas/catalog.py`: hapus `std_ai_mode`/`std_dcs_flag` dari `TiCatalogRead` (~47,49); rapikan
   import (baris 7).
3. `schemas/uraian_tugas.py`: hapus `std_ai_mode`/`std_dcs_flag` di **tiga** kelas
   (`UraianTugasCreate` ~84,86; `UraianTugasUpdate` ~121,123; `UraianTugasRead` ~164,166); rapikan
   import (baris 18).
4. `schemas/hasil.py`: hapus `std_ai_mode`/`std_dcs_flag` (~27,29), `ai_mode_dist` (~48),
   `dcs_flag_count` (~50); rapikan import (baris 7).

### Langkah 2 — Service layer

1. `services/detail.py` (in-memory): hapus field dataclass (~26,28) + semua assign (~85,87,103,105).
2. `services/detail_sql.py`: hapus mapping baca (~35,37) + upsert/insert (~74,76,92,94).
3. `services/uraian_tugas.py` (in-memory): hapus field dataclass (~80,82) + assign create (~151,153).
4. `services/uraian_tugas_sql.py`: hapus mapping baca (~69,71) + assign create (~152,154).
5. `services/catalog.py`: hapus `std_ai_mode=`/`std_dcs_flag=` saat build `TiCatalogRead` (~166,168).
6. `services/analisis.py`: hapus set `std_ai_mode`/`std_dcs_flag` (~49,51); hapus akumulator
   `dcs_count` & loop `ai_dist` untuk ai_mode (~88,90,92-93); hapus argumen `ai_mode_dist=`/
   `dcs_flag_count=` (~112,114). Pastikan `va_dist`/`va_type_dist` **tetap**.

### Langkah 3 — Model ORM

`src/anjab_abk_backend/models.py`:
- `TiDetailModel`: hapus `ai_mode` (~533) & `dcs_flag` (~535).
- `TiUraianTugasModel`: hapus `std_ai_mode` (~423) & `std_dcs_flag` (~425).

### Langkah 4 — Migrasi Alembic (DROP kolom)

`make migration m="hapus ai_mode dcs_flag dari calhr"` → review berkas hasil autogenerate di
`migrations/versions/`. Pastikan:
- `down_revision` = `3b10e24fa970` (head saat ini).
- `upgrade()` men-`op.drop_column()` **4 kolom**: `ti_detail.ai_mode`, `ti_detail.dcs_flag`,
  `ti_uraian_tugas.std_ai_mode`, `ti_uraian_tugas.std_dcs_flag`.
- `downgrade()` menambahkan kembali kolomnya. Catatan: `ti_detail.ai_mode` semula `NOT NULL` tanpa
  server_default — pada `downgrade` beri `server_default` sementara atau `nullable=True` agar tak
  gagal di tabel berisi (autogenerate biasanya tak menangani ini; sesuaikan tangan, konsisten dgn
  konvensi downgrade best-effort di repo, mis. `3b10e24fa970`).
- **Jangan** menumpuk perubahan lain ke berkas ini.

### Langkah 5 — Hapus enum `AiMode`

Setelah semua importer bersih (Langkah 1), hapus baris `AiMode = Literal[...]` di `calhr.py:9`.
Pastikan `VaType`/`SumberBukti`/`Kondisi` tetap. Grep ulang `AiMode` di `src/` → harus **nihil**.

### Langkah 6 — Test

Terapkan perlakuan di tabel "Test yang menyebut field ini". Khusus:
- `tests/test_taskinv.py:721` — buang `"ai_mode"` dari `parametrize`.
- `tests/test_taskinv_master.py:632` — alihkan uji enum-invalid ke field enum yang masih ada.
- Grep ulang `ai_mode_dist`/`dcs_flag_count`/`std_ai_mode`/`std_dcs_flag` di `tests/` → harus nihil
  setelah edit.

### Langkah 7 — Regen OpenAPI

`python scripts/export_openapi.py openapi.json` (atau target make bila ada). Commit `openapi.json`
sebagai bagian perubahan — ini kontrak yang dikonsumsi item 040.

## Kriteria penerimaan

- [ ] `openapi.json` **tidak lagi** memuat `ai_mode`, `dcs_flag`, `std_ai_mode`, `std_dcs_flag`,
      `ai_mode_dist`, `dcs_flag_count` di skema mana pun (verifikasi: `grep -i "ai_mode\|dcs_flag"
      openapi.json` → nihil).
- [ ] Enum `AiMode` tak ada lagi di `src/` (`grep -rn AiMode src/` → nihil).
- [ ] `POST/PUT .../detail` menolak (422) payload yang menyertakan `ai_mode`/`dcs_flag`
      (schema `extra="forbid"` di `TiDetailItem`/`TiDetailUpsert` sudah aktif — field asing ditolak).
- [ ] `GET .../sesi/{id}/hasil` & `POST .../analisis` mengembalikan `TiHasilTaskRead` **tanpa**
      `ai_mode_dist`/`dcs_flag_count`; `va_type_dist` tetap ada dan benar.
- [ ] `GET .../catalog` & `uraian-tugas` tak lagi mengeluarkan `std_ai_mode`/`std_dcs_flag`.
- [ ] Migrasi baru `alembic upgrade head` mulus di DB berisi; `tests/test_migrations.py`
      (`test_schema_matches_models`, `test_single_head`) hijau — schema ↔ model konsisten & satu head.
- [ ] `make test` hijau (lint + unit).

## Skenario uji

- **`tests/test_migrations.py`** (penjaga): `test_schema_matches_models` akan **gagal** bila model
  diubah tanpa revisi DROP — pastikan revisi Langkah 4 ada. `test_single_head` menjaga tak ada cabang.
- **`tests/test_taskinv.py`**: alur end-to-end Tahap 1→3→analisis (`_ditem`, `_detail_submit`,
  assert hasil) harus lulus tanpa `ai_mode`/`dcs_flag`. Test enum-invalid `test_detail_enum_invalid`
  (parametrize) hanya menguji `sumber_bukti`+`va_type` setelah `ai_mode` dibuang.
- **`tests/test_taskinv_master.py`**: create/update/read uraian tugas dengan `std_*` (tanpa
  `std_ai_mode`/`std_dcs_flag`); `test_uraian_tugas_std_invalid_enum` dialihkan ke field enum lain.
- **`tests/test_sesi_cascade.py`**: insert `TiDetailModel` langsung tanpa `ai_mode=`.
- **Tambahan disarankan**: satu test yang menegaskan `TiDetailItem` menolak (`422`) `ai_mode` sebagai
  field asing (`extra="forbid"`), memastikan penghapusan benar-benar menutup kontrak.
- Perintah: `make test` (lint + unit dalam Docker).

## Definition of done

- [ ] `make test` hijau di `anjab-abk-backend`.
- [ ] `openapi.json` diregenerasi & di-commit (breaking change; dependency item 040).
- [ ] `CHANGELOG.md` diperbarui (breaking: field CalHR `ai_mode`/`dcs_flag` + turunannya dihapus).
- [ ] Entri "Revisi Desain" ditambahkan di `CLAUDE.md` repo backend (perubahan model + migrasi DROP).
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`; buat/aktifkan item **040 (web-app)** yang
      blocked-by 039.

## Risiko & catatan

- **Data hilang permanen (DROP kolom).** `ti_detail.ai_mode`/`dcs_flag` kemungkinan **terisi** di
  produksi (sesi TI Teranalisis di YPII). DROP menghapusnya tanpa jalan pulih dari aplikasi.
  `std_ai_mode`/`std_dcs_flag` di `ti_uraian_tugas` (master katalog) juga bisa terisi. **Ambil backup
  DB (`make backup`) sebelum `alembic upgrade head` di produksi.** Ini konsekuensi yang sudah diterima
  oleh keputusan produk — tapi konfirmasi ke user sebelum migrasi dijalankan di produksi.
- **Aturan data panel SME (dari MEMORY):** "data panel SME jangan pernah disentuh". Migrasi ini
  hanya men-DROP kolom `ai_mode`/`dcs_flag`, **tidak** menghapus baris responden/panel — aman, tapi
  jangan tergoda menambah pembersihan baris ke berkas migrasi yang sama.
- **Enum `AiMode` hanya boleh dihapus bila 0 pemakai tersisa.** Sudah terverifikasi 5 importer,
  semuanya di modul yang disentuh item ini. Bila grep pasca-edit masih menemukan `AiMode`, **jangan**
  hapus enum — selesaikan importer itu dulu atau turunkan cakupan & lapor.
- **`VaType` mudah keliru ikut terbawa.** `va_type`/`va_type_dist`/`std_va_type` **tetap ada**. Hanya
  `ai_mode`/`dcs_flag` yang dibuang. Jangan sentuh `SumberBukti`/`Kondisi`/`VaType`.
- **Breaking change lintas repo.** Web app (item 040) & MCP mengonsumsi `openapi.json`. Backend harus
  dirilis lebih dulu; item 040 meregenerasi tipe setelahnya. Bila MCP juga mengekspos field ini,
  perlu item MCP terpisah (di luar cakupan 039; cek `anjab-abk-mcp` saat merencanakan 040).
- **Harness test vs produksi (`autoflush`):** tak relevan langsung di sini (tak ada create parent+child
  baru), tapi bila menambah test yang menyentuh urutan flush, ingat produksi `autoflush=False`
  (lihat Gotcha `CLAUDE.md` backend).
