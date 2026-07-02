# Rencana Implementasi: Instrumen OPM (Rating Tugas — Importance/Frequency/Criticality)

> **Catatan eksekusi**: rencana ini ditulis agar bisa dieksekusi oleh Sonnet. Langkah pertama eksekusi: salin rencana ini ke `anjab-abk/rencana-opm.md` (workspace induk) sebagai dokumen kerja. Saat eksekusi, patuhi skill `backend-skill`, `frontend-development-skill`, `automated-test-skill`, dan gunakan `git-workflow-skill` bila user meminta commit. **Jangan commit tanpa instruksi eksplisit user.**

## 1. Konteks

Sheet `03_Rating_OPM` pada paket instrumen YPII mendefinisikan Kuesioner Rating Tugas — Skala OPM 3 dimensi: responden (anggota SME panel sebuah jabatan) menilai **setiap task** hasil Task Inventory pada 3 dimensi skala 1–5:

- **Importance** (seberapa penting): 1 Tidak penting … 5 Sangat penting
- **Frequency** (seberapa sering): 1 Insidental … 5 Sangat sering/Harian
- **Criticality** (dampak jika gagal): 1 Dampak minimal … 5 Dampak kritis
- **Catatan** opsional per task.

Flag turunan (formula Excel, dipindah ke analisis backend):
- `Selection_Essential` = YA jika `Importance >= 4 OR Criticality >= 4`
- `Workload_Essential` = YA jika `(Importance >= 3 AND Frequency >= 3) OR Criticality >= 4`

Aturan bisnis dari user:
1. **Hanya satu sesi OPM per jabatan** (absolut), dan jabatan itu **wajib punya SME panel**.
2. Task yang diukur = **task yang lolos Tahap 2 TI** (frozen set `ti_sesi_task_terpilih` = unanimous ∪ coordinator-approved). TI harus selesai Tahap 2 dulu (`task_frozen=True`, status `TAHAP3|CLOSED|ANALYZED`).

Keputusan desain (default terpilih karena user AFK saat ditanya — konfirmasi tercatat):
- Admin memilih **`ti_sesi_id` sumber secara eksplisit** saat membuat sesi; task **di-snapshot** ke tabel anak `opm_sesi_task` saat create (sesi OPM tidak lagi bergantung pada TI setelah dibuat).
- **Responden dibuat otomatis** dari seluruh anggota SME panel saat sesi dibuat; tambah manual tetap bisa tapi **wajib anggota panel**; hapus hanya bila belum submit.
- Agregasi hasil: **mean per dimensi lintas responden + flag dari mean**, plus **proporsi rater** yang menandai essential per formula individual sebagai info tambahan.
- Status flow sesi sama dengan WCP/DCS: `DRAFT → OPEN → CLOSED → ANALYZED`. Isi hanya saat `OPEN`; analisis saat `CLOSED` (auto-transisi ke `ANALYZED`); hasil hanya saat `ANALYZED`.
- **Tidak ada seed / master data OPM** (item berasal dari snapshot TI). `seed_db.py` tidak diubah; tidak ada halaman master-data OPM.

Konfirmasi dari eksplorasi: tidak ada apa pun bernama "OPM" di backend, frontend, maupun `openapi.json` — ini penambahan greenfield yang meniru pola WCP/DCS + tautan ke TI.

---

## 2. Backend — `anjab-abk-backend`

Pola yang wajib ditiru persis (baca file-nya sebelum menulis):
- `src/anjab_abk_backend/api/v1/wcp_sesi.py` — template router (response_model, summary, operation_id, responses envelope, `_WRITE_GUARDS`, blok Idempotency-Key).
- `src/anjab_abk_backend/wcp/services/{sesi,sesi_sql,responden,responden_sql,jawaban,jawaban_sql,analisis}.py` — template service (Protocol + InMemory + `SEARCHABLE_FIELDS` + `_VALID_TRANSITIONS`; Sql impl).
- `src/anjab_abk_backend/anjab/services/sme_panel_sql.py` — pola unique per jabatan: pre-check `ConflictError` + `_flush_checked` (backstop IntegrityError).
- `src/anjab_abk_backend/taskinv/services/sesi_sql.py` — `task_frozen`, `get_task_terpilih`.

