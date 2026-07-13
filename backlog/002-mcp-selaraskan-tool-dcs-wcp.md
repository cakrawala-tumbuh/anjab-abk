# Backlog 002 — MCP: selaraskan tool DCS & WCP dengan model tanpa sesi

> **Repo:** `anjab-abk-mcp`
> **Status:** Menunggu (blocked by 001)
> **Blocked by:** 001 — butuh `openapi.json` backend hasil item itu.
> **Skill:** `mcp-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Menyesuaikan tool MCP DCS & WCP dengan backend yang sudah tidak punya sesi (item 001). Hasilnya:
**jumlah tool berkurang**, dan tidak ada lagi tool yang meminta `sesi_id` untuk DCS/WCP.

## Keputusan yang sudah dikunci

1. Tool sesi DCS/WCP **dihapus**, bukan di-deprecate. MCP ini stdio/editable dan dipakai internal.
2. Nama tool baru memakai kata **`instrumen`**, bukan `sesi`.
3. `dcs_analisis` & `dcs_hasil` **kehilangan parameter `wcp_sesi_id`** (K-Index sekarang otomatis).
4. `dcs_tambah_responden` & `wcp_tambah_responden` menerima **daftar** `partisipan_ids`.
5. Tool TI, OPM, dan TS **tidak disentuh** (sesi TI/OPM dipertahankan — lihat BACKLOG.md).

## Kondisi sekarang (verified per 2026-07-12)

Seluruh tool ada di satu file: `src/anjab_abk_mcp/server.py` (3.643 baris), didaftarkan dengan
dekorator `@mcp.tool` dan memanggil `backend_get`/`backend_post` + `_raise_tool_error(exc)`.

Tool DCS/WCP yang menyentuh sesi (semua **wajib diverifikasi ulang barisnya** sebelum diedit):

| Tool | Baris | Nasib |
|---|---|---|
| `daftar_dcs_sesi` | `server.py:641` ✓ | **hapus** |
| `buat_dcs_sesi` | `:664` ✓ | **hapus** |
| `dcs_buka_sesi` | `:688` ✓ | **hapus** (instrumen lahir OPEN) |
| `dcs_tutup_sesi` | `:706` ✓ | → `dcs_tutup_instrumen` (tanpa arg) |
| `dcs_tambah_responden` | `:724` ✓ | ubah signature → `partisipan_ids: list[str]` |
| `dcs_analisis` | `:754` ✓ | buang `sesi_id` **dan** `wcp_sesi_id` |
| `dcs_hasil` | `:775` ✓ | buang `sesi_id` **dan** `wcp_sesi_id` |
| `detail_dcs_sesi` | `:2123` ✓ | → `dcs_instrumen` (tanpa arg) |
| `cari_dcs_sesi` | `:2139` ✓ | **hapus** |
| `perbarui_dcs_sesi` | `:2165` ✓ | → `dcs_perbarui_instrumen(min_responden?, catatan?)` |
| `hapus_dcs_sesi` | `:2201` ✓ | **hapus** |
| `dcs_daftar_responden` | `:2224` ✓ | buang arg `sesi_id` |
| `daftar_wcp_sesi` `:800`, `buat_wcp_sesi` `:823`, `wcp_buka_sesi` `:847`, `wcp_tutup_sesi` `:865`, `wcp_tambah_responden` `:883`, `wcp_analisis` `:913`, `wcp_hasil` `:931`, `detail_wcp_sesi` `:2434`, `cari_wcp_sesi` `:2450`, `perbarui_wcp_sesi` `:2476`, `hapus_wcp_sesi` `:2512`, `wcp_daftar_responden` `:2535` | ✓ | perlakuan **cermin** DCS |

Tidak berubah: `dcs_detail_responden` `:2240`, `dcs_hapus_responden` `:2256`, `dcs_submit_jawaban`
`:2275`, `dcs_daftar_jawaban` `:2306`, `dcs_daftar_subskala` `:2322`, `dcs_detail_subskala` `:2335`,
`dcs_subskala_items` `:2351`, `dcs_perbarui_item` `:2367`, `dcs_kuesioner_saya` `:2399`,
`dcs_hasil_responden` `:2412` — dan padanan WCP-nya. (Path endpoint-nya tidak mengandung sesi.)

**Catatan**: `std_dcs_flag` di `:3432`, `:3559` adalah field **standar CalHR pada uraian tugas** — sama
sekali tidak berhubungan dengan sesi DCS. **Jangan disentuh.**

## Langkah eksekusi

### Langkah 1 — Tunggu & tarik backend

Pastikan item 001 sudah merge dan `openapi.json` backend sudah mencerminkan endpoint baru. Semua path
di bawah harus diverifikasi ada di sana sebelum menulis tool.

### Langkah 2 — Tulis ulang blok DCS di `server.py`

Blok `# DOMAIN: DCS` (mulai `server.py:636`). Tool baru:

