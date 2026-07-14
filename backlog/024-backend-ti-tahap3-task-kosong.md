# Backlog 024 — TI: Tahap 3 menampilkan 0 task meski Task Terpilih sudah dibekukan

> **Repo:** `anjab-abk-backend` (terkonfirmasi)
> **Status:** **SIAP DIEKSEKUSI** — root cause ditemukan & dibuktikan 2026-07-14 (sesi ketiga)
> lewat panggilan API langsung ber-token. Bukan "0 task" — endpoint `task-terpilih`
> **500 Internal Server Error** karena `detil_tugas` bernilai `NULL` di katalog.
> Lihat "Root cause (2026-07-14, terbukti)" di bawah.
> **Blocked by:** —
> **Skill yang dipakai:** `backend-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## ⚠️ HASIL INVESTIGASI 2026-07-14 — kedua hipotesis GUGUR, nol kode diubah

Investigasi kode menyeluruh (backend + web-app terdeploy) **mengeliminasi kedua hipotesis utama
di bawah dengan bukti**, bukan sekadar "belum terbukti". **Tidak ada kode yang diubah** — menulis
perbaikan di atas dugaan ditolak.

### Hipotesis (b) — INNER JOIN / `detil_tugas_id: null` → **GUGUR**

Tidak ada JOIN yang mengasumsikan `detil_tugas_id` NOT NULL di jalur baca Tahap 3:

- `taskinv/services/catalog.py:148` — `dt = self._dt.get(ut.detil_tugas_id) if ut.detil_tugas_id else None`,
  lalu `detil_tugas=dt.nama if dt else None` (`:157`) ✓ — task ber-`detil_tugas_id` null **dilayani
  normal**, bukan disaring.
- `taskinv/services/analisis.py:32-53` (`compute_task_terpilih`) — bahkan bila entri katalog **hilang
  total**, baris tetap diemit (`tugas_pokok=cat.tugas_pokok if cat else ""`) ✓.
- `api/v1/taskinv_hasil.py:47-54` (`_catalog_map`) menelan exception per-kode → paling buruk **label
  kosong**, bukan **list kosong** ✓.

Task `WK-ALL-PD-001` **tidak bisa** mengosongkan daftar; paling banter muncul tanpa label.

### Hipotesis (a) — guard 403 untuk partisipan → **GUGUR**

- `GET /sesi/{id}/task-terpilih` (`api/v1/taskinv_hasil.py:81`) dan `GET /sesi/{id}`
  (`api/v1/taskinv_sesi.py:161`) memanggil **guard yang identik** dengan service identik:
  `authorize_sesi_access(principal, sesi, par_service, rsp_service)` ✓.
- Halaman Tahap 3 versi **terdeploy** *melempar* bila `GET /sesi/{id}` gagal. Karena halaman
  **berhasil dirender** (nama jabatan, status TAHAP3, form semuanya tampil), `GET /sesi/{id}`
  **sukses** → guard **lolos** → guard yang sama di `task-terpilih` **pasti lolos juga** ✓.
- Test yang sudah ada membuktikannya: `tests/test_taskinv.py:1715` — peserta non-admin
  `GET .../task-terpilih` → **200** ✓.

### Juga tereliminasi

- **TAHAP3 tanpa task beku itu mustahil.** Satu-satunya penulis `status = "TAHAP3"` adalah
  `freeze_task_terpilih` (`taskinv/services/sesi_sql.py:196-202`), yang **menolak `kodes` kosong**
  dan selalu menyetel `task_frozen = True`. `TiSesiUpdate` tidak punya field `status` ✓.
- **422** mustahil (status sesi memang TAHAP3). **429** mustahil (endpoint itu tidak memasang
  `rate_limit`). **500 selektif** mustahil — jalur setelah guard **independen dari principal**,
  jadi admin akan ikut gagal, padahal admin justru dapat 19 task ✓.

### Konsekuensi — premis observasi patut dicurigai

Dengan kode yang **benar-benar berjalan di produksi**, admin dan peserta menerima respons yang
**persis sama** dari `task-terpilih`. Artinya salah satu premis di tabel "Kondisi sekarang" di bawah
**pasti keliru**. Kandidat terkuat (belum dibuktikan): **`responden.sesi_id` dari 7 responden itu
bukan `tises_434a8864`** — mis. baris `ti_responden` warisan **auto-enroll universal lama** (lihat
revisi `[2026-07-13]` soal `/kuesioner/saya`, backlog 013), sehingga halaman Tahap 3 sebenarnya
membaca **sesi lain** yang memang belum punya task.

### Catatan verifikasi produksi

- Tool MCP `mcp__anjab-abk__*` → **401 "Token sudah kedaluwarsa"**. Dilaporkan apa adanya, tidak
  diakali.
- Yang **berhasil** diverifikasi tanpa token: `openapi.json` produksi **identik dengan HEAD
  (v0.33.1)** — jadi analisis kode di atas memang berlaku untuk kode yang berjalan di produksi.
- **KOREKSI PENTING (berdampak ke backlog 023):** `info.version` produksi `0.26.0` **bukan tanda
  deploy tertinggal** — `__version__` **di-hardcode** `"0.26.0"` di
  `src/anjab_abk_backend/__init__.py:3` **di HEAD** dan tak pernah di-bump. Fakta #9 backlog 023
  sudah dikoreksi.

### Langkah decisive berikutnya (murah — kini mungkin berkat 026)

1. **Deploy web-app 026**, lalu buka `/task-inventory/tahap3/{responden_id}` sebagai salah satu
   partisipan sesi itu. Halaman kini menampilkan **kode status + `X-Request-ID`** bila gagal, atau
   panel kuning **"Tidak ada task final"** bila benar-benar `200` + kosong. Itu **langsung
   memisahkan** "gagal ditelan" dari "kosong sungguhan".
2. Bila ternyata `200` + kosong → bandingkan `responden.sesi_id` (via
   `GET /task-inventory/sesi/responden/{id}`) dengan `tises_434a8864` — menguji hipotesis "baris
   responden yatim / sesi salah".
3. Baru setelah itu tentukan repo pemiliknya & perbaikannya.

---

## Catatan asli (dipertahankan sebagai jejak — perhatikan dua hipotesisnya sudah GUGUR)

> **Repo:** `anjab-abk-backend` (dugaan; belum diverifikasi di kode — lihat "Langkah eksekusi")
> **Status:** ~~Menunggu investigasi — BUKAN siap dieksekusi~~
> **Blocked by:** —
> **Skill yang dipakai:** `backend-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Halaman **Isi Tahap 3** (`/task-inventory/tahap3/{responden_id}`) menampilkan **"0 dari 0 task"**
dan daftar task kosong untuk **seluruh responden** dari satu sesi TI (jabatan **Wali Kelas**,
`tises_434a8864`) — padahal halaman detail admin sesi yang sama dengan jelas menunjukkan
**"Task Terpilih: 19"**, dan form "Mulai Analisis Jabatan OPM" berhasil menampilkan sesi ini
sebagai sumber task dengan label **"2026-07 — 19 task"**. Ini membuktikan **task final memang
tersimpan dengan benar** di backend — masalahnya murni di endpoint/query yang dipakai halaman
Tahap 3 partisipan untuk mengambil daftar task yang harus di-detail.