### 2.1 Model ORM — edit `src/anjab_abk_backend/models.py` (semua model di satu file, tambah blok OPM)

```
OpmSesiModel        (tabel opm_sesi)
  id            String(40) PK                          # prefix "opses_"
  jabatan_id    String(40) NOT NULL, unique=True, index  # ← 1 sesi per jabatan
  ti_sesi_id    String(40) NOT NULL                    # sumber snapshot (jejak audit)
  periode       String(7)  NOT NULL                    # YYYY-MM (metadata, bukan kunci unik)
  status        String(20) NOT NULL default "DRAFT"
  min_responden Integer NOT NULL default 3
  max_responden Integer NOT NULL default 10
  catatan       Text nullable
  created_at    _ts(index=True)
  task_links    relationship → OpmSesiTaskModel (cascade="all, delete-orphan", lazy="selectin")

OpmSesiTaskModel    (tabel opm_sesi_task) — snapshot task dari TI
  __table_args__ = (UniqueConstraint("sesi_id", "task_kode"),)
  id            Integer PK autoincrement
  sesi_id       ForeignKey("opm_sesi.id", ondelete="CASCADE"), index
  task_kode     String(20) NOT NULL
  uraian_tugas  Text NOT NULL
  tugas_pokok   String(300) NOT NULL
  detil_tugas   String(300) nullable
  urutan        Integer NOT NULL default 1

OpmRespondenModel   (tabel opm_responden) — salin WcpRespondenModel
  id            String(40) PK                          # prefix "oprs_"
  sesi_id       String(40) NOT NULL, index
  nama          String(200) nullable
  jabatan_label String(200) NOT NULL
  partisipan_id String(40) nullable, index
  sudah_submit  Boolean NOT NULL default False
  submitted_at  DateTime(timezone=True) nullable
  created_at    _ts(index=True)

OpmJawabanModel     (tabel opm_jawaban)
  __table_args__ = (UniqueConstraint("responden_id", "task_kode"),)
  id            String(40) PK                          # prefix "opjw_"
  responden_id  String(40) NOT NULL, index
  task_kode     String(20) NOT NULL
  importance    Integer NOT NULL   # 1–5, validasi di Pydantic
  frequency     Integer NOT NULL
  criticality   Integer NOT NULL
  catatan       Text nullable
```

### 2.2 Package baru `src/anjab_abk_backend/opm/`

```
opm/__init__.py
opm/schemas/{__init__,sesi,responden,jawaban,kuesioner,hasil}.py
opm/services/{__init__,sesi,sesi_sql,responden,responden_sql,jawaban,jawaban_sql,analisis}.py
```

Skema Pydantic (gaya `wcp/schemas/*`: `extra="forbid"`, Field ber-description/examples):
- `OpmSesiCreate`: `jabatan_id` (min_length=1), `ti_sesi_id` (min_length=1), `periode` (pattern `^\d{4}-\d{2}$`), `min_responden: int = 3` (ge=1), `max_responden: int = 10` (ge=1), `catatan: str|None` (max 500).
- `OpmSesiUpdate` (hanya DRAFT): `periode`, `min_responden`, `max_responden`, `catatan` — **tanpa** `jabatan_id`/`ti_sesi_id` (ganti sumber = hapus & buat ulang).
- `OpmSesiRead`: semua field + `jabatan_nama: str|None` (join `JabatanModel`, pola `TiSesiRead`) + `jumlah_task: int`.
- `OpmSesiTaskRead`: `task_kode, uraian_tugas, tugas_pokok, detil_tugas, urutan`.
- `OpmJawabanItem`: `task_kode`, `importance/frequency/criticality: int` (ge=1, le=5), `catatan: str|None` (max 500); `OpmJawabanBulkCreate`: `jawaban: list[OpmJawabanItem]` (min_length=1; kelengkapan set divalidasi service terhadap snapshot — jumlah task per sesi dinamis).
- `OpmHasilTaskRead`: `task_kode, uraian_tugas, tugas_pokok, detil_tugas, n, mean_importance, mean_frequency, mean_criticality, sd_importance|None, sd_frequency|None, sd_criticality|None, selection_essential: bool, workload_essential: bool, prop_selection_essential: float, prop_workload_essential: float`.
- `OpmHasilSesiRead`: `sesi_id, jabatan_id, jabatan_nama, periode, n_responden_submit, tasks: list[OpmHasilTaskRead]`.

