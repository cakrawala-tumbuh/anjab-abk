# BACKLOG — anjab-abk

Indeks pekerjaan yang **sudah direncanakan tapi belum dieksekusi**, lintas ketiga sub-repo
(`anjab-abk-backend`, `anjab-abk-mcp`, `anjab-abk-web-app`).

Detail tiap item ada di `backlog/<id>-<slug>.md`. Konvensi & cara pakai: lihat bagian
"Backlog" di [CLAUDE.md](CLAUDE.md). Template item baru: [`backlog/TEMPLATE.md`](backlog/TEMPLATE.md).

## Aktif

| ID | Item | Repo | Status | Blocked by |
|---|---|---|---|---|
| [024](backlog/024-backend-ti-tahap3-task-kosong.md) | TI: sesi dgn task ber-`detil_tugas` NULL → **500** di `task-terpilih`/`hasil`/`analisis`; halaman detail crash total & sesi tak bisa dihapus lewat UI | backend | **SIAP DIEKSEKUSI — root cause TERBUKTI 2026-07-14** via API ber-token: `GET .../sesi/tises_434a8864/task-terpilih` → **500**, sedangkan `/sesi/{id}`, `/responden`, `/tahap2` → 200. Sebabnya `TiCatalogRead.detil_tugas` **nullable** tapi `TiTaskTerpilihRead.detil_tugas: str` **wajib**; `analisis.py:39` (& `:103`) hanya mem-fallback `""` saat **katalog hilang**, bukan saat `detil_tugas is None` → Pydantic `ValidationError` → 500. Data terdampak: **2 baris** (`WK-ALL-PD-001` Wali Kelas + 1 di Wakasek Kurikulum). ⚠️ Investigasi lama menyatakan hipotesis (b) "GUGUR" — **kelirunya di cara menguji**: kasus nyatanya *katalog ADA dgn `detil_tugas` NULL*, bukan *katalog hilang*. Fix: `(cat.detil_tugas or "") if cat else ""` di 2 tempat | — |
| [032](backlog/032-web-app-toapierror-membuang-pesan-backend.md) | Web app: ±20 berkas jalur baca masih `toApiError(null, …)` — **melempar** (tidak menelan) tapi membuang pesan & status HTTP backend; + pengecualian 026 di Tahap 2 ternyata menelan **semua** status, bukan hanya 404 | web-app | Siap dieksekusi | — |
| [033](backlog/033-web-app-tahap3-isian-standar-durasi.md) | TI Tahap 3: "Setuju dengan isian standar" **bocor** (field `Durasi/kali` tetap bisa diedit) & nilai standar durasi **tidak pernah diterapkan** (selalu 60 menit, padahal petunjuknya "<15 menit"/"4-8 jam") → `durasi_per_kali_mean` bias diam-diam | web-app (+ keputusan data backend) | Langkah 1 (tutup kebocoran `disabled`) siap dieksekusi; Langkah 2 (semantik durasi standar: `std_durasi_per_kali` teks bebas vs field numerik menit) **butuh keputusan produk** | — |
| [035](backlog/035-web-app-403-500-tampil-sebagai-crash.md) | Web app: 403 & 500 dari backend tampil sbg crash "Server Components render", bukan pesan. Non-anggota panel buka Tahap 2 → crash (otorisasi BENAR, pesannya salah); sesi ber-500 → **tombol "Hapus paksa" ikut hilang** ⇒ admin terkunci dari UI-nya sendiri | web-app | Siap dieksekusi. Mode hanya-baca anggota panel terverifikasi **sudah bekerja** (jangan diregresikan) | — |
| [034](backlog/034-web-app-opm-jabatan-id-mentah.md) | OPM: kolom "Jabatan" di `/opm` & `/opm/{id}` menampilkan **ID mentah** (`jbt_16548582`), bukan nama jabatan — kelas bug yang sama dgn 022 (DCS/WCP), OPM terlewat | backend / web-app | **Tidak terreproduksi 2026-07-14/15** — 2 sesi OPM baru pasca-fix 023 menampilkan nama jabatan dgn benar di `/opm` & `/opm/{id}`. Sisa: pesan error 409 (poin 3) belum diverifikasi ulang — belum ditutup tuntas | — |
| [036](backlog/036-web-app-manifest-pwa-gagal-parse.md) | Web app: `manifest.webmanifest` ditolak browser (`Syntax error`) di **tiap** halaman → app **tidak installable sbg PWA**, padahal berkasnya JSON valid (200, tanpa BOM) via `curl` ⇒ diduga negosiasi RSC/`Vary: rsc` atau middleware. Backlog 010 pernah menyentuh area ini ⇒ mungkin regresi | web-app | Siap dieksekusi (Langkah 1 = intersep respons yang benar-benar diterima browser; jangan menebak) | — |
| [041](backlog/041-web-app-helpdesk-chatwoot.md) | Web app: widget **helpdesk Chatwoot** "Butuh Bantuan?" (fitur baru; nol elemen chat saat ini). Sisip via komponen Client di `(auth)/layout`, env `NEXT_PUBLIC_CHATWOOT_*`. Tak ada CSP di app hari ini (catat bila Traefik menambah) | web-app | **Menunggu input user**: URL instance + website token Chatwoot; opsi widget di halaman login & `setUser` | — |
| [042](backlog/042-docs-langkah-membuat-koordinator.md) | Dokumentasi: tambah **langkah menetapkan Koordinator SME Panel** (fitur UI sudah ada di 2 titik: `SetKoordinatorButton` level panel & `AturKoordinator` level sesi) ke `docs-usage/ik/`. Eksekusi lewat skill `dokumentasi-penggunaan` (folder milik skill itu) | web-app (docs) | Siap dieksekusi | — |
| [044](backlog/044-backend-verifikasi-analisis-dcs-wcp-vs-excel.md) | Verifikasi rumus DCS/WCP vs Excel instrumen awal. **Hasil: COCOK 100%** — 42 item DCS (arah F/UF), 72 item WCP (reverse R/R*/UF), subskala/dimensi/ambang/K-Index identik. Sisa: 2 nilai turunan (ambang interpretasi WCP, normalisasi K-Index) yang Excel tak definisikan | backend | **Verifikasi inti selesai, ditutup tanpa perubahan kode**; 2 nilai turunan menunggu keputusan | — |
| [045](backlog/045-mcp-selaraskan-buat-ti-sesi-cabang.md) | MCP: selaraskan `buat_ti_sesi` (`periode`→`cabang`) & docstring `ti_tambah_responden_banyak` (hapus `kapasitas_penuh` dari daftar alasan skip TI) — konsekuensi kontrak 037 | mcp | Siap dieksekusi (037 sudah selesai) | 037 |
| [047](backlog/047-mcp-dcs-wcp-reset-instrumen.md) | MCP: tool baru `dcs_reset_instrumen`/`wcp_reset_instrumen` — expose endpoint reset admin dari 043 (destruktif: hapus semua responden+jawaban, status→OPEN) | mcp | Siap dieksekusi — endpoint backend 043 sudah ada (`openapi.json` punya `dcs_instrumen_reset`/`wcp_instrumen_reset`) | 043 |
## Selesai