Sesi TI **lain** yang dibuat pada momen yang sama, dengan langkah identik (jabatan **Guru Kelas
SD**, `tises_070c04b0`, 15 task terpilih) **bekerja normal** — partisipan melihat 15 task dan
berhasil mengisi & mengirim detail CalHR. Ini murni bug pada satu sesi/jabatan, bukan kegagalan
alur Tahap 3 secara umum.

## Kondisi sekarang (verified)

Ditemukan saat simulasi ulang end-to-end SOP TI + OPM di produksi (`anjab-abk.cantum-ypii.com`,
2026-07-14, via Playwright), dengan jabatan/panel yang sengaja **baru** (bukan yang dipakai
simulasi TI+OPM sebelumnya hari yang sama — lihat memori `ti-opm-test-run-2026-07-14` dan
backlog 023).

| # | Fakta | Verifikasi |
|---|---|---|
| 1 | `GET /task-inventory/tahap3/{responden_id}` untuk **7 responden berbeda** di sesi `tises_434a8864` (termasuk koordinator `Christmass Jeffri` dan anggota multi-panel `Teresia Dwi Rustini`) — **semua** menampilkan "Ditandai dikerjakan: 0 dari 0 task", `<div class="space-y-4"></div>` benar-benar kosong di DOM (dicek via `outerHTML`), tanpa error/exception di console | ✓ dicek langsung 2 responden (Christmass, Teresia), pola identik |
| 2 | Detail admin sesi (`/task-inventory/tises_434a8864`) menunjukkan **"Task Terpilih: 19"** dan tabel **"Task Relevan Terpilih (19)"** terisi lengkap dengan nama task, tugas pokok, dan persentase relevansi | ✓ snapshot halaman |
| 3 | Form `/opm/buat` dengan Jabatan = **Wali Kelas** menampilkan opsi Analisis Jabatan TI **"2026-07 — 19 task"** — backend query lain yang membaca task final untuk sesi ini **berhasil** mendapat 19 task | ✓ snapshot dropdown |
| 4 | Reload halaman Tahap 3 berulang kali (jeda ~7 menit dari waktu freeze `Mulai Tahap 3`) **tidak mengubah hasil** — bukan race condition/eventual-consistency sesaat | ✓ dicek 3× dengan jeda |
| 5 | Sesi TI lain (**Guru Kelas SD**, `tises_070c04b0`, 15 task terpilih) yang dibuat & dibekukan dengan **langkah identik** (persis pola SOP yang sama, hanya beda jabatan/panel) **bekerja normal** — 2 responden (`E. Diah Ratnawulan`, `Teresia Dwi Rustini`) berhasil melihat 15 task, mencentang, mengisi CalHR (sebagian pakai isian standar, sebagian dikustomisasi), dan **Kirim Detail** sukses; sesi berhasil ditutup & dianalisis sampai **Teranalisis** dengan hasil agregasi lengkap | ✓ end-to-end sukses, dipakai sbg baseline pembanding |
| 6 | Halaman Tahap 3 me-render **dua** blok penghitung "Ditandai dikerjakan: X dari Y task" + tombol Simpan/Kirim Detail (atas & bawah daftar task) — pola ini juga muncul di sesi Guru Kelas SD yang normal, jadi **bukan** bagian dari bug ini, hanya dicatat sebagai desain UI (action bar sticky atas+bawah) | ✓ dicek `outerHTML`, pola sama di kedua sesi |

