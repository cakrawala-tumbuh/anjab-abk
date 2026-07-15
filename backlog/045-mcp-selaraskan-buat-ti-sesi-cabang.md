# Backlog 045 — MCP: selaraskan `buat_ti_sesi` dengan `cabang` (backlog 037)

> **Repo:** `anjab-abk-mcp`
> **Status:** Siap dieksekusi (blocked by 037 — SUDAH SELESAI, backend v0.35.0)
> **Blocked by:** 037 (selesai)
> **Skill yang dipakai:** `mcp-development-skill`, `docstring-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Backlog 037 (`anjab-abk-backend`, selesai 2026-07-15, v0.35.0) mengganti field `TiSesiCreate.periode`
(string `YYYY-MM`) dengan `cabang` (enum `"Bandung"|"Semarang"`) dan menghapus total
`min_responden`/`max_responden` dari `TiSesi`. `TiSesiCreate` memakai `model_config =
ConfigDict(extra="forbid")`, jadi tool MCP `buat_ti_sesi` yang masih mengirim `periode` akan
menerima **422** dari backend sejak backend v0.35.0 dirilis. Item ini menyelaraskan tool MCP.

## Keputusan yang sudah dikunci

- `cabang` adalah enum 2 nilai hardcoded `"Bandung"`/`"Semarang"` — sama seperti keputusan di 037,
  bukan lookup ke master data.
- `unit` **tetap dibiarkan** sebagai parameter opsional tool `buat_ti_sesi` — item ini TIDAK
  membahasnya (lihat catatan Risiko: `unit` sudah dihapus dari `TiSesiCreate` backend sejak
  revisi `[2026-06-25]`, jauh sebelum 037; bila param `unit` benar-benar dipakai user, tool akan
  422 karena `extra="forbid"` — tapi ini bug PRA-EXISTING di luar cakupan 037, catat saja, jangan
  diperbaiki tanpa keputusan terpisah kecuali sudah dikonfirmasi memang tidak pernah dipakai).
- Docstring `ti_tambah_responden_banyak` yang menyebut alasan skip `kapasitas_penuh` **harus**
  dikoreksi — TI tidak lagi bisa menghasilkan alasan itu (cap dicabut total di 037); OPM masih bisa.

## Kondisi sekarang (verified — path:baris, dicek 2026-07-15 ✓; baca ulang sebelum edit)

| Lokasi | Baris ✓ | Isi |
|---|---|---|
| `src/anjab_abk_mcp/server.py` `buat_ti_sesi` | `427-434` ✓ | signature: `jabatan_id, periode, unit=None, koordinator_id=None, catatan=None` |
| `src/anjab_abk_mcp/server.py` `buat_ti_sesi` docstring | `435-454` ✓ | Args menyebut `periode: Periode kajian format YYYY-MM`; tidak menyebut `cabang` |
| `src/anjab_abk_mcp/server.py` `buat_ti_sesi` body | `455-461` ✓ | `body = {"jabatan_id": jabatan_id, "periode": periode}` + `unit`/`koordinator_id`/`catatan` opsional |
| `src/anjab_abk_mcp/server.py` `ti_tambah_responden_banyak` docstring | `530-532` ✓ | `"Alasan skip: sudah_terdaftar, duplikat_input, bukan_anggota_sme_panel, atau kapasitas_penuh."` — **stale**, TI tidak lagi bisa `kapasitas_penuh` |
| `tests/test_server.py` | — | cari test yang memanggil `buat_ti_sesi` dengan `periode=...` (grep sebelum edit; baris bisa banyak) |

### Fakta pendukung

- Backend `TiSesiCreate` (setelah 037): `jabatan_id` (wajib), `cabang: Literal["Bandung","Semarang"]`
  (wajib), `koordinator_id` (opsional), `catatan` (opsional) — **tidak ada** `unit`, `periode`,
  `min_responden`, `max_responden`. `extra="forbid"` → payload dengan field asing 422.
- `openapi.json` backend (v0.35.0) sudah mencerminkan skema baru — bisa dipakai sebagai referensi
  kontrak (`components.schemas.TiSesiCreate`).

## Langkah eksekusi

### Langkah 1 — `buat_ti_sesi`: `periode` → `cabang`

- Ganti parameter `periode: str` → `cabang: Literal["Bandung", "Semarang"]` (import `Literal` dari
  `typing` bila belum ada di `server.py`).
- Docstring Args: ganti baris `periode: Periode kajian format YYYY-MM, mis. 2026-06.` menjadi
  penjelasan `cabang` (nilai valid, contoh `"Bandung"`).
- `body: dict = {"jabatan_id": jabatan_id, "periode": periode}` → `{"jabatan_id": jabatan_id,
  "cabang": cabang}`.
- **Jangan** hapus parameter `unit` di langkah ini (lihat Risiko) — biarkan seperti sekarang kecuali
  ada temuan baru saat mengeksekusi bahwa `unit` sudah memicu 422 (dalam hal itu, hapus juga
  parameter `unit` dan sisipkan catatan di CHANGELOG bahwa itu debt pra-existing yang ikut
  dibereskan).

### Langkah 2 — `ti_tambah_responden_banyak`: docstring `kapasitas_penuh`

- Baris `Alasan skip: sudah_terdaftar, duplikat_input, bukan_anggota_sme_panel, atau
  kapasitas_penuh.` → hapus `kapasitas_penuh` dari daftar (khusus untuk tool TI ini). Tambahkan
  catatan singkat: cap responden TI sudah dihapus (backlog 037) — SELURUH anggota panel selalu
  diproses tanpa batas atas.

### Langkah 3 — Test

- `tests/test_server.py`: cari pemanggilan `buat_ti_sesi(..., periode=...)` → ganti ke
  `cabang="Bandung"` (atau nilai lain yang relevan ke skenario test). Tambah 1 test negative-path:
  `cabang` di luar `{"Bandung","Semarang"}` diteruskan mentah ke backend → backend menolak 422 →
  tool melempar `ToolError` (pola error existing, ikuti `_raise_tool_error`).
- Jalankan `make test` (lint + unit di Docker) — harus hijau.

### Langkah 4 — Dokumentasi

- `CHANGELOG.md` (`anjab-abk-mcp`): catat breaking change parameter `buat_ti_sesi` (`periode` →
  `cabang`) mengikuti rilis backend v0.35.0. Bump versi (minor, pra-1.0 bila ada; ikuti konvensi
  repo `mcp`).
- `CLAUDE.md` (`anjab-abk-mcp`): tidak wajib entri baru kecuali ditemukan pola baru yang layak
  didokumentasikan (mis. bila ternyata `unit` juga harus dihapus).

## Kriteria penerimaan

- [ ] `buat_ti_sesi` tidak lagi mengirim `periode` ke backend; mengirim `cabang`.
- [ ] Memanggil `buat_ti_sesi(jabatan_id=..., cabang="Bandung")` sukses (201, terverifikasi via test
      in-memory FastMCP terhadap backend test/mock).
- [ ] `cabang` invalid diteruskan ke backend → 422 → tool melempar error yang jelas (bukan crash).
- [ ] Docstring `ti_tambah_responden_banyak` tidak lagi menyebut `kapasitas_penuh` untuk TI.
- [ ] `make test` hijau (lint + unit) di `anjab-abk-mcp`.

## Skenario uji

- `tests/test_server.py`: pemanggilan `buat_ti_sesi` dengan `cabang` valid → sukses; `cabang`
  invalid → error terlempar dengan pesan dari backend (bukan ditelan).

## Definition of done

- [ ] `make test` hijau di `anjab-abk-mcp`.
- [ ] `CHANGELOG.md` diperbarui (breaking change + bump versi).
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`.

## Risiko & catatan

- **Parameter `unit` di `buat_ti_sesi` sudah basi sejak revisi backend `[2026-06-25]`** (field
  `unit` dihapus dari `TiSesiCreate` jauh sebelum 037) — kemungkinan besar sudah memicu 422 setiap
  kali dipakai, TAPI ini adalah utang pra-existing yang TIDAK lahir dari 037. Item ini sengaja
  membatasi diri ke perubahan `periode`→`cabang`; bila agen pelaksana menemukan `unit` memang
  rusak saat menjalankan test, perbaiki sekalian (hapus parameter) dan catat di CHANGELOG sebagai
  temuan tambahan — jangan biarkan lolos tanpa catatan.
- Breaking change ini hanya berdampak ke pengguna MCP yang memanggil `buat_ti_sesi` langsung
  (klien Claude); web-app punya jalurnya sendiri (item 038, terpisah, tidak memakai MCP).