### 2.3 Logika service kunci

**`SqlOpmSesiService.create(data)`** — satu transaksi (import model lintas domain langsung dari `...models`, pola `taskinv/services/sesi_sql.py::_jabatan_map`):
1. Jabatan ada (`JabatanModel`) → tidak → `ValidationAppError`.
2. `min_responden <= max_responden` → `ValidationAppError`.
3. `SMEPanelModel` untuk jabatan itu ada DAN punya anggota → tidak → `ValidationAppError("Jabatan ini belum memiliki SME panel / panel belum punya anggota.")`.
4. Pre-check sesi OPM untuk jabatan sudah ada → `ConflictError`; unique constraint sebagai backstop via `_flush_checked` (salin helper `sme_panel_sql.py`).
5. `TiSesiModel` by `ti_sesi_id` ada; `ti.jabatan_id == data.jabatan_id`; `ti.task_frozen == True`; `ti.task_terpilih` tidak kosong — pelanggaran mana pun → `ValidationAppError` dengan pesan spesifik.
6. **Snapshot**: tiap kode di `ti.task_terpilih` → query `TiUraianTugasModel` (kode unik) + nama `TiTugasPokokModel`/`TiDetilTugasModel` → baris `OpmSesiTaskModel` (urutan dari `TiUraianTugasModel.urutan`).
7. **Auto-responden**: tiap `partisipan_id` anggota panel → `OpmRespondenModel(nama=par.nama, jabatan_label=<nama jabatan>, partisipan_id=...)`. Bila anggota panel > `max_responden` → `ValidationAppError`.

Method tambahan Protocol sesi: `list_task(sesi_id)`, `get_task_kodes(sesi_id) -> set[str]`.

**`SqlOpmRespondenService.create`** — beda dari WCP:
- Boleh saat sesi `DRAFT` atau `OPEN` (cek di router).
- `partisipan_id` **wajib**.
- Partisipan harus anggota SME panel jabatan sesi → bukan → `ValidationAppError("Partisipan bukan anggota SME panel jabatan ini.")` (service query panel sendiri).
- Duplikat `(sesi_id, partisipan_id)` → `ConflictError` (scope **per sesi**, bukan global — partisipan bisa panelis 2 jabatan).
- Cek `max_responden` seperti WCP.

**`opm/services/analisis.py`** — fungsi murni tanpa DB:
```python
def compute_hasil_sesi(
    sesi: OpmSesiRead,
    tasks: list[OpmSesiTaskRead],
    responden_raw: list[tuple[str, dict[str, tuple[int, int, int]]]],  # (responden_id, {task_kode: (imp, freq, crit)})
) -> OpmHasilSesiRead
```
Per task: `mean_*` (2 desimal), `sd_*` = `statistics.stdev` bila n≥2 else `None`;
`selection_essential = mean_imp >= 4 or mean_crit >= 4`;
`workload_essential = (mean_imp >= 3 and mean_freq >= 3) or mean_crit >= 4`;
`prop_selection_essential` = proporsi responden dengan `(imp>=4 or crit>=4)`; `prop_workload_essential` analog `((imp>=3 and freq>=3) or crit>=4)` (4 desimal).

**Jawaban submit** (`SqlOpmJawabanService.bulk_create(responden_id, payload, valid_task_kodes)`): set `{item.task_kode}` harus == `valid_task_kodes` persis (kurang/lebih/duplikat → `ValidationAppError` dengan daftar kode bermasalah). `get_raw_by_responden` → `dict[str, tuple[int,int,int]]`; `list_by_responden` untuk read (termasuk catatan).

### 2.4 Router — file baru di `src/anjab_abk_backend/api/v1/`

Semua endpoint: `response_model`, `summary`, `operation_id`, `responses` envelope error; POST create sesi pakai `Idempotency-Key` (salin blok `wcp_sesi.py`). Guard `_WRITE_GUARDS` seperti WCP (tanpa `require_admin` — konsisten dengan WCP sesi/responden).