## PENTING — kenapa bug ini tampil sebagai "0 task" dan bukan pesan error (temuan kode, ✓)

Pembacaan kode setelah item ini ditulis menemukan sebabnya **halaman diam**, terpisah dari
sebab **datanya kosong**:

`src/app/(auth)/task-inventory/tahap3/[responden_id]/page.tsx` mengambil daftar task dengan
`terpilih = (ttRes.data ?? []) as TiTaskTerpilihRead[]` ✓ — **respons gagal apa pun**
(401/403/422/500) berubah jadi array kosong tanpa pesan error. Sementara endpointnya,
`GET /task-inventory/sesi/{sesi_id}/task-terpilih`, **bisa** mengembalikan **403** (guard
`authorize_sesi_access()`, `api/v1/taskinv_hasil.py:78` ✓) dan **422** (bila status sesi belum
TAHAP3, `taskinv_hasil.py:79-82` ✓).

Artinya **"0 dari 0 task" bukan berarti daftar task kosong** — kemungkinan besar panggilan itu
**gagal** (403/500) dan kegagalannya ditelan. Ini juga menjelaskan kenapa halaman **admin** untuk
sesi yang sama menampilkan 19 task dengan benar: admin lolos `authorize_sesi_access()`, partisipan
mungkin tidak.

**Konsekuensi untuk urutan kerja:** kerjakan **backlog 026** (hentikan telan-senyap) **LEBIH
DULU**, lalu buka lagi halaman Tahap 3 sesi `tises_434a8864` sebagai partisipan — error yang
sesungguhnya (kode status + `X-Request-ID`) akan langsung terlihat dan kemungkinan besar
**langsung menyelesaikan** item 024 ini tanpa menebak-nebak.

