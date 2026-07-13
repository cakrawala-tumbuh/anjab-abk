# BACKLOG — anjab-abk

Indeks pekerjaan yang **sudah direncanakan tapi belum dieksekusi**, lintas ketiga sub-repo
(`anjab-abk-backend`, `anjab-abk-mcp`, `anjab-abk-web-app`).

Detail tiap item ada di `backlog/<id>-<slug>.md`. Konvensi & cara pakai: lihat bagian
"Backlog" di [CLAUDE.md](CLAUDE.md). Template item baru: [`backlog/TEMPLATE.md`](backlog/TEMPLATE.md).

## Aktif

| ID | Item | Repo | Status | Blocked by |
|---|---|---|---|---|

## Selesai

| ID | Item | Repo | Status | Blocked by |
|---|---|---|---|---|
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