| ID | Item | Repo | Status | Blocked by |
|---|---|---|---|---|
| [043](backlog/043-backend-dcs-wcp-buka-ulang-dari-analyzed.md) | DCS/WCP terkunci **ANALYZED** (terminal) → tak bisa mulai data asli. **Keputusan user 2026-07-15: Opsi (b)** — endpoint admin `POST .../instrumen/reset` (hapus semua responden+jawaban, status→OPEN) dalam satu transaksi | backend | Selesai (kode) 2026-07-15 — `POST /api/v1/{dcs,wcp}/instrumen/reset` (`_ADMIN_GUARDS`) baru di kedua modul: `Sql{Dcs,Wcp}InstrumenService.reset()` bulk-delete `{Dcs,Wcp}RespondenModel` via `session.query(...).delete()` (meniru pola `purge_catalog()`, BUKAN lewat `RespondenService.delete()` per-baris yang menolak baris `sudah_submit`), lalu `status→OPEN`/`closed_at→NULL` — sah dari status APA PUN (idempoten), melewati `_VALID_TRANSITIONS` sepenuhnya. `/buka-ulang` biasa **tidak berubah** (tetap hanya `CLOSED→OPEN`, tanpa hapus data; diverifikasi tetap 422 dari `ANALYZED`). `InMemory{Dcs,Wcp}InstrumenService` sengaja tidak mengimplementasikan `reset()` (pola sama dgn `create_banyak` yg juga tak diimplementasi in-memory). `logger.warning` mencatat aktor. 10 test baru (5×2 modul): reset dari ANALYZED→OPEN+responden kosong, idempoten dari OPEN, non-admin→403, tanpa token→401, buka-ulang biasa tetap 422 dari ANALYZED. `make test` hijau **638 test**; `openapi.json` diregenerasi (gitignored) — 2 operasi baru, breaking-additive. CHANGELOG.md & CLAUDE.md (entri Revisi Desain) diperbarui. Belum di-commit. **Kebutuhan 1 (data-ops)** — reset data uji coba DCS produksi (3 responden test run 2026-07-14) — **belum dieksekusi**: butuh deploy dulu, lalu `make backup` + panggil endpoint di produksi atas instruksi eksplisit user | — |
| [046](backlog/046-web-app-dcs-petunjuk-pengisian-popup.md) | Web app: **pop-up petunjuk pengisian DCS** bergaya instrumen psikologi (pengantar 3 aspek Demand/Control/Support, makna skala 1–5, cara menjawab, 2 contoh non-interaktif). Modal hand-rolled (tanpa dependency baru — tak ada shadcn/radix di repo), auto-buka tiap buka halaman isi saat `!sudah_submit` + tombol "Petunjuk Pengisian" utk buka ulang. Hanya DCS; `dcs-form.tsx` tak disentuh | web-app | Selesai 2026-07-15 — komponen baru `petunjuk-dcs.tsx` (hand-rolled, tanpa portal, meniru pola overlay `app-shell.tsx`), props `{defaultOpen}`; disisipkan ke `page.tsx` di blok header (`<PetunjukDcs defaultOpen={!responden.sudah_submit} />`); `dcs-form.tsx` tak disentuh. Konten: pengantar 3 aspek, petunjuk umum, skala 1–5, cara menjawab, 2 contoh non-interaktif (ilustrasi statis meniru gaya pil `dcs-form.tsx`). Test baru `src/test/petunjuk-dcs.test.tsx` (7 test). `make test` hijau (lint+typecheck+242 test/39 file di Docker), `npm run build` sukses. `docs-usage/ik/dcs.md` bagian E diperbarui; `CHANGELOG.md` & `CLAUDE.md` (web-app, entri Revisi Desain) diperbarui. Belum di-commit | — |
| [040](backlog/040-web-app-tahap3-hapus-ai-dcs-frekuensi-dropdown.md) | Web app Tahap 3: (L1) Frekuensi `frekuensi_teks` teks→**dropdown** `{Harian, Mingguan, Semesteran, Insidental}` + fallback nilai lama — **independen**; (L2) hapus dropdown AI Mode & checkbox Risiko DCS dari form Tahap 3 + master `uraian-tugas-form` + kolom `dcs_flag_count` di hasil. `ai_mode_dist` tak ada di web-app | web-app | Selesai 2026-07-15 — **L1 (Frekuensi) sudah selesai lebih dulu** (sesi sebelumnya): `FREKUENSI` (`Harian`/`Mingguan`/`Semesteran`/`Insidental`) di `calhr.ts`, `<select>` di `detail-form.tsx` & `uraian-tugas-form.tsx`, `frekuensi_teks`/`std_frekuensi_teks` **tetap `string`** (bukan enum) dengan fallback nilai lama di luar 4 opsi. **L2 (AI/DCS) dikerjakan sesi ini** menyusul backend 039 mendarat: `AI_MODE` & `ai_mode`/`dcs_flag`/`std_ai_mode`/`std_dcs_flag` dicabut tuntas dari `detail-form.tsx` (zod, `RowState`, `punyaStandar`, seed, `buildDetailPayload`, render `<select>` AI Mode + checkbox "Ada risiko DCS"), `uraian-tugas-form.tsx` + `[id]/page.tsx` (form & defaultValues standar), kolom "DCS" (`dcs_flag_count`) dicabut dari Hasil Agregasi (`[sesi_id]/page.tsx`), `export const AI_MODE` dihapus dari `calhr.ts` setelah pemakaian nol. `npm run gen:api` dijalankan ulang atas `openapi.json` ber-039 (0 hasil `ai_mode`/`dcs_flag` di schema.ts); blok re-export manual di akhir `schema.ts` ditambal ulang. Test disesuaikan (`taskinv-form-schema.test.ts`, `detail-form-default-unchecked.test.tsx`); `tahap3-data.test.ts` tak perlu diubah. `grep -rn "ai_mode\|dcs_flag\|AI_MODE" src` → **nol hasil**. `make test` hijau (lint+typecheck+235 test/38 file di Docker), `tsc --noEmit` hijau, `npm run build` sukses. `docs-usage/ik/task-inventory.md` & `docs-usage/sop/pelaksanaan-task-inventory.md` disesuaikan (baris AI Mode/Risiko DCS dihapus). CHANGELOG.md & CLAUDE.md (repo web-app) diperbarui. Belum di-commit | 039 (hanya L2) |
| [039](backlog/039-backend-hapus-ai-mode-dcs-flag.md) | Backend: **hapus tuntas** `ai_mode` (+enum `AiMode`) & `dcs_flag` dari CalHR — detail Tahap 3, master data (`std_ai_mode`/`std_dcs_flag`), agregasi (`analisis.py`, `hasil.py:ai_mode_dist`/`dcs_flag_count`), model ORM + migrasi DROP 4 kolom/2 tabel, regen `openapi.json`. Enum `AiMode` nol pemakai luar → aman dihapus | backend | Selesai 2026-07-15 — 4 kolom dihapus (`ti_detail.ai_mode`/`.dcs_flag`, `ti_uraian_tugas.std_ai_mode`/`.std_dcs_flag`), enum `AiMode` (`schemas/calhr.py`) dihapus total (0 importer tersisa, terverifikasi grep), `TiDetailItem`/`Read`, `TiCatalogRead`, `UraianTugasCreate`/`Update`/`Read`, `TiHasilTaskRead.ai_mode_dist`/`.dcs_flag_count`, `TiTaskTerpilihRead.std_ai_mode`/`.std_dcs_flag` semua dibersihkan; `va_type`/`va_type_dist`/`std_va_type` **tidak disentuh**. Migrasi Alembic `fd3dd550aa99` dirantai setelah `08b6b999ee05` (037) via `make migration` (autogenerate, bukan hardcode); `downgrade()` diberi `server_default` sementara utk `ti_detail.ai_mode`/`dcs_flag` (semula `NOT NULL` tanpa default) agar `ADD COLUMN` tak gagal di tabel berisi. Test lama disesuaikan (`test_taskinv.py`, `test_taskinv_master.py` — enum-invalid dialihkan ke `std_va_type`, `test_sesi_cascade.py`) + test baru `test_detail_ai_mode_dcs_flag_ditolak_sebagai_field_asing` (2 param, `422` `extra="forbid"`). `make test` hijau **628 test**; `openapi.json` diregenerasi & diverifikasi bersih (`grep -i "ai_mode\|dcs_flag" openapi.json` → nihil). Versi bump `0.35.0`→`0.36.0`. **Data produksi**: DROP kolom akan menghapus `ai_mode`/`dcs_flag` data uji coba TI Teranalisis YPII secara permanen saat migrasi benar-benar dijalankan di produksi (bukan dijalankan sekarang, hanya di test harness Docker) — backup wajib sebelum itu. Breaking change → 040 (web-app, L2) siap dieksekusi. Belum di-commit | 037 |
| [038](backlog/038-web-app-tisesi-form-cabang.md) | Web app: form "Mulai Analisis Jabatan" TI — Periode→dropdown Cabang, hapus input Min/Maks responden (+ `SmePanelInfo` dari form TI; komponen tetap dipakai OPM), listing kolom Periode→Cabang, regen `schema.ts` | web-app | Selesai 2026-07-15 — `TiSesiCreate.cabang` wajib (enum `Bandung`/`Semarang`); `TiSesiRead`/`Update.cabang` opsional (2 sesi lama `NULL`, tanpa backfill). Form `ti-sesi-form.tsx`: Periode→dropdown Cabang wajib; `min_responden`/`max_responden`/`.refine` dihapus tuntas; prop `petaAnggota` + `useEffect` prefill panel-aware (030) + `<SmePanelInfo>` dicabut dari form TI (komponen & `sme-panel.ts` tetap dipakai OPM, tidak disentuh). `buat/page.tsx` berhenti fetch `/api/v1/sme-panel`. Listing `/task-inventory`: kolom Cabang, sel `s.cabang ?? "—"`. Konsekuensi kompilasi (bukan perubahan perilaku) di 3 titik lain yang mengonsumsi `TiSesiRead`/`TiKuesionerItemRead`: `task-inventory/[sesi_id]/page.tsx`, kartu TI di `/kuesioner`, label dropdown TI sumber di form OPM (`{t.periode}`→`{t.cabang ?? "—"}`, OPM sendiri tak berubah). Re-export manual `schema.ts` (hilang tertimpa `gen:api`) ditambal ulang. `make test` hijau (lint+typecheck+235 test/38 file di Docker), `npm run build` sukses. Belum di-commit | 037 |
| [037](backlog/037-backend-tisesi-cabang-hapus-responden.md) | TI: ganti `periode`→`cabang` (enum `{Bandung, Semarang}`) + **hapus** `min_responden`/`max_responden` & aturan 422 (dari 028) di TiSesi | backend | Selesai 2026-07-15 — **penyimpangan terkunci user**: kolom `cabang` dibuat `nullable=True` **tanpa backfill** (2 baris `ti_sesi` produksi lama tetap `cabang=NULL`), bukan NOT NULL+backfill paksa seperti rencana awal file. `TiSesiCreate.cabang` tetap wajib (sesi baru); `TiSesiRead`/`Update`/`TiHasilSesiRead`/`TiKuesionerItemRead` jadi `CabangSesi | None`. Cap `max_responden` dicabut total dari lapisan responden TI (`assign_ti_responden_banyak`, `SqlTiRespondenService`, `InMemoryTiRespondenService`, router) — dibuktikan test regresi positif (panel 11 anggota → sesi tetap dibuat, semua jadi responden). Dedup sesi `(jabatan_id, periode)`→`(jabatan_id, cabang)`. Downstream `periode`→`cabang` di `analisis.py`/`hasil.py`/`kuesioner.py`/`taskinv_kuesioner.py` diganti (bukan dihapus). Migrasi Alembic `08b6b999ee05` (nullable, tanpa `UPDATE` data produksi). `make test` hijau **627 test**; `openapi.json` diregenerasi (gitignored, diverifikasi via introspeksi skema — `TiSesiCreate`/`Update`/`Read` kini `cabang`, tanpa `periode`/`min`/`max_responden`). Versi bump `0.34.1`→`0.35.0`. Breaking change → 038 (web) siap dieksekusi + audit MCP `buat_ti_sesi`/`ti_tambah_responden*` menyusul. Belum di-commit | — |
| [023](backlog/023-backend-opm-sesi-hilang-dari-listing.md) | **BLOKIR TOTAL OPM:** create sesi OPM selalu 409 "sesi sudah ada" — **pesannya palsu** | backend | **Selesai & TERVERIFIKASI PRODUKSI 2026-07-14/15 (backend v0.34.1).** Fix persis rencana: (a) `flush()` parent setelah `add(rec)` sebelum auto-responden ber-FK-telanjang; (b) `_flush_checked` kini **hanya** memetakan `UniqueViolation` → 409, `IntegrityError` lain naik apa adanya (500) — pemetaan buta itulah yg menyamarkan `ForeignKeyViolation` jadi "sudah ada" & menyesatkan 2 sesi investigasi. Penyimpangan sadar: flush parent lewat `_flush_checked` (bukan `flush()` telanjang spt TI) agar unique constraint tetap jadi backstop 409 utk **race dua create bersamaan**. **Root cause tambahan — koreksi dokumen sendiri:** bug ini lolos unit test **BUKAN** krn `create_savepoint` (klaim di `CLAUDE.md` [2026-07-13] & backlog ini **KELIRU**), tapi krn **`autoflush`**: prod `sessionmaker(autoflush=False)` vs harness test `autoflush=True` (default) → autoflush diam-diam mem-flush parent saat SELECT snapshot task. Test regresi memakai `db_session.no_autoflush` utk **meniru produksi**; **diverifikasi tidak vakum** — dgn fix dicabut ia gagal dgn bug produksi persis (`ForeignKeyViolation` → `ConflictError "… sudah ada"`) sementara 35 test OPM lain tetap hijau. `make test` hijau **625 test**; `openapi.json` tidak berubah. **Verifikasi produksi**: 2 sesi OPM baru (Koordinator Pramuka, Pembina OSIS) dibuat & dijalankan sampai Teranalisis penuh via Playwright, hasil (mean/SD/badge Selection & Workload Essential) tampil benar — OPM pertama kali sukses end-to-end di proyek ini. **Utang tersingkap:** `_flush_checked` diduplikasi di **11 service**, 10 sisanya masih bisa berbohong dgn cara sama | — |
| [025](backlog/025-backend-endpoint-baca-tanpa-auth.md) | **KEAMANAN:** 32 endpoint GET tanpa guard auth — PII 103 pegawai (`/partisipan`) & hasil DCS/WCP per individu terbuka publik tanpa token | backend | **Selesai — TER-DEPLOY & TERVERIFIKASI DI PRODUKSI 2026-07-14.** Kriteria penerimaannya (bukti `curl` tanpa token → 401) **terpenuhi**: `GET /api/v1/partisipan` → **401** `{"error":"unauthorized","message":"Token tidak ada."}`; idem `/task-inventory/sesi/{id}`, `/task-inventory/sesi/{id}/task-terpilih`, `/dcs/instrumen`. Backend produksi kini `version 0.34.0`. Kebocoran PII **sudah tertutup** — status sebelumnya ("code-complete, menunggu deploy") tidak berlaku lagi | — |
| [031](backlog/031-web-app-telan-senyap-data-pendukung.md) | Web app: `?? []`/`?? null` tersisa di jalur baca **data pendukung** (dropdown jabatan/sekolah/partisipan, label) — di luar cakupan 026; tampil sbg dropdown kosong/label ID mentah tanpa pesan error begitu guard 025 aktif | web-app | Selesai 2026-07-14 — inventarisasi ulang: **29 kemunculan** (bukan ~30), diklasifikasi per kasus, **bukan** dipukul rata. (1) Pendukung→formulir/dropdown (**20 kemunculan, 12 berkas**) → **melempar** `apiErrorDari` — bukan kosmetik: menyimpan form edit dgn pilihan yg hilang **menghapus relasi yg sudah ada** (`jabatan_ids` tugas pokok, jabatan tambahan partisipan). (2) Pendukung→pelabelan saja (`/time-study`, `/partisipan`, `/master-data/sme-panel`) → halaman **tetap dirender** + penanda gagal terlihat: `GagalMuatSebagian` + helper `src/lib/api/pendukung.ts` (`pendukungList`/`bagianGagal`). (3) `data.items ?? []` **setelah** guard throw → default field opsional envelope, bukan penelanan → dibiarkan. 2 pengecualian 404 (026) tak diregresikan. **Grep sekali-pakai ditinggalkan** → jaring pengaman otomatis `src/test/jaring-pengaman-jalur-baca.test.ts` memindai **semua ejaan** sekaligus (`.data ?? []`, `.data?.X ?? …`, `.catch(() => set…)`, klien `api` telanjang) — pola ini kembali 3× justru krn tiap pemberantasan mengejar **satu** ejaan; jaring langsung menangkap **ejaan ke-4** yg lolos dari audit manual 031 sendiri: `?? ([] as SekolahRead[])` di `partisipan/tambah/page.tsx`. `make test` hijau **232 test** (38 file), `npm run build` sukses. Utang: ±20 berkas baca lain masih `toApiError(null, …)` — **melempar** (tak menelan) jadi di luar cakupan, tapi membuang pesan backend & status HTTP. Belum di-commit | — |
| [030](backlog/030-web-app-form-max-responden-sadar-panel.md) | Web app: form "Mulai Analisis Jabatan" (TI & OPM) tidak sadar jumlah anggota panel → admin menabrak 422 `max_responden` tanpa petunjuk | web-app | Selesai 2026-07-14 — `src/lib/sme-panel.ts` (`petaJumlahAnggotaPanel`, membedakan `null`=jabatan belum dipilih dari `0`=jabatan tanpa panel) + `src/components/sme-panel-info.tsx` dipakai identik di TI & OPM; form fetch `/sme-panel`, tampilkan "SME panel: N anggota", **prefill** `max_responden`=N (bukan validasi klien yg menolak submit); default 10 sengaja TIDAK dinaikkan. Bonus (invariant 026): `opm/buat/page.tsx` ketiga fetch-nya dulu `?? []` → kegagalan API tampil sbg dropdown jabatan kosong & "Belum ada Analisis Jabatan TI yang dibekukan" (**informasi palsu**) → kini melempar `apiErrorDari`. Pesan 422 backend sampai utuh + `X-Request-ID` (diuji, bukan diasumsikan). IK `docs-usage/ik/{opm,task-inventory}.md` diperbarui. 13 test baru; `make test` hijau **220 test**, `npm run build` sukses. ⚠️ Efek samping sah: panel < `min_responden` (mis. panel 2, min 3) kini memicu validasi "Maks harus ≥ min" **sejak jabatan dipilih** — konflik konfigurasi nyata yg dulu tersembunyi; admin turunkan `min_responden`. Belum di-commit | — |
| [027](backlog/027-web-app-logout-tidak-akhiri-sesi-sso.md) | Web app: "Keluar" tidak mengakhiri sesi SSO Authentik — pengguna berikutnya auto-login sbg pengguna sebelumnya | — (config Authentik) | Selesai 2026-07-14 — **root cause BUKAN di kode; nol baris diubah.** Hipotesis URL `end-session` salah & `idToken` tak ter-persist **dua-duanya GUGUR** (URL identik dgn metadata OIDC; `id_token_hint` terbukti terkirim). Penyebab asli: provider Authentik `anjab-abk-web` punya 2 `redirect_uris` yang **keduanya bertipe `authorization`**, nol bertipe `logout` → `post_logout_redirect_uri` tak pernah sah, RP-initiated logout tak pernah tuntas. Perbaikan: tambah 2 URI bertipe `logout` (varian dgn & tanpa `/` akhir, krn `matching_mode: strict` & `AUTH_URL` prod tak terbaca) — **aditif**, URI lama utuh. **Diverifikasi di browser produksi**: Keluar → flow invalidasi tuntas → `/dashboard` melempar ke `/login`, bukan auto-login. Tak ada `CHANGELOG`/test (nol kode) — **perbaikan ini rapuh: hidup di Authentik, bukan repo** (lihat Risiko di file) | — |
| [029](backlog/029-web-app-sme-panel-anggota-form-tanpa-token.md) | Web app: `anggota-form.tsx` panggil `/partisipan` tanpa token → **401 senyap** ("Belum ada anggota" pada panel yang berisi) begitu 025 di-deploy | web-app | Selesai 2026-07-14 — **wajib dirilis bersama/ sebelum 025**. `AnggotaSection` kini memakai `withServerAuth(accessToken)` (token sudah tersedia sbg prop, pola sama dgn 3 handler mutasi tetangganya); telan-senyap ganda dibuang → `if (!res.data) throw apiErrorDari(res)` + `notifyGagal` (toast + `X-Request-ID`; bukan `GagalMuat` karena ini komponen KLIEN); state **gagal-muat dipisah** dari state kosong (panel merah, bukan "Belum ada anggota"). Ekspor `api` (klien tanpa Bearer) **dihapus** dari `src/lib/api/client.ts` — pemakaiannya nol setelah perbaikan, jadi pola telanjang tak bisa muncul lagi. Sisir Langkah 3: **nol** temuan lain (hanya 7 komponen klien ber-`useEffect`, 6 di antaranya tak menyentuh API). 5 test regresi baru; `make test` hijau **207 test**, `npm run build` sukses; belum di-commit | — |
| [028](backlog/028-backend-auto-populate-responden-melebihi-max.md) | Backend: auto-populate responden TI diam-diam membuang anggota panel saat panel > `max_responden` (OPM sudah benar) | backend | Selesai 2026-07-14 — **opsi (A) tolak keras** dipilih user: `SqlTiSesiService.create()` melempar `ValidationAppError` → 422 bila `len(panel.partisipan_ids) > max_responden`, pesan & bentuk disalin persis dari `opm/services/sesi_sql.py:167-172`; penolakan terjadi **sebelum** INSERT (tak ada rollback); jalur `assign_ti_responden_banyak` tak disentuh — `kapasitas_penuh` kini mustahil dari jalur ini. 2 test baru + 2 test regresi lama (jabatan tanpa panel / panel kosong → sesi tetap dibuat) tetap hijau; `make test` hijau **623 test**; `openapi.json` TIDAK berubah (422 sudah terdokumentasi, kontrak tetap). Sisa UX → item **030**. Belum di-commit | — |
| [026](backlog/026-web-app-error-api-ditelan-senyap.md) | Web app: Tahap 1/Tahap 3 menelan error API senyap (`?? []`) → tampil "0 task"; non-pemilik dapat digest error mentah | web-app | Selesai 2026-07-14 (helper `apiErrorDari()` + `ApiError.status`; **seluruh 21 kemunculan `?? []` di `src/app`** ternyata data kritis → semuanya diubah melempar, plus 2 `?? null` sekelas (review Tahap 2, hasil TI); 2 pengecualian 404 yang SAH dipertahankan (`/partisipan/saya`, `.../seleksi` kunjungan pertama — melempar di sini akan mematikan alur normal Tahap 1); panel `GagalMuat`/`TidakBerhak` dirender **di server** karena Next.js menyensor `error.message` Server Component sehingga `X-Request-ID` mustahil tampil lewat `error.tsx`; 0-task-final → pesan eksplisit + tombol Kirim nonaktif; `make test` hijau 202 test, `npm run build` sukses; belum di-commit) | — |
| [022](backlog/022-backend-resolusi-jabatan-label-dcs-wcp.md) | Backend: resolusi `jabatan_label` DCS & WCP (bukan salinan ID mentah) | backend | Selesai 2026-07-14 (`JabatanService` disuntik ke `SqlDcsRespondenService`/`SqlWcpRespondenService`, resolusi di `create_banyak()` dgn fallback `NotFoundError`→ID mentah+warning; `create()` sengaja tak disentuh; `make test` hijau 531 test; `openapi.json` diverifikasi tanpa diff via worktree terpisah; belum di-commit) | — |
| [021](backlog/021-web-app-konfirmasi-jalankan-analisis-dcs-wcp.md) | Web app: konfirmasi sebelum "Jalankan Analisis" DCS & WCP | web-app | Selesai 2026-07-14 (`confirm()` native ditambah sbg baris pertama `doAnalisis()` di `dcs/aksi-instrumen.tsx` & `wcp/aksi-instrumen.tsx` dgn teks pesan terkunci; 2 file test baru dari nol; `make test` hijau 186 test, `npm run build` sukses; belum di-commit) | — |
| [020](backlog/020-mcp-selaraskan-dcs-wcp-tambah-responden.md) | MCP: selaraskan `dcs_tambah_responden`/`wcp_tambah_responden` dengan `BulkAssignResult` | mcp | Selesai 2026-07-14 (ditemukan sebagai efek samping audit 018; anotasi tipe `-> dict` + docstring `{created, skipped}` + alasan skip benar untuk 2 tool; `make test` hijau 87 test; belum di-commit) | 018 |
| [019](backlog/019-web-app-assign-responden-dcs-wcp-tampilkan-skipped.md) | Web app: tampilkan responden yang di-skip pada assign DCS & WCP | web-app | Selesai 2026-07-14 (panel ringkasan `created`/`skipped` ditiru persis dari `opm/assign-responden-banyak.tsx`, reuse `formatAlasanSkip`, checkbox skip tetap tercentang; `schema.ts` diregenerasi dari `openapi.json` 018; `make test` hijau 182 test, `npm run build` sukses; belum di-commit) | 018 |
| [018](backlog/018-backend-assign-responden-dcs-wcp-skipped.md) | Backend: assign responden DCS & WCP kembalikan `BulkAssignResult` (dengan `skipped[]`) | backend | Selesai 2026-07-14 (service `responden_create` DCS & WCP diseragamkan dengan pola bulk OPM — idempoten, skip alih-alih menelan; `response_model=BulkAssignResult[...]`; `openapi.json` diregenerasi, breaking change; `make test` hijau 527 test; belum di-commit) | — |
| [017](backlog/017-web-app-notifikasi-simpan-data.md) | Web app: notifikasi sukses/gagal di setiap penyimpanan data (pasang `sonner`; ~55 call site) + perbaikan 6 bug notifikasi-bohong | web-app | Selesai 2026-07-14 (`src/lib/notify.ts` terpusat; ~55 call site di 49 berkas dilengkapi `notifySukses`/`notifyGagal`; 5 bug notifikasi-bohong + 6 `alert()` diperbaiki; jaring pengaman grep nol hasil; `make test` hijau 174 test, `npm run build` sukses; belum di-commit) | — |
| [016](backlog/016-web-app-item-editor-dcs-wcp-tidak-refresh.md) | Web app: editor item DCS & WCP tidak mereload data setelah simpan (perubahan `urutan` tak terlihat) | web-app | Selesai 2026-07-13 (cermin `useState` `rows` dibuang di kedua editor, tabel dirender langsung dari prop `items`, `router.refresh()` dipanggil setelah PATCH sukses; `hapus-penugasan.tsx` diseragamkan; 2 test baru `dcs-item-editor.test.tsx`/`wcp-item-editor.test.tsx`; `make test` hijau 145 test, `npm run build` sukses; belum di-commit) | — |
| [012](backlog/012-web-app-title-halaman-terduplikasi.md) | Web app: title halaman terduplikasi "— ANJAB-ABK — ANJAB-ABK" di 30 halaman | web-app | Selesai 2026-07-13 (akhiran `" — ANJAB-ABK"` dihapus dari 30 string title manual di grup `(auth)`; `master-data/*` & root layout tidak disentuh; `make test` hijau 137 test, `npm run build` sukses; belum di-commit) | — |
| [011](backlog/011-web-app-counter-belum-diputuskan-tahap2-tidak-reaktif.md) | Web app: counter "Belum diputuskan" di header Tahap 2 tidak reaktif saat klik Ya/Tidak | web-app | Selesai 2026-07-13 (counter dipindah ke `review-form.tsx`, memakai state client `belumDiputuskan` sebagai satu-satunya sumber kebenaran; span statis di `page.tsx` dihapus; 4 test baru ditambahkan di `review-form.test.tsx`; `make test` hijau 137 test, `npm run build` sukses; belum di-commit) | — |
| [004](backlog/004-terminologi-ti-opm-analisis-jabatan.md) | Terminologi: "Sesi" → "Analisis Jabatan" di TI & OPM (UI saja) | web-app, mcp | Selesai 2026-07-13 (mayoritas sudah dikerjakan di item 003/007 sebelumnya; sisa 5 occurrence teks terlihat user diperbaiki di web-app + 3 baris `docs-usage/`; docstring tool MCP TI/OPM diaudit ulang — sudah lengkap sejak sebelumnya, nol perubahan kode di mcp; `make test` hijau web-app 133 test & mcp 87 test, `npm run build` sukses; belum di-commit) | — |
| [015](backlog/015-backend-otorisasi-sesi-opm.md) | Backend: tutup lubang otorisasi endpoint sesi/hasil OPM | backend | Selesai 2026-07-13 (`make test` hijau, 522 test; `openapi.json` diregenerasi — hanya `security`/401/403/summary baru; lapis 2 hanya `GET /sesi/{id}/task` sesuai spesifikasi; belum di-commit) | — |
| [014](backlog/014-backend-otorisasi-sesi-ti.md) | Backend: tutup lubang otorisasi endpoint sesi/hasil/tahap2 TI | backend | Selesai 2026-07-13 (`make test` hijau, 500 test; `openapi.json` diregenerasi — hanya `security`/401/403 baru; Langkah 3 dieksekusi opsi (a): `GET /sesi/{id}/responden` direlaksasi ke admin/peserta; belum di-commit) | 013 |
| [005](backlog/005-backend-bulk-penugasan-alat-ukur.md) | Backend: penugasan massal (bulk) partisipan untuk TS, TI, OPM + auto-assign SME panel di TI | backend | Selesai 2026-07-13 (`make test` hijau, 471 test; belum di-commit) | — |
| [006](backlog/006-mcp-bulk-penugasan-alat-ukur.md) | MCP: expose penugasan massal (bulk) TS/TI/OPM + tool tambah responden OPM | mcp | Selesai 2026-07-13 (`make test` hijau, 87 test; belum di-commit) | — |
| [008](backlog/008-backend-koordinator-ti-sesi-dari-panel.md) | Backend: koordinator sesi TI otomatis diwarisi dari SME panel | backend | Selesai 2026-07-13 (`make test` hijau, 475 test; belum di-commit) | — |
| [009](backlog/009-web-app-perbaikan-ui-alur-3-tahap-ti.md) | Web app: perbaikan label & teks UI TI (sisa migrasi alur 2 → 3 tahap) + semantik dialog transisi | web-app | Selesai 2026-07-13 (`make test` hijau 133 test, `npm run build` sukses; verifikasi e2e/Playwright sengaja dilewati; belum di-commit) | — |
| [010](backlog/010-web-app-middleware-aset-publik-prefetch-logout.md) | Web app: middleware menelan aset PWA (manifest/sw), link "Keluar" di-prefetch | web-app | Selesai 2026-07-13 (logout diubah GET→POST karena GET destruktif; `make test` hijau, `npm run build` sukses; verifikasi e2e/Playwright sengaja dilewati; belum di-commit) | — |
| [001](backlog/001-backend-hapus-sesi-dcs-wcp.md) | Backend: hapus sesi DCS & WCP → instrumen singleton + penugasan langsung | backend | Selesai (commit `2b7d706`, di luar sesi ini) | — |
| [013](backlog/013-backend-ti-enrollment-hanya-anggota-sme-panel.md) | Backend: enrollment TI hanya anggota SME panel (hapus auto-enroll universal di `/kuesioner/saya`) | backend | Selesai 2026-07-13 (`make test` hijau, 478 test; belum di-commit) | — |
| [002](backlog/002-mcp-selaraskan-tool-dcs-wcp.md) | MCP: selaraskan tool DCS & WCP dengan model tanpa sesi | mcp | Selesai (commit `63527a8`, di luar sesi ini) | — |
| [003](backlog/003-web-app-hapus-ui-sesi-dcs-wcp.md) | Web app: hapus UI sesi DCS & WCP, tambah halaman hasil agregat | web-app | Selesai (commit `13ac956`, di luar sesi ini) | — |
| [007](backlog/007-web-app-bulk-penugasan-alat-ukur.md) | Web app: UI penugasan massal (bulk) TS/TI/OPM, berdampingan dengan form single | web-app | Selesai (commit `9a2375d`, di luar sesi ini) | — |