| File | Method & Path (prefix `/api/v1`) | operation_id | Guard | Syarat |
|---|---|---|---|---|
| `opm_sesi.py` | GET `/opm/sesi` | `opm_sesi_list` | — | — |
| | POST `/opm/sesi` | `opm_sesi_create` | WRITE + Idempotency | 409 jabatan sudah punya sesi; 422 panel/TI tidak valid |
| | POST `/opm/sesi/search` | `opm_sesi_search` | — | domain ala Odoo |
| | GET `/opm/sesi/{sesi_id}` | `opm_sesi_get` | — | — |
| | PATCH `/opm/sesi/{sesi_id}` | `opm_sesi_update` | WRITE | DRAFT |
| | DELETE `/opm/sesi/{sesi_id}` | `opm_sesi_delete` | WRITE | DRAFT |
| | POST `/opm/sesi/{sesi_id}/buka` | `opm_sesi_buka` | WRITE | DRAFT→OPEN |
| | POST `/opm/sesi/{sesi_id}/tutup` | `opm_sesi_tutup` | WRITE | OPEN→CLOSED |
| | GET `/opm/sesi/{sesi_id}/task` | `opm_sesi_task_list` | — | snapshot task |
| `opm_responden.py` | GET `/opm/sesi/{sesi_id}/responden` | `opm_responden_list` | — | — |
| | POST `/opm/sesi/{sesi_id}/responden` | `opm_responden_create` | WRITE | DRAFT/OPEN; 422 bukan anggota panel; 409 duplikat |
| | GET `/opm/sesi/responden/{responden_id}` | `opm_responden_get` | — | — |
| | DELETE `/opm/sesi/responden/{responden_id}` | `opm_responden_delete` | WRITE | belum submit |
| | POST `/opm/sesi/responden/{responden_id}/jawaban` | `opm_jawaban_submit` | WRITE | sesi **OPEN** + belum submit; 422 set task tidak lengkap |
| | GET `/opm/sesi/responden/{responden_id}/jawaban` | `opm_jawaban_list` | — | — |
| `opm_hasil.py` | POST `/opm/sesi/{sesi_id}/analisis` | `opm_analisis_run` | WRITE | CLOSED; 422 submit < min_responden; auto→ANALYZED |
| | GET `/opm/sesi/{sesi_id}/hasil` | `opm_hasil_sesi_get` | — | ANALYZED |
| `opm_kuesioner.py` | GET `/opm/kuesioner/saya` | `opm_kuesioner_saya` | principal | hanya sesi OPEN; salin `wcp_kuesioner.py` 1:1 |

Catatan `opm_jawaban_submit`: router fetch sesi via responden → tolak bila `sesi.status != "OPEN"`.

### 2.5 Wiring

- `dependencies.py`: `get_opm_sesi_service`, `get_opm_responden_service`, `get_opm_jawaban_service` (pola `get_wcp_*`).
- `api/router.py`: mount urutan seperti WCP — `opm_kuesioner` (prefix `/opm`, tag `opm.kuesioner`), lalu `opm_sesi` (`/opm/sesi`, `opm.sesi`), `opm_responden` (`/opm/sesi`, `opm.responden`), `opm_hasil` (`/opm/sesi`, `opm.hasil`).
- `openapi.py`: tambah metadata tag `opm.*` mengikuti deklarasi tag `wcp.*`.

### 2.6 Migrasi (Alembic inkremental gaya Odoo)

1. Selesaikan `models.py`.
2. `make migration m="tambah tabel opm sesi task responden jawaban"` → SATU berkas revisi baru di `migrations/versions/` (4 tabel + unique constraints). Review hasil autogenerate.
3. Jangan edit revisi lama. `tests/test_migrations.py` (schema-guard, single-head) memverifikasi otomatis di `make test`.

### 2.7 Unit test backend

Helper bersama `_setup_jabatan_panel_ti(client)` (tiru pola `tests/test_taskinv.py` + `tests/test_sme_panel.py`): buat jabatan → 2 partisipan → SME panel + anggota → jalankan TI sampai frozen (create sesi TI → responden → `mulai-tahap1` → submit seleksi → `mulai-tahap2` → submit tahap2 → `mulai-tahap3`).