Catatan: hipotesis `detil_tugas_id: null` di bawah **belum gugur**, tapi turun prioritasnya —
ia hanya relevan bila ternyata endpointnya mengembalikan 500, bukan 403.

## Kemungkinan penyebab (belum terverifikasi — perlu baca kode)

Karena fakta #2 dan #3 membuktikan task final **tersimpan dengan benar** di tabel task
terpilih/frozen, tapi endpoint yang dipakai halaman Tahap 3 partisipan mengembalikan kosong,
kemungkinan besar penyebabnya ada di **query/filter spesifik endpoint Tahap 3** (mis.
`GET /task-inventory/responden/{id}/tahap3` atau serupa) — bukan di logika freeze itu sendiri.

Perbedaan konkret antara sesi Wali Kelas (rusak) dan Guru Kelas SD (normal) yang bisa jadi
petunjuk awal (belum tentu relevan, perlu dicek di kode):

- Wali Kelas: 63 baris katalog, 27 task partial diputuskan Tahap 2, 19 final. Salah satu baris
  katalog Wali Kelas punya `detil_tugas_id: null` (task langsung di bawah tugas pokok
  "Koordinasi" tanpa level detil — lihat `ti_catalog` untuk `jbt_59eb604e`, kode
  `WK-ALL-PD-001`) — **kemungkinan** endpoint Tahap 3 melakukan `JOIN`/query yang secara implisit
  mengharuskan `detil_tugas_id` NOT NULL, sehingga bila task ber-`detil_tugas_id: null` termasuk
  dalam 19 final, query gagal senyap dan mengembalikan list kosong alih-alih partial. **Perlu
  diverifikasi**: apakah task `WK-ALL-PD-001` benar masuk ke 19 final (ada di tabel "Task Relevan
  Terpilih" admin), dan apakah endpoint Tahap 3 memang melakukan INNER JOIN ke `detil_tugas`.
- Guru Kelas SD: 30 baris katalog, semua task punya `detil_tugas_id` terisi (tidak ada baris
  langsung di bawah tugas pokok) — konsisten dengan hipotesis di atas, tapi **korelasi bukan
  bukti sebab-akibat**; perlu baca kode query sebenarnya.
- Kemungkinan lain: race condition di proses freeze `Mulai Tahap 3` untuk sesi dengan jumlah
  task partial besar (27 keputusan Tahap 2 disimpan sekaligus untuk Wali Kelas vs. hanya 8 untuk
  Guru Kelas SD) — mis. bulk-insert task terpilih yang tidak sepenuhnya commit sebelum endpoint
  Tahap 3 query, meski fakta #4 (persisten setelah 7 menit) mengurangi kemungkinan ini.

## Langkah eksekusi

**JANGAN langsung menulis kode.** Langkah pertama adalah membaca kode endpoint yang dipanggil
halaman Tahap 3 partisipan (`anjab-abk-web-app/src/app/(auth)/task-inventory/tahap3/[responden_id]/page.tsx`
dan endpoint backend yang dipanggilnya) untuk:

1. Identifikasi endpoint pasti yang dipanggil untuk mengambil daftar task Tahap 3.
2. Baca query/filter di endpoint tsb — cari kemungkinan `INNER JOIN` ke `detil_tugas` atau
   filter lain yang bisa mengecualikan task dengan `detil_tugas_id: null`.
3. Verifikasi langsung di DB produksi (bila ada akses): apakah baris `WK-ALL-PD-001` (atau task
   lain ber-`detil_tugas_id: null`) ada di tabel task terpilih/frozen milik `tises_434a8864`, dan
   apa hasil query endpoint Tahap 3 dijalankan manual dengan `responden_id` salah satu dari 7
   responden sesi tsb.
4. Bila hipotesis JOIN terbukti benar → perbaiki query (LEFT JOIN / query terpisah yang tidak
   mengasumsikan `detil_tugas_id` selalu ada), tambah test regresi dengan skenario task
   ber-`detil_tugas_id: null` masuk ke daftar final.
5. Bila hipotesis salah → investigasi lebih dalam log backend sekitar waktu `Mulai Tahap 3`
   sesi ini (2026-07-14, sekitar jam yang tercatat di memori uji), cari exception yang ditelan.

## Kriteria penerimaan

- [ ] Root cause dikonfirmasi (bukan dugaan)
- [ ] `GET` endpoint Tahap 3 untuk responden di sesi `tises_434a8864` (atau sesi baru dengan
      kondisi serupa yang direproduksi di lingkungan test) mengembalikan seluruh task final,
      bukan list kosong
- [ ] Test regresi baru: sesi TI dengan task final yang mencakup baris `detil_tugas_id: null`
      (task langsung di bawah tugas pokok) tetap muncul lengkap di endpoint/halaman Tahap 3

## Skenario uji

- Test backend baru untuk endpoint Tahap 3 dengan fixture sesi yang task finalnya mencakup
  campuran task ber-`detil_tugas_id` terisi dan `null`
- Bila root cause di luar itu (mis. race condition), tambahkan test yang mereproduksi kondisi
  aktualnya (jumlah task partial besar, dsb.)

## Definition of done

- [ ] `make test` hijau di repo terkait
- [ ] `CHANGELOG.md` diperbarui
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Sesi TI produksi `tises_434a8864` (Wali Kelas) sengaja DIBIARKAN macet di status TAHAP3**
  sebagai bukti reproduksi — jangan "Hapus paksa" atau coba benahi manual lewat data sampai
  root cause dikonfirmasi; state ini yang dipakai untuk verifikasi perbaikan nanti.
- Task Inventory Wali Kelas ini **data uji coba** (bukan studi asli), koordinator `Christmass
  Jeffri`, sesi dibuat bersamaan dengan `tises_070c04b0` (Guru Kelas SD, sukses) — detail lengkap
  di memori `ti-opm-test-2-2026-07-14`.
- Bug ini **berbeda** dari backlog 023 (OPM 409 "sesi sudah ada") — ditemukan di sesi/percobaan
  yang sama tapi merupakan cacat terpisah di TI, bukan OPM. Backlog 023 tetap terverifikasi masih
  terjadi (lihat update di file backlog 023) memakai jabatan Wali Kelas & Guru Kelas SD ini juga.

---

## Root cause (2026-07-14, sesi ketiga — TERBUKTI)

Ditemukan dengan memanggil API produksi langsung memakai token admin (M2M), bukan lewat UI —
sehingga status HTTP asli terlihat, tidak lagi tersembunyi di balik `?? []` web-app.

### Bukti empiris

Sesi `tises_434a8864` (Wali Kelas, TAHAP3, `jumlah_task_terpilih: 19`):

| Endpoint | Status |
|---|---|
| `GET /api/v1/task-inventory/sesi/tises_434a8864` | **200** ✓ |
| `GET .../sesi/tises_434a8864/responden` | **200** ✓ |
| `GET .../sesi/tises_434a8864/tahap2` | **200** ✓ |
| `GET .../sesi/tises_434a8864/task-terpilih` | **500** `{"error":"internal_error"}` ✗ |

Sesi TAHAP3 lain (`tises_d3806654`, Koordinator Ekstrakurikuler) → `task-terpilih` **200**.
Jadi bukan bug umum endpoint, tapi **bergantung data**.

Membandingkan 16 kode task yang disetujui koordinator di sesi itu dengan katalog jabatannya:

```
catalog rows: 63 | rows dengan NULL detil_tugas: 1
    WK-ALL-PD-001 | detil_tugas = None | tugas_pokok = 'Koordinasi'
```

`WK-ALL-PD-001` **termasuk** dalam himpunan task beku sesi tsb. Pemindaian seluruh katalog:
**2 baris** ber-`detil_tugas` NULL di seluruh sistem — `WK-ALL-PD-001` (Wali Kelas) dan 1 baris
di Wakil Kepala Sekolah Bidang Kurikulum. Hanya sesi yang membekukan salah satu kode itu yang kena.

### Mekanisme (kode aktual)

1. `taskinv/services/catalog.py:157` — `detil_tugas=dt.nama if dt else None` → `TiCatalogRead.detil_tugas`
   memang **nullable** (`str | None`). ✓
2. `taskinv/schemas/hasil.py:17` — `TiTaskTerpilihRead.detil_tugas: str` → **wajib, non-nullable**. ✓
3. `taskinv/services/analisis.py:39` — `detil_tugas=cat.detil_tugas if cat else ""`.
   Fallback `""` hanya menangani kasus **katalog hilang** (`cat is None`). Bila `cat` **ada**
   tapi `cat.detil_tugas is None`, yang dioper adalah `None` → **Pydantic ValidationError** →
   500. ✓
4. Cacat **identik** di `analisis.py:103` (`compute_hasil_sesi`) → `GET /sesi/{id}/hasil` dan
   `POST /sesi/{id}/analisis` juga 500 untuk sesi yang sama.

### Kenapa investigasi sebelumnya menyimpulkan hipotesis (b) "GUGUR"

Catatan investigasi lama menyatakan hipotesis "INNER JOIN `detil_tugas_id: null`" gugur karena
`catalog.py:148` & `analisis.py:32-53` "justru tetap mengemit baris meski katalog hilang". Itu
**benar tapi tidak relevan** — kasus yang sebenarnya terjadi bukan *katalog hilang*, melainkan
*katalog ADA dengan `detil_tugas` NULL*. Fallback `if cat else ""` menutup kasus pertama dan
justru **membiarkan** kasus kedua lolos ke Pydantic. Hipotesis (b) sebetulnya **hampir benar**;
yang keliru adalah cara pengujiannya.

### Kenapa gejalanya "0 task" (bukan pesan error)

Web-app (sebelum perbaikan 026) menelan error API dengan `?? []` → 500 tampil sebagai daftar
kosong. Setelah 026, penelanan hilang → gejalanya berubah jadi **halaman detail sesi crash total**
("Gagal memuat detail analisis" / Server Components render error), yang memang teramati
2026-07-14. Sesi itu bahkan **tidak bisa dihapus lewat UI** karena tombolnya ikut tak terender.

## Perbaikan (terkunci)

`taskinv/services/analisis.py` — **dua** tempat, baris **39** dan **103**:

```python
# SEBELUM
detil_tugas=cat.detil_tugas if cat else "",
# SESUDAH
detil_tugas=(cat.detil_tugas or "") if cat else "",
```

Pertimbangkan juga `tugas_pokok` (baris 38 & 102): `TiCatalogRead.tugas_pokok` saat ini
non-nullable (`catalog.py:154` mengoper `tp.nama` langsung), jadi belum bisa NULL — **tapi**
`_to_catalog` akan `AttributeError` bila `tp is None`. Di luar lingkup item ini; catat saja.

### Keputusan yang dikunci

- **Perbaiki di lapisan penyaji (`analisis.py`), BUKAN dengan membersihkan data katalog.**
  `detil_tugas` memang boleh NULL menurut model (`TiCatalogRead`), jadi penyaji yang wajib
  toleran. Membersihkan 2 baris data hanya menyembunyikan bug sampai ada uraian tugas baru
  tanpa detil tugas.
- Sesi produksi yang sudah terlanjur beku dengan kode bermasalah **langsung pulih** begitu
  perbaikan ini di-deploy (tidak perlu migrasi/backfill).

## Skenario uji (wajib)

- [ ] Uraian tugas dengan `detil_tugas_id = NULL` → `GET /sesi/{id}/task-terpilih` **200**,
      field `detil_tugas` berisi `""` (bukan 500).
- [ ] Sesi yang sama → `GET /sesi/{id}/hasil` & `POST /sesi/{id}/analisis` **200**.
- [ ] Regresi: sesi tanpa NULL apa pun tetap berperilaku sama.

## Kriteria penerimaan

- [ ] `make test` hijau, dengan test baru yang gagal sebelum perbaikan.
- [ ] Diverifikasi di produksi: sesi Wali Kelas (atau yang setara) bisa dibuka & dianalisis.