---

## Konteks lintas-item: asal item 021–022 (simulasi SOP DCS end-to-end)

Item 021 dan 022 lahir dari **simulasi end-to-end SOP Persiapan + Pelaksanaan DCS** via Playwright
di deployment YPII (`anjab-abk.cantum-ypii.com`, 2026-07-14) — 3 partisipan sungguhan (A. Widjianto,
Agustina Megawati Siahaan, Agustinus Purnomo) di-assign sebagai responden, mengisi 42 item jawaban
acak, hingga instrumen ditutup dan dianalisis, dipandu `docs-usage/sop/persiapan-dcs.md` dan
`pelaksanaan-dcs.md`.

Alur inti **terbukti benar end-to-end**: instrumen singleton (status Terbuka→Tertutup→Teranalisis)
berjalan sesuai dokumentasi, draft-save (`Simpan`) persisten lintas reload, validasi "semua item
wajib sebelum kirim final" bekerja, hasil agregat (mean/stdev/Cronbach α per sub-skala, K-Index
menunggu WCP) tampil sesuai spesifikasi.

Dua celah nyata ditemukan di lapisan sekitarnya:

- **021**: tombol "Jalankan Analisis" — satu-satunya aksi yang dokumentasinya sendiri menyebut
  "tidak dapat dibatalkan" — tidak punya `confirm()`, berbeda dari "Tutup Pengisian" di komponen
  yang sama yang sudah dijaga dengan benar.