- `tests/test_opm_sesi.py`: create ok (snapshot = task_terpilih TI; responden = anggota panel); 401 tanpa auth; 422 tanpa SME panel; 422 panel tanpa anggota; 409 jabatan sudah punya sesi; 422 TI tidak ada / jabatan beda / belum frozen; idempotency replay; update/delete hanya DRAFT; transisi lengkap + invalid; task list; search domain.
- `tests/test_opm_responden.py`: auto-responden terisi; tambah manual anggota panel ok; 422 bukan anggota; 409 duplikat; 422 melebihi max; hapus belum submit 204; 422 hapus sudah submit; submit jawaban ok + tandai submit; 422 submit saat sesi bukan OPEN; 422 submit dua kali; 422 task kurang/asing; 422 skor di luar 1–5; kuesioner-saya hanya OPEN (fake verifier partisipan).
- `tests/test_opm_analisis.py`: 422 analisis butuh CLOSED; 422 kurang min_responden; analisis ok → ANALYZED; mean/SD/flag benar (2 responden deterministik); 422 hasil sebelum ANALYZED; hasil ok setelah ANALYZED; test fungsi murni `compute_hasil_sesi` (boundary: mean_imp tepat 4.0 → True; mean_crit 3.99 → False).

### 2.8 Export OpenAPI

Tidak ada target make khusus — jalankan `python scripts/export_openapi.py openapi.json` dari root backend (atau via `make shell`). Hasil menimpa `openapi.json` di root backend; pastikan memuat path `/api/v1/opm/...`.

---

## 3. Frontend — `anjab-abk-web-app`

### 3.1 Regenerasi tipe (fase pertama)

1. Salin `anjab-abk-backend/openapi.json` → `anjab-abk-web-app/openapi/openapi.json`.
2. `npm run gen:api` → `src/lib/api/schema.ts`.
3. **PENTING**: pertahankan/append ulang blok convenience re-export di akhir `schema.ts`; tambahkan tipe OPM (`OpmSesiRead`, `OpmSesiTaskRead`, `OpmRespondenRead`, `OpmJawabanRead`, `OpmKuesionerItemRead`, `OpmHasilSesiRead`) mengikuti pola tipe WCP.

### 3.2 Route tree baru `src/app/(auth)/opm/` (salin dari `wcp/`, sesuaikan)

```
opm/page.tsx                        # list sesi (isAdmin guard); kolom: Keterangan (catatan ?? periode), Jabatan (jabatan_nama), Status, jumlah task
opm/loading.tsx, error.tsx          # wajib per route
opm/buat/page.tsx                   # Server Component: fetch jabatan + sme-panel + ti-sesi → form
opm/buat/opm-sesi-form.tsx          # Client, react-hook-form + zod (export `schema` utk unit test)
opm/buat/loading.tsx, error.tsx
opm/[sesi_id]/page.tsx              # detail: status, statistik, tabel task snapshot, TransisiSesi, TambahResponden, daftar responden + HapusResponden, link Hasil saat ANALYZED
opm/[sesi_id]/transisi-sesi.tsx     # salin wcp: Buka/Tutup/Jalankan Analisis → /api/v1/opm/sesi/...
opm/[sesi_id]/tambah-responden.tsx  # BEDA: select partisipan dibatasi anggota SME panel jabatan sesi (page fetch GET /api/v1/sme-panel + filter jabatan_id, map partisipan_ids → PartisipanRead); partisipan_id wajib
opm/[sesi_id]/hapus-responden.tsx   # salin apa adanya
opm/[sesi_id]/hasil/page.tsx        # tabel hasil per task: mean I/F/C, SD, badge Selection/Workload Essential, proporsi; hanya saat ANALYZED
opm/[sesi_id]/loading.tsx, error.tsx (+ hasil/)
opm/isi/[responden_id]/page.tsx     # partisipan (isPartisipan guard): fetch responden + sesi + task + jawaban existing
opm/isi/[responden_id]/opm-form.tsx
```

