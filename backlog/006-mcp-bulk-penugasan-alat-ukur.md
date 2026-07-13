# Backlog 006 — MCP: expose penugasan massal (bulk) untuk TS, TI, OPM

> **Repo:** `anjab-abk-mcp`
> **Status:** Menunggu (blocked by 005)
> **Blocked by:** [005](005-backend-bulk-penugasan-alat-ukur.md)
> **Skill yang dipakai:** `mcp-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Item [005](005-backend-bulk-penugasan-alat-ukur.md) menambahkan endpoint bulk-assign idempoten
(`POST .../bulk`) untuk TS, TI, OPM di `anjab-abk-backend`, serta auto-populate SME panel saat
sesi TI dibuat. Item ini meng-expose endpoint bulk baru tersebut sebagai MCP tool, **dan**
menambal celah lama: MCP saat ini sama sekali tidak punya tool untuk menambah responden OPM
(hanya ada tool hapus), padahal endpoint single-nya sudah lama ada di backend
(`POST /api/v1/opm/sesi/{sesi_id}/responden`).

Mekanisme manual (single) yang sudah ada — `buat_ts_penugasan`, `ti_tambah_responden` — **tidak
diubah/dihapus**. Tool baru ditambahkan berdampingan.

## Keputusan yang sudah dikunci

1. **Response bulk tool = passthrough mentah dari backend** (`{created: [...], skipped:
   [{partisipan_id, alasan}]}`, lihat item 005 Keputusan #2) — MCP tidak mengubah bentuknya,
   cukup mengembalikan JSON response backend apa adanya.
2. **MCP untuk OPM ditambah dua tool baru**: `opm_tambah_responden` (single — expose endpoint
   backend yang sudah ada tapi belum pernah di-wire) dan `opm_tambah_responden_banyak` (bulk).
3. Semua tool baru mengikuti pola yang sudah konsisten di seluruh `server.py`: `@mcp.tool async
   def ...`, panggil `backend_post` dari `.client`, bungkus
   `try/except BackendError as exc: _raise_tool_error(exc)`. Tidak ada abstraksi/wrapper baru —
   ikuti gaya tool tetangga persis.

## Kondisi sekarang (verified)

Server MCP: satu file `src/anjab_abk_mcp/server.py` (FastMCP), tool dikelompokkan dengan komentar
banner `# DOMAIN: ...`. Client HTTP bersama: `src/anjab_abk_mcp/client.py`
(`backend_post(path, *, ctx=None, body=None, params=None)`, `BackendError`).

| Tool sekarang | Lokasi | Params | Endpoint backend yang dipanggil |
|---|---|---|---|
| `buat_ts_penugasan` (single, tetap ada) | `server.py:2688-2710` | `partisipan_id, aktif=True, catatan=None` | `POST /api/v1/time-study/penugasan` |
| `ti_tambah_responden` (single, tetap ada) | `server.py:469-508` | `sesi_id, partisipan_id=None, nama=None` | `POST /api/v1/task-inventory/sesi/{sesi_id}/responden` |
| `wcp_tambah_responden` (bulk, referensi gaya) | `server.py:922` | `partisipan_ids: list[str]` | `POST /api/v1/wcp/responden` |
| `dcs_tambah_responden` (bulk, referensi gaya) | `server.py:771` | `partisipan_ids: list[str]` | `POST /api/v1/dcs/responden` |
| — (tidak ada tool tambah responden OPM sama sekali) | domain OPM hanya punya `hapus_opm_sesi` (`server.py:~2604-2630`) dan `opm_hapus_responden` (`server.py:~2632-2651`) | — | — |

Docstring domain di kepala `server.py` (baris ~11-17) saat ini masih menyebut
`opm: sesi OPM (delete-only; sisa domain — lihat rencana-opm.md)` — sudah usang begitu item ini
selesai.

Test tool bulk yang sudah ada, jadi template gaya assert: `tests/test_server.py` baris 123-144
(`dcs_tambah_responden`/`wcp_tambah_responden`) — assert path & body lewat
`m.await_args.args[0]` / `m.await_args.kwargs["body"]` pada mock `backend_post`. Test MCP tidak
memerlukan backend hidup (HTTP client di-mock), jadi item ini **tidak** butuh
`anjab-abk-backend` berjalan untuk lulus test — hanya butuh endpoint & path-nya sudah pasti
(dari item 005) agar path yang di-assert benar.