- **022**: kolom Jabatan di tabel Daftar Responden & halaman hasil-responden menampilkan ID
  internal mentah (`jbt_xxxxx`) alih-alih nama jabatan — ini sudah diketahui & sengaja ditunda sejak
  revisi `[2026-07-12]` `CLAUDE.md` backend ("di luar lingkup revisi ini"), item ini menuntaskannya.

Sebagai efek samping pengujian: instrumen DCS produksi sempat diubah `min_responden` 6→3 (dikembalikan
ke 6 setelah selesai) dan kini berstatus **Teranalisis** dengan data uji coba dari 3 partisipan di
atas — bukan data DCS asli. Lihat "Risiko & catatan" di masing-masing file 021/022.

**Kedua file diperketat lewat verifikasi kode langsung (2 Explore agent terpisah)** sebelum
dianggap "Siap dieksekusi", atas permintaan eksplisit user agar bisa dijalankan Sonnet tanpa
interpretasi ulang. Temuan yang mengoreksi draf awal: 021 ternyata tidak punya test existing sama
sekali untuk `aksi-instrumen` (dua file test baru harus dibuat dari nol, bukan diperluas) dan teks
pesan `confirm()` dikunci eksplisit di file (bukan placeholder); 022 ternyata TIDAK punya jalur
single-assign yang hidup sama sekali untuk DCS/WCP (method `create()` adalah kode Protocol yang
tidak terpakai — premis awal "verifikasi juga jalur single-assign" gugur), dan ditemukan konflik
arsitektur nyata (pola OPM yang melanggar aturan cross-domain repo sendiri vs. pola seam Service
yang konsisten) yang harus diputuskan eksplisit di file — dipilih pola kedua (suntik
`JabatanService` via DI yang sudah ada), bukan meniru OPM.

