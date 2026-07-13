# Backlog 004 — Terminologi: "Sesi" → "Analisis Jabatan" di TI & OPM (UI saja)

> **Repo:** `anjab-abk-web-app` (utama), `anjab-abk-mcp` (docstring saja)
> **Status:** Siap dieksekusi (independen dari 001–003)
> **Blocked by:** —
> **Skill:** `frontend-development-skill`, `dokumentasi-penggunaan-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Sesi TI dan OPM **dipertahankan** — tapi namanya menyesatkan. Keduanya bukan "sesi studi", melainkan
**satu analisis untuk satu jabatan**: `TiSesiModel` punya `jabatan_id` + `koordinator_id` +
`task_frozen`, dan `OpmSesiModel` bahkan meng-`UNIQUE` `jabatan_id`. Satu studi punya puluhan jabatan →
puluhan "sesi". Kata "sesi" itulah yang membuat model ini terasa berlebihan padahal justru inti dari
ANJAB.

Item ini mengganti **istilah yang dilihat manusia** menjadi **"Analisis Jabatan"**, tanpa menyentuh
skema database, nama tabel, nama kolom, path endpoint, atau `sesi_id` di kode.

## Keputusan yang sudah dikunci

1. **Perubahan kosmetik/terminologi saja.** Nol perubahan skema, nol migrasi, nol perubahan endpoint.
   `sesi_id` tetap `sesi_id` di URL dan di kode.
2. Yang berubah hanya: label UI, judul halaman, teks tombol, breadcrumb, item menu, dokumentasi
   pengguna, dan **docstring tool MCP** (karena docstring itulah yang dibaca Claude).
3. Istilah pengganti: **"Analisis Jabatan"**. Contoh: "Daftar Sesi" → "Analisis Jabatan",
   "Buat Sesi" → "Mulai Analisis Jabatan", "Tutup Sesi" → "Tutup Analisis".
4. Kerjakan **setelah** 001–003 kalau ketiganya sedang berjalan, untuk menghindari konflik merge di
   `sidebar.tsx` dan `docs-usage/`. Tapi item ini tidak bergantung padanya secara teknis.

## Kondisi sekarang (verified per 2026-07-12)

| Fakta | Lokasi |
|---|---|
| `TiSesiModel`: `jabatan_id` (NOT NULL), `koordinator_id`, `task_frozen`, status 6 nilai; unique `(jabatan_id, periode)` | backend `models.py:431-455`; `taskinv/services/sesi_sql.py:96-105` ✓ |
| `OpmSesiModel`: `jabatan_id` **UNIQUE** — 1 sesi OPM per jabatan; `ti_sesi_id` sebagai lineage | backend `models.py:593-608` ✓ |
| Listing & detail TI | `src/app/(auth)/task-inventory/page.tsx`, `[sesi_id]/page.tsx`, `buat/page.tsx` ✓ |
| Listing & detail OPM | `src/app/(auth)/opm/page.tsx`, `[sesi_id]/page.tsx`, `buat/page.tsx`, `[sesi_id]/hasil/page.tsx` ✓ |
| Menu sidebar admin | `src/components/shell/sidebar.tsx` (`NAV_ADMIN`) ✓ |
| Docstring tool MCP TI/OPM (dibaca Claude, jadi ikut menyesatkan) | `anjab-abk-mcp/src/anjab_abk_mcp/server.py` ✓ |

## Langkah eksekusi

### Langkah 1 — Web app: label UI

Sisir teks yang **dilihat pengguna** di `src/app/(auth)/task-inventory/**` dan `src/app/(auth)/opm/**`
plus `src/components/shell/sidebar.tsx`:

- Judul listing: "Sesi Task Inventory" → **"Analisis Jabatan — Task Inventory"**
- Tombol: "Buat Sesi" → **"Mulai Analisis Jabatan"**; "Tutup Sesi" → **"Tutup Analisis"**
- Kolom tabel & breadcrumb: hilangkan kata "sesi"; jabatan yang jadi identitas utama baris.
- Transisi TI ("Mulai Tahap 1/2/3") **tetap** — itu istilah domain yang benar, bukan jargon internal.
- **Jangan** ubah nama variabel/prop/route yang mengandung `sesi` (mis. `params.sesi_id`,
  `TiSesiRead`). Ini murni string yang tampil di layar.

Cara aman: cari string literal yang mengandung "Sesi"/"sesi" **di dalam JSX dan label**, bukan
`grep -r sesi` lalu ganti semua.

### Langkah 2 — MCP: docstring

Di `anjab-abk-mcp/src/anjab_abk_mcp/server.py`, docstring tool `buat_ti_sesi`, `daftar_ti_sesi`,
`buat_opm_sesi`, dst.: jelaskan bahwa **satu "sesi" TI/OPM = satu analisis untuk satu jabatan**, dan
satu studi punya banyak di antaranya. Nama tool **tidak diubah** (menghindari breaking change tanpa
manfaat nyata).

### Langkah 3 — Dokumentasi pengguna

`docs-usage/`: sesuaikan istilah agar konsisten dengan UI baru.

## Kriteria penerimaan

- [ ] Tidak ada kata "sesi" di layar TI/OPM yang dilihat admin (kecuali di URL).
- [ ] Nol perubahan di `anjab-abk-backend` (verifikasi: `git status` bersih di sana).
- [ ] Nol perubahan pada `schema.ts`, route, dan nama variabel.
- [ ] `make test` hijau — E2E yang mencari tombol berdasarkan teks (mis. `getByRole("button", { name: "Buat Sesi" })`)
      **akan pecah** dan memang harus diperbarui. Sisir `e2e/` lebih dulu.

## Definition of done

- [ ] `make test` hijau di web-app
- [ ] `docs-usage` + `CHANGELOG.md` diperbarui
- [ ] Submodule di repo induk di-bump

## Risiko & catatan

- Nilai item ini adalah **kejelasan konsep**, bukan fungsionalitas. Kalau waktu terbatas, ini yang
  pertama ditunda — dan itu tidak apa-apa.
- Godaan terbesar: "sekalian saja rename kolom/tabelnya". **Jangan.** Rename skema tidak memberi
  manfaat apa pun ke pengguna dan membawa risiko migrasi yang tidak sebanding.
