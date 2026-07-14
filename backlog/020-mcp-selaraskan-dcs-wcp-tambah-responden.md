# Backlog 020 — MCP: selaraskan `dcs_tambah_responden`/`wcp_tambah_responden` dengan `BulkAssignResult`

> **Repo:** `anjab-abk-mcp`
> **Status:** Selesai (dieksekusi 2026-07-14, sesi yang sama dengan 017/018/019)
> **Blocked by:** 018
> **Skill yang dipakai:** `mcp-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Item **018** mengubah response `POST /api/v1/dcs/responden` & `POST /api/v1/wcp/responden` dari
`array` menjadi objek `BulkAssignResult` (`{created, skipped}`). Ditemukan saat mengeksekusi 018:
`dcs_tambah_responden` dan `wcp_tambah_responden` di `anjab-abk-mcp` masih bertipe kembali `-> list`
dan docstring-nya masih menjanjikan "daftar responden yang baru dibuat" — kontraknya jadi stale/salah
begitu 018 dirilis, walau secara teknis tool tetap meneruskan body response backend apa adanya (tidak
crash, hanya deskripsi & tipe yang salah).

Pola acuan sudah ada dan benar: `ti_tambah_responden_banyak` (`server.py:512`) dan
`opm_tambah_responden_banyak` mengembalikan `dict` dengan docstring yang menjelaskan bentuk
`{"created": [...], "skipped": [{"partisipan_id", "alasan"}]}`.

## Keputusan yang sudah dikunci

1. Tiru persis pola `ti_tambah_responden_banyak` — ubah anotasi tipe kembali ke `dict`, perbarui
   docstring `Returns:` untuk menjelaskan bentuk `{created, skipped}`.
2. Alasan skip DCS/WCP (dari implementasi 018): `duplikat_input`, `sudah_terdaftar`. **Tidak** ada
   `bukan_anggota_sme_panel`/`kapasitas_penuh` (itu khas TI) — jangan disalin dari docstring TI.
3. Tidak ada perubahan pada `client.py`/`backend_post` — tool ini sudah meneruskan body backend apa
   adanya, cukup anotasi & docstring yang perlu benar.

## Kondisi sekarang (verified 2026-07-14)

| Fakta | Bukti |
|---|---|
| `dcs_tambah_responden` bertipe `-> list`, docstring "Daftar responden DCS yang baru dibuat" | ✓ `src/anjab_abk_mcp/server.py:804` |
| `wcp_tambah_responden` idem | ✓ `src/anjab_abk_mcp/server.py:955` |
| Test hanya assert path request, bukan bentuk response | ✓ `tests/test_server.py:141,155,238,248,482,491` |
| Backend (018) mengembalikan `{"created": [...], "skipped": [{"partisipan_id", "alasan"}]}`, 201, alasan `duplikat_input`/`sudah_terdaftar` | ✓ `anjab-abk-backend/src/anjab_abk_backend/dcs/services/responden_sql.py:141,159` (idem WCP) |

## Langkah eksekusi (sudah dijalankan)

1. `server.py:804` — `dcs_tambah_responden(...) -> list` → `-> dict`; docstring `Returns:` diganti
   menjadi bentuk `{"created": [...], "skipped": [{"partisipan_id": ..., "alasan": ...}]}` dengan
   alasan `duplikat_input`/`sudah_terdaftar`.
2. `server.py:955` — idem untuk `wcp_tambah_responden`.
3. `tests/test_server.py` — test `test_dcs_tambah_responden_bulk`/`test_wcp_tambah_responden_bulk`
   tidak perlu diubah strukturnya (masih assert path & body request), ditambahkan assertion ringan
   pada bentuk response mock agar konsisten dengan pola TI/OPM.
4. `make test` dijalankan sampai hijau.
5. `CHANGELOG.md` repo `anjab-abk-mcp` diperbarui.

## Kriteria penerimaan

- [x] `dcs_tambah_responden`/`wcp_tambah_responden` bertipe kembali `dict`.
- [x] Docstring `Returns:` menjelaskan `{created, skipped}` dengan alasan skip yang benar (bukan
      disalin dari TI).
- [x] `make test` hijau.

## Definition of done

- [x] `make test` hijau di `anjab-abk-mcp`
- [x] `CHANGELOG.md` diperbarui
- [x] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- Ditemukan sebagai efek samping eksekusi 018 (agen pelaksana 018 melakukan audit `grep` atas
  `anjab-abk-mcp` sesuai instruksi "satu item = satu repo" dan melaporkan temuan ini, bukan
  langsung mengubah repo MCP).
- Scope sengaja kecil — hanya anotasi tipe & docstring. Tidak ada perubahan perilaku runtime.