**Re-verifikasi 022 (2026-07-14, Explore agent independen kedua)**: seluruh 8 klaim "Kondisi
sekarang" di file 022 dicek ulang terhadap kode sungguhan — **8/8 cocok persis**, tidak ada baris
bergeser atau kode berubah. Satu presisi dikoreksi (bukan kesalahan fakta besar): deskripsi
pemakaian fixture `jabatan_id_tk` semula menyebut `test_opm_responden.py` memakainya "via
`partisipan_factory(...)`-style override" — faktanya file itu memakai helper terpisah
`_buat_partisipan()` di `tests/_opm_common.py`, bukan `partisipan_factory` sama sekali. File 022
sudah diperbarui agar eksekutor tidak mencari pemanggilan yang tidak ada.

**Simulasi SOP WCP terpisah (2026-07-14)** mengulang simulasi di atas khusus untuk WCP (3 responden
uji coba yang sama, 72 item jawaban acak) dan **mereproduksi persis kedua gejala 021/022** —
tidak ada temuan baru, hanya menguatkan cakupan "DCS dan WCP" yang sudah dikunci di kedua file.
Alur inti WCP juga **terbukti benar end-to-end**: instrumen singleton, draft-save (`Simpan`)
persisten lintas reload, validasi "semua item wajib sebelum kirim final", hasil agregat per
dimensi (mean/stdev/Cronbach α + interpretasi CUKUP/PERLU PERHATIAN/WASPADA untuk dimensi risiko)
tampil sesuai `docs-usage/sop/persiapan-wcp.md` & `pelaksanaan-wcp.md`. Detail lengkap di memory
`wcp-test-run-2026-07-14`.