Pola data: Server Component fetch via `withServerAuth(accessToken).GET(...)`; mutasi di client component via typed client lalu `router.refresh()`/`router.push()`. **Tanpa TanStack hooks** (tidak dipakai di repo ini). Field relasi tampil sebagai label manusiawi (nama jabatan/partisipan), bukan id.

**`opm-sesi-form.tsx`** — field:
- Select `jabatan_id`: opsi = jabatan yang **punya SME panel** (server page: `GET /api/v1/jabatan?limit=100` + `GET /api/v1/sme-panel?limit=100`, join di klien; 422 server tetap ditampilkan via `serverError` sebagai backstop).
- Select `ti_sesi_id`: `GET /api/v1/task-inventory/sesi?limit=100` di server page → filter klien by `jabatan_id` terpilih DAN `jumlah_task_terpilih > 0` (null = belum frozen; field ada di `TiSesiRead`). Label `periode — N task`. Kosong → "Belum ada sesi TI yang dibekukan untuk jabatan ini."
- `periode` (regex `^\d{4}-\d{2}$`), `min_responden` default 3, `max_responden` default 10 (refine max ≥ min), `catatan` opsional.
- Submit → `POST /api/v1/opm/sesi` → `router.push(/opm/${id})`. Error handling `toApiError` + `x-request-id` (salin `wcp-sesi-form.tsx`).

**`opm-form.tsx`** (halaman isi) — per task satu card: uraian_tugas (judul), tugas_pokok/detil_tugas (subteks), 3 radio group 1–5 berlabel skala (Kepentingan/Frekuensi/Kritikalitas sesuai anchor sheet), textarea Catatan opsional. Progress "X / N tugas lengkap" (lengkap = 3 dimensi terisi); tombol "Kirim Jawaban" disabled sampai lengkap; POST bulk; sukses → "Jawaban berhasil dikirim!". Mode read-only bila `sudah_submit` (tiru `wcp-form.tsx`).

### 3.3 Registrasi menu (3 tempat)

- `src/app/(auth)/layout.tsx`: `<Link href="/opm">OPM</Link>` di blok admin (setelah WCP).
- `src/app/(auth)/dashboard/page.tsx`: card admin "OPM — Rating Tugas".
- `src/app/(auth)/kuesioner/page.tsx`: tambah `GET /api/v1/opm/kuesioner/saya` ke `Promise.all`, hitung total/belum, section kartu OPM (link `/opm/isi/${id}`) — salin blok WCP.
- Tidak ada halaman master-data baru.

### 3.4 Unit test frontend

- `src/test/opm-sesi-form-schema.test.ts` (pola `sesi-form-schema.test.ts`): periode valid/invalid, max ≥ min, jabatan_id/ti_sesi_id wajib.
- Opsional: extract util kelengkapan jawaban opm-form ke fungsi murni + test.
- Gate: `make test` (lint + typecheck + vitest di Docker) dan `npm run build`.

---

## 4. E2E Playwright — `e2e/opm.spec.ts`

**Strategi seeding**: seluruh precondition lewat **UI, idempoten** (konsisten `tahap1.spec.ts` yang membuktikan alur TI via UI feasible; harness e2e tidak punya utilitas token Bearer admin, jadi REST seeding malah menambah kompleksitas).

**Refactor kecil**: pindahkan builder `buatJenjang/buatSekolah/buatJabatan/buatPartisipan` dari `kuesioner.spec.ts` ke modul baru `e2e/builders.ts` (export); `kuesioner.spec.ts` mengimpornya; `opm.spec.ts` reuse.

**Konstanta**: `PERIODE_TI = "2031-05"` (tidak bentrok `2031-03` milik tahap1.spec), `PERIODE_OPM = "2031-06"`. Jabatan: pakai jabatan ber-catalog hasil seed (pola `bukaAtauBuatSesi` di tahap1.spec) — catat nama jabatan dari teks option untuk SME panel & form OPM. Karena sesi OPM unik per jabatan absolut, **idempotensi run-ulang wajib**: tiap langkah cek "sudah ada → pakai ulang".