```python
@mcp.tool
async def dcs_instrumen(ctx: Context) -> dict:
    """Ambil status instrumen DCS (status, min_responden, catatan).

    DCS adalah instrumen singleton — satu deployment = satu studi, jadi tidak ada sesi.

    Returns:
        Dict berisi ``status`` (OPEN | CLOSED | ANALYZED), ``min_responden``, ``catatan``.
    """
    try:
        return await backend_get("/api/v1/dcs/instrumen", ctx=ctx)
    except BackendError as exc:
        _raise_tool_error(exc)
```

Sisanya dengan pola yang sama:

| Tool | Endpoint | Argumen |
|---|---|---|
| `dcs_instrumen` | `GET /api/v1/dcs/instrumen` | — |
| `dcs_perbarui_instrumen` | `PATCH /api/v1/dcs/instrumen` | `min_responden?`, `catatan?` |
| `dcs_tutup_instrumen` | `POST /api/v1/dcs/instrumen/tutup` | — |
| `dcs_buka_ulang_instrumen` | `POST /api/v1/dcs/instrumen/buka-ulang` | — |
| `dcs_daftar_responden` | `GET /api/v1/dcs/responden` | — |
| `dcs_tambah_responden` | `POST /api/v1/dcs/responden` | `partisipan_ids: list[str]` |
| `dcs_analisis` | `POST /api/v1/dcs/analisis` | — |
| `dcs_hasil` | `GET /api/v1/dcs/hasil` | — |

Docstring tiap tool harus menjelaskan bahwa DCS adalah instrumen tunggal (tidak ada sesi) — ini yang
mencegah Claude mengarang `sesi_id` dari kebiasaan lama.

### Langkah 3 — Cermin untuk WCP

Blok `# DOMAIN: WCP`, sama persis. Tool `wcp_hasil` juga tanpa argumen.

### Langkah 4 — Dokumentasi

- `README.md`: perbarui daftar tool + jumlah tool.
- `CLAUDE.md` MCP: catat bahwa DCS/WCP tidak punya sesi (TI & OPM masih punya).
- `CHANGELOG.md`: **BREAKING** — tool sesi DCS/WCP dihapus.

## Kriteria penerimaan

- [ ] `grep -n "dcs.*sesi\|sesi.*dcs\|wcp.*sesi\|sesi.*wcp" src/anjab_abk_mcp/server.py` → tidak ada hasil
      (kecuali komentar/changelog).
- [ ] Tool TI (`ti_*`, `*_ti_sesi`) dan OPM (`*_opm_sesi`) **masih utuh** — hitung ulang, jangan sampai
      ikut terhapus saat cari-ganti.
- [ ] Setelah reconnect `/mcp`, `dcs_instrumen` mengembalikan status tanpa argumen apa pun.
- [ ] `dcs_tambah_responden` bisa menambahkan 5 partisipan dalam satu panggilan.

## Skenario uji

Sesuai `automated-test-skill`, lewat `make test`. Test yang ada di `tests/` memakai backend tiruan —
perbarui fixture-nya agar merespons endpoint baru.

1. Tiap tool baru memanggil path & method yang benar (assert pada klien tiruan).
2. `dcs_tambah_responden(["p1","p2"])` mengirim body `{"partisipan_ids": ["p1","p2"]}`.
3. Error backend (mis. 422 saat instrumen CLOSED) diterjemahkan lewat `_raise_tool_error`.
4. Test penjaga: jumlah tool terdaftar sesuai ekspektasi, dan tidak ada tool ber-nama `*_dcs_sesi` /
   `*_wcp_sesi`.

## Definition of done

- [ ] `make test` hijau
- [ ] `CHANGELOG.md`, `README.md`, `CLAUDE.md` diperbarui
- [ ] Reconnect `/mcp` lalu panggil `dcs_instrumen` sungguhan untuk membuktikan jalan end-to-end
- [ ] Submodule di repo induk di-bump ke versi baru

## Risiko & catatan

- Bahaya terbesar item ini adalah **cari-ganti yang terlalu rakus**: kata "sesi" dipakai juga oleh TI,
  OPM, dan (di masa lalu) TS. Edit blok DCS dan WCP saja, per tool, jangan `sed` seluruh file.
- MCP terpasang editable/stdio — cukup reconnect `/mcp` untuk memuat perubahan, tidak perlu reinstall.