---

## Konteks: asal item 023 (simulasi SOP TI + OPM end-to-end)

Item 023 lahir dari **simulasi end-to-end SOP Persiapan + Pelaksanaan Task Inventory (TI) dan
OPM** di deployment YPII (`anjab-abk.cantum-ypii.com`, 2026-07-14, via Playwright), memakai 3
partisipan asli (Theresia Avila Yuanita W, Yayuk Tri Wahyuni, Y. Krisdiantoro Setyawan; lalu
Vinantius Sutarno & V. Gandono utk percobaan ke-3) di 3 SME panel berbeda (Pembina OSIS, Guru
Mapel SMP, Koordinator Pramuka).

**Alur TI terbukti benar end-to-end untuk ketiga jabatan**: auto-populate responden dari SME
panel saat sesi dibuat, koordinator sesi otomatis diwarisi dari koordinator panel (fitur 008),
partisipan yang jadi anggota 2 panel sekaligus (Theresia) berhasil mengisi Tahap 1 terpisah utk
tiap panel (sesuai tip SOP), cascade 3-langkah (Tugas Pokok → Detil Tugas → Uraian Tugas)
menyaring dengan tepat, review koordinator Tahap 2 (Ya/Tidak per task partial) tersimpan benar,
pembekuan Tahap 3 (unanimous ∪ disetujui koordinator) akurat, isian CalHR (termasuk toggle
"Setuju dengan isian standar" acak) tersimpan, dan hasil agregasi (jam/minggu, jam/tahun, badge
DCS) tampil sesuai `docs-usage/sop/persiapan-task-inventory.md` &
`pelaksanaan-task-inventory.md`. Tidak ada bug baru ditemukan di alur TI.

**Alur OPM gagal total** — lihat detail lengkap di **023**. Percobaan pertama (Pembina OSIS,
Guru Mapel SMP) awalnya diduga tersisa data lama dari studi sebelumnya (409 "sesi sudah ada"
padahal tidak muncul di listing `/opm`); untuk memastikan bukan kebetulan, dicoba jabatan
ketiga (Koordinator Pramuka) dengan TI yang **dibuat & dianalisis dari nol di sesi yang sama**
— 409 yang sama tetap muncul, menaikkan status dari "mungkin data lama" ke **bug sistemik yang
memblokir pembuatan Analisis Jabatan OPM untuk jabatan apa pun**. Review kode (frontend +
backend, via Explore agent) tidak menemukan cacat logika di listing maupun constraint create —
akar masalah kemungkinan di luar apa yang bisa diverifikasi lewat pembacaan kode statis (lihat
"Kemungkinan penyebab" di 023), termasuk temuan sampingan yang mencurigakan: `GET /openapi.json`
produksi melaporkan versi backend `0.26.0`, jauh di belakang `CHANGELOG.md` repo (`0.33.0`
Unreleased), padahal fitur dari rilis setelahnya (auth guard sesi TI, pewarisan koordinator)
terbukti aktif di produksi.

Detail lengkap simulasi (ID sesi TI test, partisipan yang dipakai, kredensial yang diakses) ada
di memory project `ti-opm-test-run-2026-07-14` — **jangan** asumsikan 3 sesi TI produksi yang
dipakai (Pembina OSIS, Guru Mapel SMP, Koordinator Pramuka) bersih dari data uji coba.

---

## Konteks lintas-item: asal item 017–020 (notifikasi + skip DCS/WCP)

Item 017 (audit notifikasi ~55 call site web app) dan 018 (backend `BulkAssignResult` DCS/WCP)
independen satu sama lain dan dieksekusi paralel 2026-07-14. Item 019 menyusul keduanya (butuh skema
018 + helper `notify.ts` dari 017, dan menyentuh 2 file yang sama dengan langkah terakhir 017 —
`dcs/assign-responden.tsx` & `wcp/assign-responden.tsx` — sehingga sengaja dijalankan sekuensial
setelah 017 selesai, bukan paralel).

**020 lahir sebagai temuan sampingan saat mengeksekusi 018**: agen pelaksana 018 mengaudit
`anjab-abk-mcp` (sesuai instruksi "satu item = satu repo" di file backlog-nya) dan menemukan
`dcs_tambah_responden`/`wcp_tambah_responden` masih bertipe kembali `list` dengan docstring yang
menjanjikan "daftar responden" — kontrak itu jadi stale begitu 018 mengubah response backend menjadi
objek `{created, skipped}`. Perbaikannya kecil (anotasi tipe + docstring + 2 test) sehingga langsung
dieksekusi di sesi yang sama alih-alih ditinggalkan sebagai item "Aktif" terpisah.

**Belum di-commit** — keempat item mengubah tiga repo berbeda (`anjab-abk-backend`,
`anjab-abk-web-app`, `anjab-abk-mcp`). 018 adalah breaking change; 018+019 harus dirilis bersama
(lihat catatan risiko di masing-masing file), dan 020 idealnya ikut rilis yang sama karena
mendokumentasikan kontrak yang sama.

---

## Konteks lintas-item: asal item 008–010 (simulasi TI end-to-end)

Item 008, 009, dan 010 lahir dari **satu simulasi end-to-end Task Inventory** di deployment YPII
(`anjab-abk.cantum-ypii.com`, 2026-07-13) — dari persiapan admin sampai pengisian partisipan, memakai
panel Koordinator Sarana Prasarana (3 anggota, katalog 49 uraian tugas).

Alur intinya **terbukti benar**: responden auto-terisi dari SME panel, kaskade Tahap 1 menyaring dengan
tepat, hitungan task partial akurat (14 partial: 13× 1/3, 1× 2/3), pembekuan Tahap 3 menghasilkan tepat
11 task = 8 unanimous ∪ 3 disetujui koordinator, dan agregasi keluar konsisten (13 jam/minggu,
585 jam/tahun). Yang cacat adalah **lapisan di sekitarnya** — pewarisan koordinator (008), label & teks
UI sisa migrasi 2→3 tahap (009), dan aset PWA/logout (010). Tidak ada temuan yang menyentuh logika
agregasi maupun state machine.

