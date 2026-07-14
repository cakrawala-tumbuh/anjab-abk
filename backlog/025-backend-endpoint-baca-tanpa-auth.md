# Backlog 025 — KEAMANAN: 32 endpoint GET tanpa guard autentikasi (PII partisipan & hasil DCS/WCP per individu terbuka publik)

> **Repo:** `anjab-abk-backend`
> **Status:** Siap dieksekusi (setelah keputusan cakupan di "Keputusan yang perlu dikonfirmasi")
> **Blocked by:** —
> **Skill yang dipakai:** `backend-skill`, `backend-authentik-skill`, `automated-test-skill`
> **Prioritas: TERTINGGI di backlog aktif** — ini pemaparan data, bukan bug fungsional.
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Sebagian besar endpoint **GET** di backend tidak memasang guard autentikasi sama sekali —
hanya `Depends(rate_limit)`. Akibatnya **siapa pun di internet, tanpa token apa pun**, dapat
membaca data dari instance produksi YPII, termasuk:

- **`GET /api/v1/partisipan`** → daftar **seluruh 103 pegawai YPII asli** beserta
  `nama`, `email`, dan `authentik_user_id` (lihat `PartisipanRead` di
  `src/anjab_abk_backend/core/schemas/partisipan.py:85-103` ✓). Ini **data pribadi**, bocor
  penuh tanpa perlu menebak ID apa pun.
- **`GET /api/v1/wcp/hasil-responden/{responden_id}`** dan
  **`GET /api/v1/dcs/hasil-responden/{responden_id}`** → hasil **per individu** instrumen
  psikososial (DCS) & beban kerja/burnout (WCP). Ini kategori data paling sensitif di seluruh
  aplikasi.
- `GET /api/v1/dcs/hasil`, `/wcp/hasil` (agregat), `/sme-panel` (keanggotaan panel),
  `/jabatan`, `/sekolah`, `/jenjang-pendidikan`, `/mata-pelajaran`, seluruh katalog & master
  Task Inventory.

Tujuan item ini: **semua endpoint baca yang mengandung data organisasi/orang wajib menuntut
token yang valid**, sekurang-kurangnya `Depends(get_current_principal)`; endpoint yang memuat
data per individu wajib juga guard object-level (admin ATAU pemilik data).

## Kondisi sekarang (verified)

Diverifikasi 2026-07-14 lewat pembacaan kode **dan** permintaan langsung ke produksi
(`https://api.anjab-abk.cantum-ypii.com`) **tanpa header `Authorization` sama sekali**.

