# Backlog 001 — Backend: hapus sesi DCS & WCP → instrumen singleton + penugasan langsung

> **Repo:** `anjab-abk-backend`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Memblokir:** 002 (MCP), 003 (web app) — keduanya butuh `openapi.json` hasil item ini.
> **Skill:** `backend-skill`, `backend-postgresql-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Menghapus entitas **sesi** dari DCS dan WCP, menggantinya dengan pola Time Study: **partisipan
di-assign langsung ke instrumen**. Yang tetap dipertahankan dari sesi adalah dua hal yang benar-benar
dibutuhkan analisis — ambang `min_responden` dan momen **penutupan** yang membekukan kohort sebelum
Cronbach alpha dihitung — keduanya pindah ke **satu baris konfigurasi singleton per instrumen**.

Latar belakang & pembenaran lengkap: lihat [BACKLOG.md](../BACKLOG.md) bagian "Konteks lintas-item".

**Sesi TI dan OPM TIDAK disentuh sama sekali di item ini.** Jangan tergoda menyeragamkan.

## Keputusan yang sudah dikunci

1. **1 deployment = 1 studi.** Karena itu `periode` di DCS/WCP **dihapus** (redundan — periodenya adalah
   deployment itu sendiri).
2. **Instrumen adalah singleton**, satu baris per instrumen, dibuat oleh migrasi. Tidak ada endpoint
   create/delete instrumen. PK adalah string tetap: `"dcs"` dan `"wcp"`.
3. **Status instrumen: `OPEN → CLOSED → ANALYZED`.** **Tidak ada `DRAFT`** — instrumen sudah OPEN sejak
   migrasi. Inilah friksi yang dihapus (dulu admin harus klik "Buka Sesi"). Reopen `CLOSED → OPEN`
   diizinkan selama status belum `ANALYZED`.
4. **`max_responden` dihapus.** Dalam satu studi, batas atas hanya bikin admin mentok tanpa alasan.
   `min_responden` **dipertahankan** (cutoff analisis, default 6).
5. **Responden = penugasan.** `DcsRespondenModel`/`WcpRespondenModel` tetap ada (jawaban sudah FK ke
   sana), tapi kehilangan `sesi_id` dan mendapat `UNIQUE(partisipan_id)`. Tidak ada model/tabel baru
   bernama "penugasan" — hindari churn yang tidak perlu.
6. **`wcp_sesi_id` sebagai parameter analisis DCS dihapus.** K-Index sekarang selalu membaca instrumen
   WCP yang satu-satunya itu. Parameternya jadi tidak punya makna.
7. **Assign responden mendukung bulk**: satu request boleh berisi banyak `partisipan_id`.
8. Migrasi **menolak jalan (abort)** kalau ada >1 sesi DCS/WCP yang punya responden — lihat "Risiko".

## Kondisi sekarang (verified per 2026-07-12)

Semua model ORM ada di satu file: `src/anjab_abk_backend/models.py`.

| Fakta | Lokasi |
|---|---|
| `DcsSesiModel` — `periode`, `status`, `min_responden` (6), `max_responden` (8), `catatan`, `created_at`. Tanpa jabatan/unit kerja. | `models.py:236-245` ✓ |
| `DcsRespondenModel` — FK `sesi_id → dcs_sesi.id ON DELETE CASCADE`; `nama`, `jabatan_label` (teks bebas, bukan FK), `partisipan_id` (nullable), `sudah_submit`, `submitted_at` | `models.py:248` ✓ |
| `DcsJawabanModel` — FK CASCADE ke responden, `UNIQUE(responden_id, item_id)` | `models.py:263` ✓ |
| `WcpSesiModel` / `WcpRespondenModel` / `WcpJawabanModel` — struktur identik DCS | `models.py:303`, `:315`, `:330` ✓ |
| Partisipan sudah unik **lintas seluruh sesi DCS** (global, bukan per sesi) | `dcs/services/responden_sql.py:87-95` ✓ |
| Tambah responden hanya saat `OPEN`; dibatasi `max_responden` | `api/v1/dcs_responden.py:86-90`; `dcs/services/responden_sql.py:83` ✓ |
| Analisis: butuh status `CLOSED`/`ANALYZED`, cek `min_responden`, auto-transisi ke `ANALYZED` | `api/v1/dcs_hasil.py:90-113` ✓ |
| K-Index lintas instrumen via query param `wcp_sesi_id` | `api/v1/dcs_hasil.py:42-63, 79, 110, 133, 151` ✓ |
| Agregasi (mean/stdev per subskala, Cronbach alpha, `risk_flag`, `k_index`) | `dcs/services/analisis.py:142-206` ✓ |
| Kuesioner partisipan hanya tampil bila sesi `OPEN` | `api/v1/dcs_kuesioner.py:57` ✓ |
| State machine `_VALID_TRANSITIONS` | `dcs/services/sesi.py:18-22`, `wcp/services/sesi.py` ✓ |
| **Acuan pola tanpa sesi**: `TsPenugasanModel` (`partisipan_id` unique + `aktif`), `_require_active` | `models.py:553-562`; `api/v1/ts_log.py:51-63` ✓ |
| Migrasi terakhir (parent revision) | `migrations/versions/20260712_a4aeb5bcbe81_fk_cascade_sesi_responden_jawaban.py` ✓ |
| Preseden penghapusan sesi (baca ini dulu!) | `migrations/versions/20260704_0a58616358f4_ts_hapus_sesi_penugasan_berbasis_.py` ✓ |

**Agen pelaksana wajib membaca ulang file-file di atas sebelum mengedit** — nomor baris bisa bergeser.

---

## Langkah eksekusi

Kerjakan **DCS sampai tuntas dulu** (model → service → router → test hijau), baru **WCP** dengan
menyalin polanya. Jangan kerjakan dua-duanya paralel — WCP identik dan akan lebih cepat setelah DCS
selesai.

### Langkah 1 — Model ORM (`src/anjab_abk_backend/models.py`)

Ganti `DcsSesiModel` dengan:

```
DcsInstrumenModel        (tabel dcs_instrumen)   # singleton
  id             String(10) PK                    # nilainya SELALU "dcs"
  status         String(20) NOT NULL default "OPEN"   # OPEN | CLOSED | ANALYZED
  min_responden  Integer NOT NULL default 6
  catatan        Text nullable
  closed_at      _ts nullable                     # kapan kohort dibekukan (baru — sesi lama tak punya)
  created_at     _ts(index=True)