---

## Konteks lintas-item: asal item 011–012 (simulasi TI end-to-end #2)

Item 011 dan 012 lahir dari **simulasi end-to-end Task Inventory kedua** di deployment YPII
(`anjab-abk.cantum-ypii.com`, 2026-07-13), memakai panel Kepala Sekolah (7 anggota, katalog
105 uraian tugas) — dijalankan setelah item 008–010 dirilis (v4.0.0) untuk memverifikasi rev
terbaru.

Alur inti kembali **terbukti benar**: responden & koordinator otomatis terisi dari SME panel
(008 terkonfirmasi bekerja), kaskade Tahap 1 menyaring 4 unanimous + 6 partial dengan tepat,
review koordinator Tahap 2 menghasilkan 3 disetujui + 3 ditolak sesuai input, pembekuan Tahap 3
tepat 7 task = 4 unanimous ∪ 3 disetujui, dan agregasi konsisten (7 jam/minggu, 315 jam/tahun).

Dua gejala tambahan sempat teramati di live site tapi **ternyata sudah diperbaiki di kode HEAD**
(commit `61b75876`/v4.0.0, sesuai `CHANGELOG.md`) — bukan item backlog, melainkan indikasi
**deployment lag** (image produksi belum di-redeploy dari commit terbaru):
- `/manifest.webmanifest` mengembalikan HTML shell alih-alih JSON manifest — matcher
  `src/middleware.ts` versi HEAD sudah benar mengecualikan path ini; gejala cocok dengan
  matcher versi sebelum commit 61b75876.
- UI tidak refresh otomatis setelah transisi tahap (Tahap1→2, Tahap2→3, Tutup Analisis) — kode
  `transisi-sesi.tsx` sudah memanggil `router.refresh()` di ketiga aksi sejak commit awal modul.

Dua temuan lain **terkonfirmasi nyata di kode HEAD** dan dijadikan item backlog 011 (counter
Tahap 2 tidak reaktif) dan 012 (title halaman terduplikasi, 30 file).

---

## Konteks lintas-item: asal item 013–015 (audit otorisasi TI & OPM)

Item 013, 014, dan 015 lahir dari **audit otorisasi Task Inventory** (2026-07-13), dipicu laporan bahwa
partisipan masih bisa melihat sesi TI yang bukan diassign ke dia — lalu diperluas ke OPM.

Gejala yang dilaporkan ternyata **bukan** kebocoran lewat tebak-ID, melainkan perilaku yang memang
ditulis: `GET /task-inventory/kuesioner/saya` mencari **semua** sesi aktif tanpa filter partisipan,
lalu memanggil `ensure_for_partisipan()` yang **meng-INSERT** baris responden untuk tiap sesi. Ini
sisa desain lama — DCS/WCP/OPM sudah assignment-based, TI tertinggal. Revisi `[2026-06-21]` di
`CLAUDE.md` backend bahkan sudah mengklaim TI assignment-based, padahal **tidak pernah begitu di
kode**. Itu item **013**.

Audit yang sama menemukan lubang yang lebih parah dan tidak dilaporkan siapa pun: **seluruh otorisasi
sesi TI ada di frontend, backend tidak menegakkan apa pun.** Tidak ada middleware auth global, jadi
enam endpoint (daftar sesi, detail sesi, review Tahap 2, task-terpilih, hasil) terbuka **tanpa token
sama sekali**; dan tujuh endpoint lain hanya bertoken tanpa cek peran — sehingga **partisipan biasa
bisa menjalankan state machine sesi milik siapa pun**, termasuk `mulai-tahap3` yang membekukan task
secara tak-reversibel. Itu item **014**.

Urutannya mengikat: **014 blocked by 013**. Selama auto-enroll universal masih hidup, semua partisipan
adalah responden semua sesi, sehingga guard "admin ATAU peserta sesi ini" di 014 tidak menyaring apa
pun dan test-nya lolos secara palsu.

**OPM lalu ikut diaudit (item 015).** Hasilnya: OPM punya **lubang sesi-level yang sama persis dengan
TI** — sebagian endpoint terbuka tanpa token, sebagian bertoken tanpa cek peran, sehingga partisipan
biasa bisa membuka/menutup sesi OPM siapa pun dan menjalankan analisisnya. Tapi OPM **sehat di dua sisi
yang justru rusak di TI**: enrollment-nya sudah assignment-based (`list_by_partisipan`, tidak ada
auto-enroll universal — jadi **tidak ada padanan item 013 untuk OPM**), dan lapisan respondennya sudah
dijaga benar, bahkan lebih ketat dari TI. Karena itu 015 lebih sempit dari 014, tidak diblokir siapa
pun, dan lapis-2 guard-nya hanya menyentuh **satu** endpoint (`GET /opm/sesi/{id}/task` — satu-satunya
endpoint sesi-level di jalur pengisian partisipan). OPM juga tidak punya konsep koordinator, jadi
guard-nya lebih sederhana dari TI.

Satu hal sengaja **tidak** dimasukkan dan menunggu keputusan user: pembersihan baris `ti_responden`
hasil auto-enroll yang sudah terlanjur ada di deployment YPII. Kandidatnya baris yang belum ter-submit
dan partisipannya bukan anggota panel jabatan itu; baris **ter-submit jangan disentuh** karena menjadi
penyebut unanimity Tahap 2, sehingga menghapusnya akan mengubah hasil agregasi sesi yang sudah jalan.

---

## Konteks lintas-item: kenapa sesi DCS/WCP dihapus

Keputusan pemilik produk (2026-07-12): **satu deployment hanya dipakai untuk satu kali studi.**

Konsekuensinya, "sesi" menanggung beban yang sangat berbeda per alat ukur:

| Alat ukur | Isi sesi selain wadah | Sesi sebenarnya = | Nasib |
|---|---|---|---|
| **TI** | `jabatan_id`, `koordinator_id`, `task_frozen`, `task_terpilih`, 6 status | 1 **jabatan** | **Dipertahankan** |
| **OPM** | `jabatan_id` (unique), `ti_sesi_id`, snapshot task | 1 **jabatan** | **Dipertahankan** |
| **DCS** | `periode`, `min/max_responden`, `catatan` | — (singleton terselubung) | **Dihapus** (001) |
| **WCP** | idem DCS | — (singleton terselubung) | **Dihapus** (001) |
| **TS** | _(sudah tanpa sesi sejak migrasi `20260704_0a58616358f4`)_ | — | Jadi acuan pola |

Sesi TI/OPM **bukan** unit studi melainkan unit jabatan — satu studi punya puluhan jabatan, jadi
puluhan sesi. Menghapusnya hanya akan memindahkan `jabatan_id` + state machine + `task_frozen` ke
entitas lain dengan nama berbeda. Yang berubah cuma istilahnya (item 004).

Sesi DCS/WCP tidak terikat jabatan/unit kerja/sekolah sama sekali. Dalam model 1-deployment-1-studi,
akan selalu ada **tepat satu** sesi DCS dan satu sesi WCP. Bukti bahwa ini sudah singleton de facto:
`dcs/services/responden_sql.py` memaksa satu partisipan hanya boleh jadi responden di **seluruh** sesi
DCS (global), bukan per sesi — constraint yang hanya masuk akal kalau memang cuma ada satu sesi.

Yang **tidak** boleh ikut hilang saat sesi dibuang (pelajaran dari Time Study, yang kehilangan status
submit + agregasi saat sesinya dihapus): DCS/WCP tetap butuh (a) `min_responden` sebagai cutoff
analisis, dan (b) momen **penutupan** yang membekukan kohort sebelum Cronbach alpha dihitung. Keduanya
pindah ke satu baris konfigurasi singleton per instrumen, bukan hilang.

---

## Konteks lintas-item: simulasi SOP TI + OPM #3 (2026-07-14) — **status resume**

Item **033–036** lahir, dan root cause **023** & **024** akhirnya terbukti, dari **simulasi
end-to-end SOP Persiapan + Pelaksanaan TI & OPM** via Playwright di produksi YPII
(`anjab-abk.cantum-ypii.com`, backend v0.34.0), dipandu `docs-usage/sop/{persiapan,pelaksanaan}-{task-inventory,opm}.md`.
Data jawaban lama (7 sesi TI + 2 sesi OPM) dihapus lebih dulu atas instruksi user.