| # | Fakta | Verifikasi |
|---|---|---|
| 1 | Tidak ada guard di level router: `include_router(..., dependencies=...)` **nol** kemunculan di seluruh `src/` — seluruh otorisasi dipasang per-operasi di dekorator | ✓ `grep -rc "include_router.*dependencies"` → 0 |
| 2 | `_WRITE_GUARDS = [Depends(get_current_principal), Depends(rate_limit)]` hanya dipasang di operasi **tulis** (`partisipan.py:36,124,246,269` ✓). Operasi **baca** (`list_partisipan`, `get_partisipan`) tidak memasang guard apa pun | ✓ dibaca langsung |
| 3 | **32 operasi GET** (di luar `/health` & `/ready` yang memang publik) tidak memasang `get_current_principal` / `require_admin` / `_ADMIN_GUARDS` / `_WRITE_GUARDS` — daftar lengkap di bawah | ✓ pemindaian AST/regex atas `src/anjab_abk_backend/api/v1/*.py` |
| 4 | **PRODUKSI, tanpa token:** `GET /api/v1/partisipan` → **HTTP 200** (mengembalikan `total` seluruh partisipan + `nama`/`email`/`authentik_user_id`) | ✓ `curl` langsung ke prod |
| 5 | **PRODUKSI, tanpa token:** `GET /api/v1/jabatan` → 200, `GET /api/v1/sme-panel` → 200, `GET /api/v1/sekolah` → 200, `GET /api/v1/dcs/hasil` → 200, `GET /api/v1/wcp/hasil` → 200 | ✓ `curl` langsung ke prod |
| 6 | **PRODUKSI, tanpa token:** `GET /api/v1/wcp/hasil-responden/wrsp_7c0ff89d` → **HTTP 200**, mengembalikan `{responden_id, dimensi[...]}` — hasil WCP **satu individu nyata** (A. Widjianto, dari uji coba WCP 2026-07-14) | ✓ `curl` langsung ke prod |
| 7 | Sebagai pembanding, endpoint yang **sudah benar**: `GET /dcs/responden`, `/wcp/responden`, `/time-study/penugasan` → **401** di produksi (memasang `Depends(require_admin)`, mis. `dcs_responden.py:46` ✓). Jadi polanya sudah ada di repo — hanya belum diterapkan merata | ✓ `curl` + baca kode |
| 8 | Produksi melaporkan `info.version = "0.26.0"` (lihat backlog 023 fakta #9) — perbaikan ini **wajib benar-benar ter-deploy**, tidak cukup merge ke `master` | ✓ |

### Daftar 32 GET tanpa guard (hasil pemindaian, `src/anjab_abk_backend/api/v1/`)

**Sensitif — data orang (prioritas 1):**
- `partisipan.py` → `GET /` (`list_partisipan`), `GET /{partisipan_id}` (`get_partisipan`)
- `dcs_hasil.py` → `GET /hasil-responden/{responden_id}` (`get_hasil_responden`)
- `wcp_hasil.py` → `GET /hasil-responden/{responden_id}` (`get_hasil_responden`)
- `dcs_hasil.py` → `GET /hasil`; `wcp_hasil.py` → `GET /hasil` (agregat)
- `sme_panel.py` → `GET /` , `GET /{panel_id}` (keanggotaan panel = siapa menilai siapa)

**Data organisasi/master (prioritas 2):**
- `jabatan.py` → `GET /`, `GET /{jabatan_id}`
- `sekolah.py` → `GET /`, `GET /{sekolah_id}`
- `jenjang_pendidikan.py` → `GET /`, `GET /{jp_id}`
- `mata_pelajaran.py` → `GET /`, `GET /{mp_id}`
- `dcs_instrumen.py` → `GET /`; `wcp_instrumen.py` → `GET /`
- `dcs_subskala.py` → `GET /`, `GET /{kode}`, `GET /{kode}/items`
- `wcp_dimensi.py` → `GET /`, `GET /{kode}`, `GET /{kode}/items`
- `taskinv_catalog.py` → `GET /`, `GET /kombinasi`
- `taskinv_tugas_pokok.py` → `GET /`, `GET /{tp_id}`
- `taskinv_detil_tugas.py` → `GET /`, `GET /{dt_id}`
- `taskinv_uraian_tugas.py` → `GET /`, `GET /{ut_id}`

**Sengaja publik — JANGAN diubah:** `system.py` → `GET /health`, `GET /ready`.

## Keputusan yang perlu dikonfirmasi ke user sebelum eksekusi

1. **Apakah seluruh 32 endpoint di atas harus butuh token, atau ada yang memang sengaja
   publik?** Rekomendasi: **semuanya butuh token** kecuali `/health` & `/ready`. Katalog TI &
   instrumen DCS/WCP memang bukan data pribadi, tapi tidak ada alasan bisnis membukanya ke
   publik, dan web app selalu memanggilnya dalam keadaan login.
2. **Untuk `hasil-responden/{id}` DCS & WCP**: cukup `get_current_principal`, atau perlu guard
   object-level (admin ATAU partisipan pemilik responden itu)? Rekomendasi: **object-level**,
   mengikuti pola `authorize_sesi_access()` yang sudah ada di `dependencies.py:365-386` ✓ —
   partisipan tidak boleh membaca hasil psikososial rekan kerjanya hanya karena dia login.

## Langkah eksekusi

### Langkah 1 — Definisikan konstanta guard baca

Di tiap modul terkait, tambahkan (mengikuti pola `_WRITE_GUARDS` yang sudah ada):

```python
_READ_GUARDS = [Depends(get_current_principal), Depends(rate_limit)]
```

Pertimbangkan menaruhnya sekali di `dependencies.py` dan mengimpornya, agar tidak
terduplikasi di 15+ berkas.

### Langkah 2 — Pasang `_READ_GUARDS` di seluruh 32 operasi GET di daftar atas

Tambahkan `dependencies=_READ_GUARDS` + `**_AUTH` di `responses` (agar OpenAPI mendokumentasikan
401). **Jangan** sentuh `system.py`.

### Langkah 3 — Guard object-level untuk hasil per individu

Untuk `dcs_hasil.get_hasil_responden` dan `wcp_hasil.get_hasil_responden`, tambahkan guard
"admin ATAU pemilik responden" — buat helper baru di `dependencies.py` (mis.
`authorize_responden_access(principal, responden_id, par_service, rsp_service)`) mengikuti
bentuk `authorize_opm_sesi_access()` di `dependencies.py:389-405` ✓.

### Langkah 4 — Regenerasi `openapi.json`

`openapi.json` berubah (401/403 baru di banyak operasi). Ini **memicu pekerjaan turunan** di
`anjab-abk-web-app` (`npm run gen:api`) dan `anjab-abk-mcp` — buat item backlog terpisah bila
tipe/kontraknya benar-benar bergeser (kemungkinan besar hanya `responses`, bukan skema data,
jadi kemungkinan tidak ada perubahan kode klien).

### Langkah 5 — Verifikasi bahwa web app tidak rusak

Web app memanggil endpoint ini lewat `withServerAuth(accessToken)` (Server Component) — sudah
mengirim Bearer token, jadi seharusnya aman. **TAPI** periksa apakah ada pemanggilan tanpa token
(mis. di halaman publik/login, atau `client.GET` tanpa `withServerAuth`) sebelum menyatakan
selesai.

## Kriteria penerimaan

- [ ] `curl https://api.../api/v1/partisipan` **tanpa token** → **401** (bukan 200)
- [ ] Idem untuk `/jabatan`, `/sekolah`, `/sme-panel`, `/dcs/hasil`, `/wcp/hasil`,
      `/dcs/hasil-responden/{id}`, `/wcp/hasil-responden/{id}`, seluruh master TI
- [ ] `/health` & `/ready` **tetap** 200 tanpa token
- [ ] Partisipan yang login **tidak** bisa membaca `hasil-responden` milik partisipan lain (403)
- [ ] Web app tetap berfungsi penuh untuk admin & partisipan (login → semua halaman jalan)
- [ ] **Perbaikan benar-benar ter-deploy ke produksi** (cek `GET /openapi.json` versi naik &
      `curl` tanpa token → 401), bukan sekadar merge

## Skenario uji

- Test baru di `tests/` (backend): untuk **setiap** endpoint di daftar 32 di atas, panggil tanpa
  token → assert **401**. Tulis sebagai test terparametrisasi (`pytest.mark.parametrize`) atas
  daftar path, supaya endpoint baru yang lupa dipasangi guard langsung ketahuan.
- Test regresi: `/health` & `/ready` tanpa token → 200.
- Test object-level: partisipan A login → `GET /wcp/hasil-responden/{responden_milik_B}` → 403.
- `make test` hijau.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-backend`
- [ ] `openapi.json` diregenerasi
- [ ] `CHANGELOG.md` diperbarui (tandai sebagai perbaikan **keamanan**)
- [ ] `CLAUDE.md` backend diperbarui: catat invariant "setiap operasi GET wajib memasang
      `_READ_GUARDS`, kecuali `/health` & `/ready`"
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Ini pemaparan data yang sedang berlangsung di produksi**, bukan risiko teoretis: data
  pribadi 103 pegawai YPII (nama, email) dapat diambil siapa pun sekarang juga. Pertimbangkan
  memberi tahu pemilik data (YPII) dan/atau memasang mitigasi cepat (mis. block di Traefik untuk
  path `/api/v1/partisipan` dari luar) bila perbaikan kode + deploy tidak bisa segera dilakukan.
- Hasil DCS/WCP per individu adalah data psikososial — dampak paling besar bila bocor.
  Meski `responden_id` (8 hex) tidak mudah ditebak, tidak adanya autentikasi berarti satu-satunya
  pelindung adalah ketidakjelasan ID (*security through obscurity*), yang bukan kontrol yang sah.
- Temuan ini muncul sebagai efek samping simulasi SOP TI+OPM 2026-07-14 (memori
  `ti-opm-test-2-2026-07-14`): sejumlah tool MCP baca **tetap berhasil** memakai token yang sudah
  kedaluwarsa, sementara tool TI-sesi menolak dengan 401 — kejanggalan itu yang menuntun ke
  pemeriksaan ini.