Semua nomor baris di atas WAJIB dicek ulang oleh agen pelaksana sebelum mengedit (baris bisa
bergeser sejak rencana ini ditulis, dan makin bergeser lagi setelah item 005 dieksekusi).

## Langkah eksekusi

### Langkah 1 — `buat_ts_penugasan_banyak`

Taruh persis setelah `buat_ts_penugasan` (`server.py:2688-2710`), sebelum tool berikutnya.

```python
@mcp.tool
async def buat_ts_penugasan_banyak(
    ctx: Context,
    partisipan_ids: list[str],
    aktif: bool = True,
    catatan: str | None = None,
) -> dict:
    """Tugaskan banyak partisipan sekaligus untuk mencatat Time Study (admin, idempoten)."""
    body: dict = {"partisipan_ids": partisipan_ids, "aktif": aktif}
    if catatan is not None:
        body["catatan"] = catatan
    try:
        return await backend_post("/api/v1/time-study/penugasan/bulk", ctx=ctx, body=body)
    except BackendError as exc:
        _raise_tool_error(exc)
```

Docstring lengkap (Google-style, sesuai `docstring-skill`) — jelaskan beda dari
`buat_ts_penugasan` (satu-per-satu) dan bentuk `created`/`skipped` di response.

### Langkah 2 — `ti_tambah_responden_banyak`

Taruh setelah `ti_tambah_responden` (`server.py:469-508`), sebelum tool TI berikutnya
(`ti_mulai_tahap1`).

```python
@mcp.tool
async def ti_tambah_responden_banyak(
    ctx: Context, sesi_id: str, partisipan_ids: list[str]
) -> dict:
    """Tugaskan (assign) banyak partisipan sekaligus sebagai responden Task Inventory (admin, idempoten)."""
    try:
        return await backend_post(
            f"/api/v1/task-inventory/sesi/{sesi_id}/responden/bulk",
            ctx=ctx,
            body={"partisipan_ids": partisipan_ids},
        )
    except BackendError as exc:
        _raise_tool_error(exc)
```

Docstring: jelaskan bahwa berbeda dari `ti_tambah_responden` (boleh anonim tanpa
`partisipan_id`), tool ini HANYA menerima partisipan yang wajib anggota SME panel jabatan sesi
ini — yang bukan anggota akan muncul di `skipped` dengan alasan `bukan_anggota_sme_panel`.

### Langkah 3 — `opm_tambah_responden` (single, baru) + `opm_tambah_responden_banyak`

Taruh di domain OPM setelah `hapus_opm_sesi` (`server.py:~2604-2630`), sebelum
`opm_hapus_responden`.

```python
@mcp.tool
async def opm_tambah_responden(
    ctx: Context,
    sesi_id: str,
    partisipan_id: str,
    jabatan_label: str,
    nama: str | None = None,
) -> dict:
    """Daftarkan satu responden OPM secara manual ke sesi (admin)."""
    body: dict = {"partisipan_id": partisipan_id, "jabatan_label": jabatan_label}
    if nama is not None:
        body["nama"] = nama
    try:
        return await backend_post(f"/api/v1/opm/sesi/{sesi_id}/responden", ctx=ctx, body=body)
    except BackendError as exc:
        _raise_tool_error(exc)


@mcp.tool
async def opm_tambah_responden_banyak(
    ctx: Context, sesi_id: str, partisipan_ids: list[str]
) -> dict:
    """Tugaskan (assign) banyak partisipan sekaligus sebagai responden OPM (admin, idempoten)."""
    try:
        return await backend_post(
            f"/api/v1/opm/sesi/{sesi_id}/responden/bulk",
            ctx=ctx,
            body={"partisipan_ids": partisipan_ids},
        )
    except BackendError as exc:
        _raise_tool_error(exc)
```