```

Ubah `DcsRespondenModel`:
- **hapus** kolom `sesi_id` beserta FK & relationship-nya
- `partisipan_id` → tambah `UniqueConstraint("partisipan_id")` di `__table_args__`
  (PostgreSQL mengizinkan banyak NULL, jadi responden lama tanpa partisipan tidak menghalangi)
- sisanya (`nama`, `jabatan_label`, `sudah_submit`, `submitted_at`) tetap

`DcsJawabanModel` **tidak berubah** (sudah FK ke responden, bukan ke sesi).

Idem untuk WCP (`WcpInstrumenModel` id `"wcp"`, `min_responden` default 6).

### Langkah 2 — Migrasi Alembic

Satu berkas per perubahan, gaya inkremental (lihat `CLAUDE.md` backend & memory
`anjab-abk-backend-migrasi`). Gunakan `make migration`. `down_revision` = `20260712_a4aeb5bcbe81`.

Berkas: `<tanggal>_<hash>_dcs_wcp_hapus_sesi_instrumen_singleton.py`

`upgrade()` harus:
1. **Guard**: `SELECT sesi_id, count(*) FROM dcs_responden GROUP BY sesi_id` — kalau menghasilkan **>1
   baris**, `raise RuntimeError` dengan pesan jelas (lihat "Risiko"). Idem `wcp_responden`.
2. Buat tabel `dcs_instrumen`, sisipkan satu baris `id='dcs'`:
   - `min_responden` & `catatan` **disalin dari sesi DCS yang punya responden** (kalau ada); kalau
     tidak ada sesi sama sekali → pakai default (`min_responden=6`, `catatan=NULL`).
   - `status`: petakan `DRAFT|OPEN → 'OPEN'`, `CLOSED → 'CLOSED'`, `ANALYZED → 'ANALYZED'`.
3. `ALTER TABLE dcs_responden DROP COLUMN sesi_id` + `CREATE UNIQUE` pada `partisipan_id`.
   Responden dari sesi yatim (tanpa responden — tidak mungkin) tidak perlu ditangani.
4. `DROP TABLE dcs_sesi`.
5. Ulangi 2–4 untuk WCP.

`downgrade()`: cukup `raise NotImplementedError` bila membalik butuh menebak sesi — **tapi cek dulu
konvensi repo** di migrasi `20260704_0a58616358f4` (penghapusan sesi TS) dan ikuti apa pun yang
dilakukan di sana. Konsistensi > preferensi.

Test penjaga schema↔model yang sudah ada di repo harus tetap hijau.

### Langkah 3 — Service layer (`src/anjab_abk_backend/dcs/services/`)

- **`sesi.py` + `sesi_sql.py` → ganti nama jadi `instrumen.py` + `instrumen_sql.py`.**
  Protocol `DcsInstrumenService`: `get()`, `update(min_responden?, catatan?)`, `tutup()`, `buka_ulang()`,
  `set_analyzed()`. Tidak ada `create`/`delete`/`list`/`search`.
  `_VALID_TRANSITIONS = {"OPEN": {"CLOSED"}, "CLOSED": {"OPEN", "ANALYZED"}, "ANALYZED": set()}`.
  `tutup()` mengisi `closed_at`.
  `get()` harus **selalu** mengembalikan baris (dijamin migrasi); kalau hilang → `raise` 500, jangan
  auto-create diam-diam.
- **`responden.py` + `responden_sql.py`**: buang seluruh parameter/filter `sesi_id`.
  - `list_all()` menggantikan `list_by_sesi(sesi_id)`
  - `create(partisipan_id, nama, jabatan_label)` → cek instrumen berstatus `OPEN` (kalau tidak, `ConflictError`),
    cek partisipan belum terdaftar (`ConflictError` — pindahkan logika dari `responden_sql.py:87-95`,
    sekarang jadi constraint DB sungguhan, tetap pre-check + backstop `IntegrityError` sesuai pola
    `anjab/services/sme_panel_sql.py`)
  - **hapus** pengecekan `max_responden`
  - `create_banyak(partisipan_ids: list[str])` untuk bulk — atomik: kalau satu gagal, semua batal.
- **`jawaban_sql.py`**: cek `sesi_id` diganti cek status instrumen `OPEN`.
- **`analisis.py`**: `compute_hasil_sesi(...)` → `compute_hasil(...)`; input `responden` sekarang seluruh
  responden ber-`sudah_submit`, tanpa filter sesi. **Logika statistiknya jangan diubah sama sekali** —
  mean/stdev/Cronbach alpha/risk_flag/k_index tetap persis. Ini refactor scope, bukan perubahan metode.

Idem `wcp/services/`.

### Langkah 4 — Router (`src/anjab_abk_backend/api/v1/`)

Hapus `dcs_sesi.py` & `wcp_sesi.py`. Peta endpoint baru (patuhi pola router yang ada: `response_model`,
`summary`, `operation_id`, envelope `responses`, `_WRITE_GUARDS`, blok `Idempotency-Key`):

| Lama | Baru |
|---|---|
| `GET/POST /dcs/sesi`, `GET/PATCH/DELETE /dcs/sesi/{id}`, `POST /dcs/sesi/search` | **dihapus** |
| `POST /dcs/sesi/{id}/buka` | **dihapus** (instrumen lahir OPEN) |
| — | `GET /dcs/instrumen` → `DcsInstrumenRead` (`operation_id="dcs_instrumen_get"`) |
| — | `PATCH /dcs/instrumen` → ubah `min_responden`, `catatan` (`dcs_instrumen_update`) |
| `POST /dcs/sesi/{id}/tutup` | `POST /dcs/instrumen/tutup` (`dcs_instrumen_tutup`) |
| — | `POST /dcs/instrumen/buka-ulang` (`dcs_instrumen_buka_ulang`) — hanya dari `CLOSED` |
| `GET /dcs/sesi/{id}/responden` | `GET /dcs/responden` (`dcs_responden_list`) |
| `POST /dcs/sesi/{id}/responden` | `POST /dcs/responden` — body terima **`partisipan_ids: list[str]`** (`dcs_responden_create`) |
| `GET/DELETE /dcs/responden/{id}` | tetap (path sudah tidak mengandung sesi) |
| `PUT/POST/GET /dcs/responden/{id}/jawaban*` | tetap |
| `POST /dcs/sesi/{id}/analisis` | `POST /dcs/analisis` — **tanpa** param `wcp_sesi_id` (`dcs_analisis`) |
| `GET /dcs/sesi/{id}/hasil` | `GET /dcs/hasil` — **tanpa** param `wcp_sesi_id` (`dcs_hasil`) |
| `GET /dcs/sesi/{id}/hasil-responden/{rid}` | `GET /dcs/hasil-responden/{rid}` |
| `GET /dcs/kuesioner/saya` | tetap — tapi field respons `sesi_id`/`sesi_periode`/`sesi_catatan`/`sesi_status` → `instrumen_status` + `catatan` |

Di `dcs_hasil.py`: `_compute_wcp_risk_score()` tidak lagi menerima `wcp_sesi_id`; ia membaca seluruh
responden WCP ber-submit. K-Index dihitung **selalu** (tidak lagi opsional), kecuali WCP belum punya
responden ber-submit → `wcp_risk = None` seperti sekarang.

Perbarui registrasi router di tempat router dirakit (cari `include_router` untuk `dcs_sesi`).

### Langkah 5 — Skema Pydantic (`dcs/schemas/`, `wcp/schemas/`)

- `sesi.py` → `instrumen.py`: `DcsInstrumenRead`, `DcsInstrumenUpdate`. Hapus `DcsSesiCreate/Read/Update`.
- `responden.py`: `DcsRespondenCreate` → field `partisipan_ids: list[str]` (min 1). `DcsRespondenRead`
  buang `sesi_id`.
- `kuesioner.py`: `DcsKuesionerItemRead` — buang `sesi_id`/`sesi_periode`/`sesi_catatan`, ganti
  `sesi_status` → `instrumen_status`.
- `hasil.py`: buang `sesi_id` dari respons hasil.

### Langkah 6 — Seed & dokumentasi

- `scripts/seed_db.py` (atau di mana pun sesi DCS/WCP dibuat saat seed): berhenti membuat sesi; kalau
  seed sebelumnya membuat sesi + responden, sekarang cukup buat responden.
- `CLAUDE.md` backend: perbarui bagian model/alur DCS & WCP (dan catat revisi bertanggal, mengikuti
  gaya catatan revisi yang sudah ada di file itu).
- `CHANGELOG.md`: entri **BREAKING** — endpoint sesi DCS/WCP dihapus.
- Regen `openapi.json` (dibutuhkan item 002 & 003).

---

## Kriteria penerimaan

- [ ] Tidak ada tabel `dcs_sesi`/`wcp_sesi`; tidak ada string `sesi` di `dcs/` & `wcp/` selain di
      changelog/migrasi. Verifikasi: `grep -rn "sesi" src/anjab_abk_backend/dcs src/anjab_abk_backend/wcp`
- [ ] `GET /api/v1/dcs/instrumen` mengembalikan status `OPEN` pada database yang baru dimigrasi, tanpa
      admin melakukan apa pun.
- [ ] Admin bisa assign 5 partisipan ke DCS dalam **satu** request `POST /dcs/responden`.
- [ ] `POST /dcs/analisis` menolak (422) bila responden ber-submit < `min_responden`, dan otomatis
      men-transisi `CLOSED → ANALYZED` bila lolos — persis seperti perilaku lama.
- [ ] Nilai `k_index` yang dihasilkan pada data yang sama **identik** dengan hasil sebelum refactor.
- [ ] Partisipan tidak bisa submit jawaban saat instrumen `CLOSED` (422).

## Skenario uji

Ikuti `automated-test-skill`; semua lewat `make test` (Docker).

1. **Migrasi**: DB berisi 1 sesi DCS + 3 responden → setelah upgrade, `dcs_instrumen` punya 1 baris
   dengan `min_responden` & `catatan` tersalin, 3 responden utuh, `dcs_sesi` lenyap.
2. **Migrasi menolak**: DB berisi 2 sesi DCS yang **sama-sama** punya responden → `upgrade()` raise,
   DB tidak berubah.
3. **Instrumen**: `get` → OPEN; `tutup` → CLOSED + `closed_at` terisi; `tutup` lagi → 409/422;
   `buka-ulang` → OPEN; setelah `ANALYZED`, `buka-ulang` ditolak.
4. **Responden**: bulk create 3 partisipan → 3 baris; create partisipan yang sama lagi → `ConflictError`;
   create saat instrumen `CLOSED` → ditolak; tidak ada lagi batas atas jumlah responden.
5. **Jawaban**: submit saat OPEN → sukses; submit saat CLOSED → ditolak.
6. **Analisis (regresi angka)**: siapkan fixture jawaban tetap, bandingkan output `compute_hasil`
   dengan nilai yang di-hardcode dari implementasi lama (mean, stdev, alpha, risk_flag, k_index).
   **Ini test terpenting di item ini** — ia yang membuktikan refactor tidak mengubah metode statistik.
7. **K-Index**: dengan WCP punya responden ber-submit → `k_index` terisi; tanpa itu → `None`.
8. **Kuesioner saya**: partisipan ter-assign melihat item DCS saat OPEN; tidak melihatnya saat CLOSED.

## Definition of done

- [ ] `make test` hijau
- [ ] `openapi.json` ter-regen & di-commit (dipakai item 002 & 003)
- [ ] `CHANGELOG.md` + `CLAUDE.md` backend diperbarui
- [ ] Item 002 & 003 di `BACKLOG.md` diubah statusnya jadi "Siap dieksekusi"

## Risiko & catatan

- **Migrasi ini destruktif dan tidak bisa dibalik dengan mudah.** Wajib `pg_dump` sebelum jalan di
  deployment mana pun (repo punya direktori `backups/` — ikuti konvensi yang ada di sana).
- **Kalau deployment nyata ternyata punya >1 sesi DCS/WCP berisi data**, migrasi sengaja dibuat
  **abort**, bukan menebak mana yang harus dipertahankan. Pesan error harus menyebutkan `sesi_id` mana
  saja yang punya responden dan menyuruh operator menghapus sesi yang tidak dipakai lebih dulu.
  Sebelum eksekusi, **cek dulu deployment YPII** (`anjab-abk-ypii/`) apakah kondisinya memang satu sesi.
- `jabatan_label` di responden tetap teks bebas (bukan FK ke `jabatan`). Item ini **tidak**
  memperbaikinya — jangan melebar.
- Endpoint lama dihapus tanpa deprecation period. Itu disengaja: tidak ada konsumen pihak ketiga, dan
  MCP + web app di-update di item 002/003 dalam rilis yang sama.
