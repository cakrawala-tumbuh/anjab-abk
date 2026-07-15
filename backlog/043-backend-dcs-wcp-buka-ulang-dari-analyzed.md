# Backlog 043 — DCS & WCP: buka ulang instrumen dari status ANALYZED (terminal)

> **Repo:** `anjab-abk-backend`
> **Status:** **Selesai (kode) 2026-07-15** — Opsi (b) diimplementasikan, `make test` hijau
> (638 test), belum di-commit. **Kebutuhan 1 (data-ops, reset data uji coba DCS produksi)
> masih menunggu deploy + instruksi eksplisit user** — lihat Definition of done.
> **Blocked by:** —
> **Skill yang dipakai:** `backend-skill`, `backend-postgresql-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Keputusan user (2026-07-15)

**Opsi (b) — endpoint "reset instrumen" admin** dipilih (lihat rancangan lengkap di bawah,
bagian "Opsi (b)"). Pemicu keputusan: percobaan reset DCS produksi via MCP (`dcs_hapus_responden`,
`dcs_buka_ulang_instrumen`) keduanya ditolak 422 persis seperti diprediksi item ini — tidak ada
jalur DB langsung yang tersedia dari sisi agen untuk jalan pintas manual, sehingga Kebutuhan 2
tidak bisa lagi ditunda. Konfirmasi data-ops (Kebutuhan 1) untuk siklus reset **pertama** setelah
endpoint ini dirilis: **DCS**, seluruh 3 responden uji coba (`drsp_55d09d5e`, `drsp_b63ac0a9`,
`drsp_885b62b4`, test run 2026-07-14) — bukan campuran data asli, boleh dihapus. WCP dibiarkan
memakai endpoint yang sama kelak saat dibutuhkan (implementasinya simetris, satu PR, tidak ada
alasan menunda salah satunya). **Eksekutor tetap wajib membaca `make backup` sebelum memanggil
endpoint reset di produksi** — endpoint baru ini destruktif by design.

## Tujuan

Feedback user (foto, 2026-07-14): **"WCP tidak bisa buka sesi"**. Terkonfirmasi lewat
runtime: instrumen WCP produksi berstatus **ANALYZED** (terminal) dan DCS juga **ANALYZED**.
Keduanya sampai ke status itu **karena DATA UJI COBA** (simulasi test run 14 Jul 2026 dengan
3 responden acak), **bukan data asli**. State machine saat ini menjadikan `ANALYZED` sebagai
status **terminal** (tidak ada transisi keluar), sehingga **tidak ada jalan** untuk membuka
ulang instrumen agar bisa memulai pengumpulan data **ASLI**.

Item ini memisahkan **dua kebutuhan yang berbeda** dan **sengaja tidak memutuskan** yang
kedua — ada trade-off produk yang harus diputuskan user lebih dulu:

1. **Kebutuhan segera (DATA OPS, bukan kode)** — reset data uji coba DCS & WCP produksi
   agar instrumen kembali OPEN dan siap menerima data asli. Ini menyentuh **data transaksi**
   (responden + jawaban), bukan data master/panel.
2. **Kebutuhan struktural (KODE)** — apakah state machine perlu jalur resmi keluar dari
   `ANALYZED` (buka ulang setelah analisis)? Ini mengubah kontrak & punya risiko
   inkonsistensi (analisis DCS/K-Index membaca hasil WCP). **Sajikan opsi a/b/c + rekomendasi,
   JANGAN putuskan sendiri.**

## Konteks penting: instrumen SINGLETON, bukan sesi

DCS dan WCP **tidak lagi punya konsep sesi** sejak revisi `[2026-07-12]` (lihat entri di
`anjab-abk-backend/CLAUDE.md`). Masing-masing adalah **singleton**: satu baris tetap
(`id='dcs'` / `id='wcp'`) dibuat oleh migrasi, mengalir lewat status
`OPEN → CLOSED → ANALYZED`. Jadi frasa user "buka sesi" secara teknis = "buka ulang
instrumen" (`POST .../instrumen/buka-ulang`). TI dan OPM (yang masih pakai sesi jabatan)
**tidak terpengaruh** item ini.

## Catatan verifikasi runtime (2026-07-14, backend v0.34.1)

- **WCP** instrumen: `status = ANALYZED`, `closed_at = 2026-07-14T10:27` (WIB/UTC per data).
- **DCS** instrumen: `status = ANALYZED`, `closed_at = 2026-07-14T08:34`.
- Backend produksi: **v0.34.1**.
- Catatan teknis: `closed_at` diisi pada transisi **CLOSED** (`instrumen_sql.py` `_transition`,
  `if target == "CLOSED"`), **bukan** pada `ANALYZED` — jadi timestamp itu menandai kapan
  instrumen ditutup, lalu dipertahankan menembus `set_analyzed()`.
- Sumber data ANALYZED ini = **test run uji coba** (lihat memory
  `dcs-test-run-2026-07-14.md` & `wcp-test-run-2026-07-14.md`): masing-masing 3 responden acak,
  **bukan** partisipan sebenarnya. Harus direset sebelum pengumpulan data asli.

## Keputusan yang sudah dikunci

- **Instrumen tetap singleton** — item ini TIDAK mengembalikan konsep sesi ke DCS/WCP.
- **Data panel SME / data master JANGAN PERNAH disentuh** (aturan user, memory
  `ti-opm-test-3-2026-07-14.md`). Reset hanya menyentuh **data transaksi** DCS/WCP
  (baris `dcs_responden`/`wcp_responden` + `*_jawaban` turunannya). DCS/WCP tidak punya
  keterkaitan ke SME panel, jadi risiko menyentuh panel = nol untuk instrumen ini — tetap
  ditegaskan agar tidak salah sasaran.
- **Data-ops (Kebutuhan 1) butuh konfirmasi eksplisit user** tentang baris mana yang dihapus
  sebelum eksekusi apa pun di DB produksi.
- **Kebutuhan struktural (Kebutuhan 2) TIDAK boleh diputuskan oleh agen pelaksana** — pilih
  opsi a/b/c hanya setelah user memutuskan.

## Kondisi sekarang (verified)

| Fakta | Lokasi | ✓ |
|---|---|---|
| State machine WCP: `OPEN→{CLOSED}`, `CLOSED→{OPEN,ANALYZED}`, `ANALYZED→∅` (terminal) | `src/anjab_abk_backend/wcp/services/instrumen.py:16-20` | ✓ |
| State machine DCS: identik dengan WCP | `src/anjab_abk_backend/dcs/services/instrumen.py:16-20` | ✓ |
| Impl SQL WCP memakai ulang `_VALID_TRANSITIONS` (import dari `instrumen.py`) di `_transition()` | `src/anjab_abk_backend/wcp/services/instrumen_sql.py:19,62-74` | ✓ |
| Impl SQL DCS analog | `src/anjab_abk_backend/dcs/services/instrumen_sql.py:19,62-83` | ✓ |
| Method service: `get/update/tutup/buka_ulang/set_analyzed` (Protocol) | `wcp/services/instrumen.py:38-45`, `dcs/services/instrumen.py:38-45` | ✓ |
| `buka_ulang()` = `_transition("OPEN")` — hanya sah dari CLOSED (bukan ANALYZED) | `wcp/services/instrumen_sql.py:79-80` | ✓ |
| Endpoint `POST /api/v1/wcp/instrumen/buka-ulang`, `operation_id=wcp_instrumen_buka_ulang`, `_WRITE_GUARDS` | `src/anjab_abk_backend/api/v1/wcp_instrumen.py:70-81` | ✓ |
| Endpoint DCS analog `POST /api/v1/dcs/instrumen/buka-ulang` | `src/anjab_abk_backend/api/v1/dcs_instrumen.py` | ✓ (dikonfirmasi ulang saat eksekusi) |
| `set_analyzed()` dipanggil dari alur analisis (hanya bila status `CLOSED`) | `api/v1/wcp_hasil.py:74`, `api/v1/dcs_hasil.py:108` | ✓ |
| Analisis DCS membaca hasil WCP (K-Index) via `_compute_wcp_risk_score(wcp_rsp, wcp_jwb)` | `api/v1/dcs_hasil.py:82-83,105` | ✓ |
| Responden punya `delete()`; jawaban ikut terhapus lewat FK `ON DELETE CASCADE` (migrasi `a4aeb5bcbe81`) | `wcp/services/responden_sql.py:212`, CLAUDE.md entri `[2026-07-12]` | ✓ |
| Baris singleton dibuat migrasi dengan `status` default `OPEN` | `migrations/versions/20260712_3b10e24fa970_dcs_wcp_hapus_sesi_instrumen_singleton.py:77,93-96` | ✓ |
| Status = `Literal["OPEN","CLOSED","ANALYZED"]` | `wcp/schemas/instrumen.py:10`, `dcs/schemas/instrumen.py` | ✓ |
| Test state machine yang sudah ada (tutup/buka-ulang/transisi invalid) | `tests/test_wcp_instrumen.py`, `tests/test_dcs_instrumen.py` | ✓ |
| Tool MCP terkait: `wcp_buka_ulang_instrumen`, `dcs_buka_ulang_instrumen` | repo `anjab-abk-mcp` | ✓ |

> ⚠️ Agen pelaksana WAJIB membaca ulang file di atas sebelum mengedit — baris bisa bergeser.
> `_VALID_TRANSITIONS` didefinisikan **sekali** di `instrumen.py` tiap modul dan **di-import**
> oleh `instrumen_sql.py`; jadi cukup ubah di satu tempat per modul (bukan dua).

---

## Kebutuhan 1 — DATA OPS (bukan kode): reset data uji coba DCS & WCP

**Tujuan:** kembalikan instrumen DCS & WCP produksi ke `OPEN` dengan data transaksi bersih,
supaya siap menerima data asli. **Tidak menyentuh kode** — hanya operasi DB + panggilan API
admin. **Butuh konfirmasi user lebih dulu.**

### Yang HARUS dikonfirmasi ke user sebelum eksekusi

1. Konfirmasi bahwa **semua** responden DCS & WCP produksi saat ini adalah data uji coba
   (test run 14 Jul) dan **boleh dihapus** — bukan campuran data asli.
2. Konfirmasi apakah reset dilakukan untuk **DCS saja, WCP saja, atau keduanya**.
3. Konfirmasi apakah perlu **backup DB lebih dulu** (disarankan **ya** — ada
   `make backup` / `scripts/backup.sh`).

### Langkah ops (setelah Kebutuhan 2 opsi (b) dirilis) — urutan wajib

**Digantikan seluruhnya oleh satu panggilan endpoint baru** — tidak ada lagi SQL manual maupun
panggilan `DELETE responden` satu-per-satu:

1. **Backup DB produksi**: `make backup` (butuh `DATABASE_URL` di env). Simpan file `.dump`.
2. **Panggil `POST /api/v1/dcs/instrumen/reset`** (admin) — dalam satu transaksi menghapus
   seluruh responden DCS (+jawaban via CASCADE) dan mengembalikan status ke `OPEN`,
   `closed_at=NULL`.
3. **Verifikasi**: `GET /api/v1/dcs/instrumen` → `status=OPEN`, `closed_at=null`;
   `GET /api/v1/dcs/responden` → kosong.
4. **Assign ulang partisipan** sebagai responden DCS lewat `dcs_tambah_responden` (MCP) atau UI
   admin `/dcs` — instrumen `OPEN` kini menerima responden baru.
5. WCP mengikuti pola identik (`POST /api/v1/wcp/instrumen/reset`) bila/ketika dibutuhkan —
   tidak dieksekusi sebagai bagian siklus reset DCS ini kecuali diminta terpisah.

---

## Kebutuhan 2 — STRUKTURAL (kode): jalur keluar dari ANALYZED

**Masalah desain:** `ANALYZED` terminal berarti sekali instrumen dianalisis, tidak ada jalan
kembali membuka pengumpulan data lewat API — bahkan untuk kasus sah "analisis tadi cuma uji
coba, sekarang mulai data asli". **Trade-off inti:** analisis DCS menghitung **K-Index** dari
hasil WCP (`dcs_hasil.py:105`, `_compute_wcp_risk_score`). Membuka ulang instrumen setelah
`ANALYZED` lalu mengubah data responden membuat **hasil DCS/WCP yang sudah dilaporkan menjadi
basi (stale)** tanpa penanda apa pun.

**Keputusan sudah dibuat: Opsi (b).** Tiga opsi di bawah dipertahankan sebagai jejak
pertimbangan (lihat "Keputusan user" di atas) — eksekutor langsung ke bagian **"Bila Opsi (b)"**
di "Langkah eksekusi".

### Opsi (a) — Izinkan transisi `ANALYZED → OPEN` (dengan invalidasi hasil)

- Ubah `_VALID_TRANSITIONS` kedua modul: `"ANALYZED": {"OPEN"}` (dari `set()`).
- `buka_ulang()` otomatis jadi sah dari `ANALYZED` (memanggil `_transition("OPEN")`) —
  **tidak** perlu endpoint baru; `POST .../instrumen/buka-ulang` cukup.
- **Invalidasi hasil**: karena `compute_hasil()` dihitung **on-the-fly** dari data responden
  (tidak ada tabel hasil tersimpan — `GET .../hasil` menghitung ulang tiap dipanggil),
  "stale" di sini berarti *pembaca yang sudah mengunduh hasil lama* punya angka usang, bukan
  ada baris hasil basi di DB. **Verifikasi asumsi ini saat eksekusi** (baca `wcp_hasil.py`/
  `dcs_hasil.py` `GET /hasil`) — bila ternyata hasil di-cache/disimpan, invalidasi harus
  eksplisit.
- **Kelemahan:** membuka ulang **tidak menghapus** jawaban lama; admin bisa lupa & mencampur
  responden uji coba dengan asli. Reset data tetap manual (Kebutuhan 1 langkah 2).
- **Risiko K-Index:** WCP dibuka ulang → data WCP berubah → hasil DCS (yang sudah `ANALYZED`)
  jadi tak konsisten dengan WCP terbaru, tanpa pemberitahuan.

### Opsi (b) — Endpoint "reset instrumen" admin (REKOMENDASI kandidat)

- Endpoint baru admin-only, mis. `POST /api/v1/{dcs,wcp}/instrumen/reset`, yang dalam **satu
  transaksi**: (1) hapus SEMUA responden instrumen tsb (jawaban ikut lewat CASCADE),
  (2) set status `→ OPEN`, `closed_at → NULL`. Idempoten.
- Transisi `ANALYZED → OPEN` diizinkan **hanya** lewat jalur reset ini (bisa via method
  service khusus `reset()` yang tidak lewat `_VALID_TRANSITIONS` biasa, atau menambah
  `ANALYZED→OPEN` ke tabel transisi tapi membungkusnya dengan penghapusan data). Menjaga
  `buka-ulang` biasa tetap **hanya** `CLOSED→OPEN` (tanpa hapus data), sehingga "buka ulang
  sesaat sebelum analisis" tidak sengaja menghapus jawaban.
- **Keunggulan:** menyelesaikan Kebutuhan 1 & 2 sekaligus — reset ke depan cukup satu klik,
  tanpa SQL manual di produksi; tidak ada risiko mencampur data uji & asli karena data lama
  dibersihkan sebagai bagian dari reset.
- **Kelemahan:** destruktif (menghapus responden+jawaban) — wajib konfirmasi di UI/MCP +
  `logger.warning` mencatat aktor (pola `paksa=true` di CLAUDE.md entri `[2026-07-12]`).
- **K-Index:** reset DCS tidak menyentuh WCP dan sebaliknya; bila keduanya perlu direset,
  admin memanggil dua kali. Dokumentasikan urutan yang disarankan (reset WCP dulu bila mau
  mempertahankan konsistensi K-Index saat DCS dianalisis ulang).

### Opsi (c) — Tetap terminal; selesaikan lewat data-ops saja

- Tidak ada perubahan kode. Kebutuhan 1 diselesaikan dengan `UPDATE ... SET status='OPEN'`
  manual di DB (setelah backup), sekali ini saja.
- **Keunggulan:** nol risiko regresi; menjaga `ANALYZED` benar-benar final (hasil yang sudah
  dilaporkan tidak pernah bisa dibuat basi lewat API).
- **Kelemahan:** setiap kebutuhan reset di masa depan butuh akses DB langsung ke produksi —
  operasi manual berisiko, tidak ada jejak audit lewat API, tidak bisa dilakukan admin non-DBA.

### Rekomendasi (untuk pertimbangan user — bukan keputusan)

**Opsi (b)** tampak paling seimbang: memberi admin jalan keluar yang aman & ber-audit dari
`ANALYZED` **tanpa** mengaburkan makna `buka-ulang` biasa (`CLOSED→OPEN`, non-destruktif) dan
**tanpa** meninggalkan jawaban uji coba yang bisa tercampur data asli. Opsi (a) paling murah
tapi menyisakan lubang "campur data" & membuat hasil bisa basi diam-diam. Opsi (c) paling
aman secara kode tapi memindahkan beban ke operasi DB manual berulang. **Tunggu keputusan
user sebelum menulis kode apa pun.**

## Langkah eksekusi (bercabang sesuai opsi terpilih)

> Jalankan hanya setelah user memilih opsi. Semua opsi kode: **jangan** edit
> `migrations/versions/` lama; tabel `*_instrumen` tidak berubah skema untuk (a)/(b)/(c),
> jadi **tidak ada migrasi Alembic** (hanya perubahan perilaku/endpoint).

### Bila Opsi (a)

1. `wcp/services/instrumen.py` & `dcs/services/instrumen.py`: ubah
   `"ANALYZED": set()` → `"ANALYZED": {"OPEN"}`. (Satu tempat per modul; `instrumen_sql.py`
   memakai ulang lewat import.)
2. Verifikasi `GET /hasil` dihitung on-the-fly (tidak ada tabel hasil) — bila ada cache,
   tambah invalidasi.
3. Update `summary`/`description` endpoint `buka-ulang` (kini juga dari ANALYZED) di
   `wcp_instrumen.py` & `dcs_instrumen.py`.
4. `make export-openapi` bila teks berubah; regen `openapi.json`.

### Bila Opsi (b)

1. Tambah method `reset()` ke Protocol + impl in-memory + impl SQL di kedua modul
   (`instrumen.py`, `instrumen_sql.py`): hapus semua responden (via `RespondenService` yang
   di-inject, agar CASCADE menghapus jawaban) lalu set `status=OPEN`, `closed_at=NULL`, dalam
   satu transaksi. Pertimbangkan menyuntik `RespondenService` ke endpoint (bukan ke service
   instrumen) agar lapisan tidak lintas-domain — ikuti pola DI yang ada (`dcs_hasil.py`
   menyuntik banyak service ke fungsi endpoint).
2. Endpoint baru admin-only `POST /api/v1/{dcs,wcp}/instrumen/reset`, `_WRITE_GUARDS` (atau
   `_ADMIN_GUARDS` bila reset ingin dibatasi admin murni — cek konvensi guard di
   `dependencies.py`), `response_model` = `{Dcs,Wcp}InstrumenRead`, `logger.warning(aktor)`.
3. `_VALID_TRANSITIONS` biasa **tidak** diubah (buka-ulang tetap `CLOSED→OPEN`). Reset
   melewati tabel transisi dengan set status langsung (dibungkus penghapusan data).
4. Update tool MCP terkait di repo `anjab-abk-mcp` (item terpisah — satu item = satu repo;
   buat backlog turunan setelah `openapi.json` berubah).
5. `make export-openapi`; regen `openapi.json` (breaking-additive: endpoint baru).

### Bila Opsi (c)

1. Tidak ada perubahan kode. Selesaikan Kebutuhan 1 langkah ops (SQL manual setelah backup).
2. Tutup item ini dengan catatan keputusan.

## Kriteria penerimaan

### Data-ops (Kebutuhan 1) — semua opsi

- [ ] Backup DB dibuat & lokasinya dicatat sebelum operasi destruktif apa pun.
- [ ] Setelah reset: `GET /api/v1/{dcs,wcp}/instrumen` → `status=OPEN`, `closed_at=null`.
- [ ] `GET /api/v1/{dcs,wcp}/responden` → hanya berisi data yang memang dipertahankan (kosong
      bila semua uji coba).
- [ ] Tidak ada baris `sme_panel` / master yang berubah (dibuktikan, bukan diasumsikan).

### Opsi (a)

- [ ] `POST /api/v1/{dcs,wcp}/instrumen/buka-ulang` dari `ANALYZED` → 200, status `OPEN`.
- [ ] Transisi lain yang tak valid tetap 422.

### Opsi (b)

- [ ] `POST /api/v1/{dcs,wcp}/instrumen/reset` (admin) → 200: status `OPEN`, `closed_at=null`,
      seluruh responden + jawaban terhapus.
- [ ] Non-admin → 401/403 sesuai guard.
- [ ] `buka-ulang` biasa **tetap** hanya `CLOSED→OPEN` (dari `ANALYZED` tetap 422).
- [ ] `logger.warning` mencatat aktor tiap reset.

### Opsi (c)

- [ ] Tidak ada perubahan kode; keputusan didokumentasikan.

## Skenario uji

Test state machine ada di `tests/test_wcp_instrumen.py` & `tests/test_dcs_instrumen.py`
(pola `TestClient`, fixture `client` ber-token & `anon_client`).

- **Opsi (a):** tambah test `test_buka_ulang_dari_analyzed_*` (tutup → analisis sampai
  ANALYZED → `buka-ulang` → 200 `OPEN`). Perlu setup min. `min_responden` responden ber-submit
  agar analisis lolos (lihat pola di `tests/test_wcp_analisis.py`). Pastikan
  `test_buka_ulang_dari_open_ditolak` (existing) tetap hijau.
- **Opsi (b):** test endpoint `reset`: (1) admin sukses → OPEN + responden kosong;
  (2) non-admin → 401/403; (3) `buka-ulang` dari ANALYZED **tetap** 422 (reset ≠ buka-ulang);
  (4) jawaban ikut terhapus (CASCADE) — verifikasi lewat `GET .../responden` kosong.
- **Opsi (c):** tidak ada test baru.
- Semua opsi: `make test` (lint + unit di Docker) hijau. Test migrasi penjaga
  (`tests/test_migrations.py`) harus tetap hijau — untuk (a)/(b) tidak ada revisi baru, jadi
  `test_schema_matches_models` & `test_single_head` tidak boleh berubah status.

## Definition of done

- [x] Opsi produk (a/b/c) dipilih user & dicatat di item ini — **Opsi (b)**, 2026-07-15.
- [x] Konfirmasi data-ops (baris mana dihapus, DCS/WCP/keduanya, backup) diperoleh user — siklus
      reset pertama: DCS saja (3 responden uji coba), backup wajib sebelum eksekusi.
- [x] `make test` hijau di `anjab-abk-backend` — **638 test** (lint + unit, Docker).
- [x] `CHANGELOG.md` diperbarui — versi `0.37.0`.
- [x] `CLAUDE.md` repo diperbarui — entri Revisi Desain baru
      `[2026-07-15] DCS & WCP: endpoint reset — jalur keluar resmi dari ANALYZED`.
- [x] `openapi.json` diregenerasi (gitignored, tidak di-commit) — 2 operasi baru
      (`dcs_instrumen_reset`, `wcp_instrumen_reset`) terverifikasi lewat introspeksi skema.
      Item turunan MCP sudah ada sebagai backlog **047** (dibuat sebelum item ini dieksekusi,
      sebelumnya berstatus "Menunggu" — kini unblocked, lihat `BACKLOG.md`).
- [x] Item dipindah ke tabel "Selesai" di `BACKLOG.md`.
- [ ] **Belum di-commit** (aturan: commit hanya atas instruksi eksplisit user).
- [ ] **Kebutuhan 1 (data-ops) BELUM dieksekusi** — reset data uji coba DCS produksi (3
      responden test run 2026-07-14) butuh kode ini ter-deploy ke produksi lebih dulu
      (rilis versi baru), lalu `make backup` + panggil `POST /api/v1/dcs/instrumen/reset`
      admin. Di luar cakupan sesi ini (kode-saja); eksekusi menyusul setelah deploy &
      instruksi eksplisit user.

## Risiko & catatan

- **Hasil DCS bergantung pada WCP (K-Index).** Membuka ulang / mereset WCP setelah DCS
  `ANALYZED` membuat K-Index yang sudah dilaporkan tak konsisten dengan data WCP terbaru,
  tanpa penanda. Bila opsi (a)/(b) dipilih, dokumentasikan urutan reset yang disarankan &
  ingatkan admin untuk menjalankan ulang analisis DCS setelah WCP berubah.
- **Data uji coba vs data asli.** Seluruh masalah ini muncul karena instrumen produksi
  "terbakar" ke `ANALYZED` oleh test run. Ke depan, pertimbangkan **jangan** menjalankan
  simulasi test run di instance produksi (di luar lingkup item ini, tapi catat sebagai akar
  penyebab). Memory `dcs-test-run-2026-07-14.md` & `wcp-test-run-2026-07-14.md` merekam bahwa
  data ANALYZED ini memang uji coba.
- **Operasi destruktif di produksi** (hapus responden/jawaban, `UPDATE status`) wajib
  didahului backup (`make backup`) dan konfirmasi user eksplisit. `restore.sh` tersedia untuk
  rollback.
- **`_VALID_TRANSITIONS` didefinisikan sekali per modul** (`instrumen.py`) dan di-import oleh
  `instrumen_sql.py` — jangan sampai mengubah salah satu saja hingga in-memory & SQL divergen.
- **Guard**: endpoint reset (opsi b) harus mengikuti pola guard yang ada; `tests/test_auth_guards.py`
  memindai skema OpenAPI dan akan menggagalkan endpoint baru yang lupa diguard.
- **Cakupan lintas repo**: bila opsi (b) menambah endpoint, tool MCP (`{dcs,wcp}_reset_instrumen`)
  dan tombol web app menyusul sebagai **item backlog terpisah** (satu item = satu repo),
  di-blok oleh perubahan `openapi.json` item ini.