Docstring `opm_tambah_responden`: jelaskan bahwa sebagian besar anggota SME panel sudah otomatis
jadi responden saat sesi OPM dibuat — tool ini untuk menambah anggota panel yang bergabung
SETELAH sesi dibuat. Docstring `opm_tambah_responden_banyak`: sama seperti langkah 2, jelaskan
`nama`/`jabatan_label` diresolusi otomatis (tidak seperti single yang mewajibkan
`jabatan_label`).

### Langkah 4 — Update docstring domain OPM

`src/anjab_abk_mcp/server.py` baris ~11-17 (banner ringkasan domain di kepala file): ganti baris
yang menyebut `opm: sesi OPM (delete-only; sisa domain — lihat rencana-opm.md)` menjadi sesuatu
seperti `opm: sesi OPM (create single+bulk, delete responden & sesi)` — sesuaikan dengan gaya
baris lain di banner yang sama.

### Langkah 5 — Test baru

`tests/test_server.py`, mengikuti gaya assert `dcs_tambah_responden`/`wcp_tambah_responden`
(baris 123-144, mock `backend_post`, assert `m.await_args`):

- `test_buat_ts_penugasan_banyak` — assert path `/api/v1/time-study/penugasan/bulk`, body
  `{"partisipan_ids": [...], "aktif": True}`.
- `test_ti_tambah_responden_banyak` — assert path
  `/api/v1/task-inventory/sesi/{sesi_id}/responden/bulk`.
- `test_opm_tambah_responden` (single) — assert path `/api/v1/opm/sesi/{sesi_id}/responden`,
  body memuat `jabatan_label`.
- `test_opm_tambah_responden_banyak` — assert path `/api/v1/opm/sesi/{sesi_id}/responden/bulk`.
- Perluas test daftar-tool-terdaftar (mis. `test_tools_terdaftar` bila ada) agar mencakup
  keempat nama tool baru.

## Kriteria penerimaan

- [ ] `buat_ts_penugasan_banyak`, `ti_tambah_responden_banyak`, `opm_tambah_responden`,
      `opm_tambah_responden_banyak` terdaftar sebagai MCP tool dan memanggil path backend yang
      benar (lihat tabel path di Langkah 1-3).
- [ ] Tool manual (single) yang sudah ada — `buat_ts_penugasan`, `ti_tambah_responden` — tidak
      berubah signature/perilakunya sama sekali.
- [ ] Docstring domain OPM di kepala `server.py` diperbarui, tidak lagi menyebut "delete-only".
- [ ] Semua tool baru mengembalikan response backend (termasuk `created`/`skipped`) apa adanya,
      tanpa transformasi tambahan di layer MCP.

## Skenario uji

Lihat daftar lengkap di Langkah 5. Semua harus lulus via `make test` (lint + unit di dalam
Docker). Test di-mock terhadap `backend_post` — tidak butuh `anjab-abk-backend` hidup untuk
lulus, tapi path yang di-assert HARUS sama persis dengan path endpoint yang dibuat di item 005
(cek ulang path final di `anjab-abk-backend` sebelum menulis assert, jangan hanya menyalin dari
rencana ini).

## Definition of done

- [ ] `make test` hijau di `anjab-abk-mcp`
- [ ] `CHANGELOG.md` diperbarui
- [ ] `CLAUDE.md` (`anjab-abk-mcp`, bila ada) diperbarui bila ada perubahan pola/alur
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Blocked by 005** — jangan mulai sebelum endpoint bulk backend sudah ada & `make test` hijau
  di `anjab-abk-backend`, supaya path/skema yang di-assert di test MCP sudah final dan tidak
  perlu direvisi ulang.
- Verifikasi manual end-to-end (opsional tapi disarankan setelah kedua item selesai, backend
  jalan lokal): panggil `buat_sme_panel` → `tambah_anggota_sme_panel` (2x) → `buat_ti_sesi` untuk
  jabatan yang sama → `ti_daftar_responden` harus langsung menunjukkan 2 responden (auto-assign
  dari item 005) tanpa panggilan tambahan; lalu panggil `ti_tambah_responden_banyak` dengan
  campuran id yang sudah terdaftar + id baru → cek `created`/`skipped` sesuai ekspektasi.