`test.describe.serial("OPM — Rating Tugas")`:
1. **admin: siapkan prasyarat** (`test.setTimeout(240_000)`) — login `admin-e2e/AdminE2e123!`; builders master data + `buatPartisipan` (idempoten); **SME panel**: `/master-data/sme-panel` — bila belum ada untuk jabatan target → buat via `/master-data/sme-panel/tambah` + tambah anggota via `anggota-form` di detail panel (baca label form aktual `master-data/sme-panel/[id]/anggota-form.tsx` saat implementasi); **TI frozen**: buat/reuse sesi TI `PERIODE_TI` → 1 responden → "Mulai Tahap 1" → isi seleksi (langkah tahap1.spec) → "Mulai Tahap 2" → (unanimous dgn 1 responden; setujui yang tampil bila ada) → "Mulai Tahap 3 — Bekukan Task Relevan". Transisi dibungkus `if (button visible)` agar idempoten.
2. **admin: buat sesi OPM & buka** — `/opm`: bila sudah ada → masuk; else `/opm/buat`: pilih jabatan, TI sesi (`PERIODE_TI`), periode `PERIODE_OPM`, min=1, max=10 → submit → `waitForURL(/\/opm\/opses_/)`. Verifikasi tabel task ≥1 baris & responden otomatis memuat nama partisipan. "Buka Sesi" bila tampak.
3. **partisipan: isi kuesioner** — login `part-e2e/PartE2e123!` → `/kuesioner` → section OPM; bila "Sudah diisi" → lanjut (idempoten); "Isi Sekarang" → tiap task set importance=4, frequency=3, criticality=5 → progress penuh → "Kirim Jawaban" → "Jawaban berhasil dikirim!".
4. **partisipan: verifikasi Sudah diisi + read-only** (pola kuesioner.spec test 4–5).
5. **admin: tutup + analisis + hasil** — "Tutup Sesi" bila tampak; "Jalankan Analisis" bila tampak (min=1 valid); `/opm/{sesi_id}/hasil` → mean 4/3/5 + badge Selection & Workload Essential (crit 5 → keduanya YA). Idempoten: bila sudah ANALYZED langsung verifikasi.

Jalankan: `make e2e` (stack `compose.e2e.yml`: web :9100, backend :9200, Authentik :9300).

---

## 5. Urutan Eksekusi & Verifikasi

| Fase | Pekerjaan | Verifikasi |
|---|---|---|
| 0 | Salin rencana ini ke `anjab-abk/rencana-opm.md` | — |
| B1 | `models.py` (4 model) → `make migration m="tambah tabel opm sesi task responden jawaban"` → review revisi | `make test` (schema-guard hijau) |
| B2 | Package `opm/` (schemas + services + analisis) | `make lint` |
| B3 | Router `api/v1/opm_*.py` + `dependencies.py` + `api/router.py` + `openapi.py` | `make test` |
| B4 | 3 file test backend | `make test` hijau penuh |
| B5 | `python scripts/export_openapi.py openapi.json` | `openapi.json` memuat `/api/v1/opm/...` |
| F1 | Salin openapi.json → `openapi/`; `npm run gen:api`; restore blok re-export + tipe OPM | typecheck lolos |
| F2 | Route tree `(auth)/opm/**` + registrasi menu | `make test` + `npm run build` |
| F3 | `src/test/opm-sesi-form-schema.test.ts` | `make test` |
| F4 | `e2e/builders.ts` (refactor) + `e2e/opm.spec.ts` | `make e2e` — jalankan **2×** untuk membuktikan idempoten |
| F5 | Update `docs-usage/` (kewajiban CLAUDE.md web-app saat UI berubah) | — |

## 6. Di Luar Scope (eksplisit)

- **MCP tools** (`anjab-abk-mcp`: `buat_opm_sesi`, `opm_*`) — follow-up terpisah setelah backend stabil.
- Rilis/tag semver, GitHub Release, image GHCR, update submodule repo induk.
- Perubahan instrumen lain (WCP/DCS/TI/TS) — nol perubahan.
- Ekspor hasil OPM ke PDF/Excel; laporan lintas instrumen.
- Seed data OPM (tidak ada by design).
- **Commit** — hanya bila user meminta eksplisit (aturan global).