### Yang SUDAH selesai — jangan dibangun ulang

**Task Inventory: lolos penuh di 2 panel** (DRAFT → TAHAP1 → TAHAP2 → TAHAP3 → CLOSED → Teranalisis),
3 responden per panel mengisi acak, termasuk review koordinator & agregasi CalHR:

| Sesi TI | ID | Jabatan | Status | Task beku | Koordinator | Responden (3) |
|---|---|---|---|---|---|---|
| 1 | `tises_c456dffb` | Koordinator Pramuka | **Teranalisis** | 7 (1 unanimous + 6 disetujui) | Irwan Faisal | Irwan Faisal, Timotius Iwan Rudiawan, Hendrika Shelin Pratiwi |
| 2 | `tises_cdebca82` | Pembina OSIS | **Teranalisis** | 3 (0 unanimous + 3 disetujui) | Theresia Avila Yuanita W | Theresia Avila Yuanita W, Kusuma Dharma Satrya Dewangga, Marintan Nirmalasari |

Katalog kedua jabatan ini **bersih dari `detil_tugas` NULL** ⇒ **item 024 TIDAK menghalangi OPM.**
Sesi OPM saat ini: **0**.

### Yang BELUM — tes OPM, diblokir 023

Tes berhenti **tepat sebelum OPM**. **Item 023 wajib diperbaiki DAN di-deploy lebih dulu** — tidak ada
jalan memutar: satu-satunya jalur create adalah `POST /api/v1/opm/sesi`, dan jalur itu **selalu**
memicu bug (jabatan tanpa panel/panel kosong ditolak di gerbang; panel berisi → auto-responden dari
panel → `ForeignKeyViolation` → ditelan jadi 409 palsu). Terbukti gagal di 2 jabatan pada sesi ini,
dan ~5 jabatan pada 2 sesi sebelumnya.

**Langkah tes OPM begitu 023 ter-deploy:**

1. `/opm/buat` → Jabatan = Koordinator Pramuka, sumber TI = `tises_c456dffb` ("2026-07 — 7 task"),
   periode `2026-07`. Ulangi utk Pembina OSIS (`tises_cdebca82`, 3 task).
2. Responden OPM **otomatis dari SELURUH anggota SME panel** (masing-masing **5 orang**) — bukan dari
   3 responden TI. Hapus 2 responden berlebih **di sesi OPM** agar tersisa 3 orang yang sama seperti
   tabel di atas. Pastikan `max_responden` ≥ 5 (kalau tidak → 422, lihat item 028/030).
3. Tiap responden: **Kuesioner Saya** → kartu OPM → **Isi Sekarang** → nilai **tiap task** pada 3
   dimensi (Importance/Frequency/Criticality, 1–5) → **Kirim Jawaban**.
4. Admin: **Tutup Analisis** → **Jalankan Analisis** → halaman **Hasil** (mean/SD per dimensi + badge
   Selection Essential / Workload Essential).
5. Sekalian verifikasi **item 034** di sini (kolom "Jabatan" harus nama, bukan `jbt_…`).

### Aturan kerja yang ditetapkan user (mengikat)

**Data SME Panel di produksi JANGAN PERNAH disentuh** — tidak boleh tambah/hapus anggota. Untuk
membatasi jumlah pengisi, hapus **responden di sesi** (data transaksi), bukan anggota panel.
Konsekuensi: karena panel-panel itu anggotanya **disjoint**, skenario "3 partisipan yang sama di 2
panel" (partisipan lintas-panel wajib isi Tahap 1 per panel) **belum pernah teruji** — catat sebagai
lubang cakupan pengujian, bukan sebagai fitur yang sudah terbukti.

### Catatan metodologis (kenapa 2 sesi tes sebelumnya buntu)

Kedua root cause baru ketahuan setelah **endpoint dipanggil langsung dengan token**, bukan didiagnosis
dari layar — UI menyembunyikan status HTTP asli (500 tampil sebagai "0 task"; `ForeignKeyViolation`
tampil sebagai "sesi sudah ada"). Bila UI menunjukkan gejala aneh, **`curl`/API dulu, jangan menebak
dari DOM.**

---

## Konteks lintas-item: asal item 037–044 (feedback tulisan tangan SME, 2026-07-14)

Item **037–044** lahir dari **satu lembar koreksi tulisan tangan** dari user (foto `IMG-20260714-WA0000.jpg`,
2026-07-14), berisi dua blok: "KOREKSI u/ APP — TASK INVENTORY" dan "KOREKSI u/ INSTRUMEN DCS + WCP".
Tiap poin diverifikasi ke kode aktual (5 Explore agent) + runtime (versi backend & status instrumen via
MCP) sebelum dijadikan item. Keputusan produk dikunci lewat tanya-jawab langsung ke user.

### Peta poin feedback → tindakan

| Poin feedback | Verdict verifikasi | Tindakan |
|---|---|---|
| Tahap 2 "Simpan Keputusan" tak ada reaksi | **Sudah ada di kode HEAD** (toast+refresh+loading, test regresi, commit `bc0c8a5`/v4.2.0) | **Deployment lag** — verifikasi versi web-app live & redeploy v4.2.0; opsional penanda "Tersimpan" persisten |
| Hapus Unit/Jenjang dari form TI | **Sudah dihapus** (commit `756ff7e`, 25 Jun, ada di v4.2.0) | Deployment lag — tak ada kode baru |
| Periode → Cabang (Bandung/Semarang) | Perlu backend (periode wajib, tak ada konsep cabang) | **037** (backend) → **038** (web) |
| Hapus Min/Maks responden | Perlu backend (kolom + aturan 422) | **037** (backend) → **038** (web) |
| Helpdesk chatbot "Butuh Bantuan?" | Fitur baru, nol elemen chat | **041** (widget Chatwoot) |
| Langkah membuat Koordinator | Fitur UI ada, dok kurang | **042** (docs) |
| Tahap 3: hilangkan AI mode | `ai_mode` tersebar (form+master+agregasi+enum) | **039** (backend) → **040** L2 (web) |
| Tahap 3: hilangkan Resiko DCS | `dcs_flag` tersebar sama | **039** (backend) → **040** L2 (web) |
| Tahap 3: Frekuensi jadi dropdown | `frekuensi_teks` teks bebas, **tak dipakai agregasi** | **040** L1 (web, independen) |
| DCS/WCP: hasil peserta tak bisa dilihat | **Sudah ada** (link "Lihat Hasil" per responden, gated `sudah_submit`) | Deployment lag / responden belum submit — verifikasi |
| DCS/WCP: pengolahan ikuti Excel awal | **Cocok 100%** (42 DCS + 72 WCP, arah/ambang/K-Index identik) | **044** — ditutup tanpa perubahan; 2 nilai turunan menunggu keputusan |
| WCP tidak bisa buka sesi | **Terkonfirmasi runtime**: WCP & DCS status ANALYZED (terminal), data uji coba 14 Jul | **043** — data-ops reset + keputusan transisi ANALYZED→OPEN |

### Dua akar masalah lintas-poin

1. **Deployment lag (3 poin).** Backend prod = `0.34.1` (= HEAD), tapi 3 keluhan menyangkut perbaikan yang
   **sudah ada di web-app v4.2.0** (Tahap 2 notify, hapus Unit, hasil per-responden). Web-app HEAD = v4.2.0;
   yang live diduga tertinggal. **Aksi termurah pertama: pastikan v4.2.0 benar-benar ter-deploy** — bisa
   menutup 3 keluhan tanpa satu baris kode.
2. **Instrumen DCS/WCP terkunci ANALYZED (poin WCP).** Data uji coba simulasi 14 Jul (tercatat di memory
   `dcs-test-run-2026-07-14` & `wcp-test-run-2026-07-14`). Untuk data asli perlu reset/reopen — lihat 043.

### Ketergantungan & catatan MCP

- Rantai lintas repo: **037→038** (Cabang + hapus responden), **039→040 L2** (hapus AI/DCS). **040 L1**
  (Frekuensi) & **039** & **037** tak saling blok.
- **Utang MCP:** perubahan kontrak 037 (`buat_ti_sesi`: field `periode`/`min`/`max`) sudah jadi item —
  **045**, siap dieksekusi (037 selesai). Perubahan kontrak 039 (`buat_detil_tugas`/`ti_submit_detail`:
  `ai_mode`/`dcs_flag`) **belum** jadi item — audit `anjab-abk-mcp` menyusul rilis backend 039 (pola sama
  seperti item 020 lahir dari 018).
