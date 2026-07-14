# Backlog 028 — Backend: auto-populate responden TI diam-diam membuang anggota SME panel saat panel > `max_responden`

> **Repo:** `anjab-abk-backend` (+ `anjab-abk-web-app` untuk sisi UI — lihat "Risiko & catatan")
> **Status:** Siap dieksekusi (setelah keputusan di "Keputusan yang perlu dikonfirmasi")
> **Blocked by:** —
> **Skill yang dipakai:** `backend-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Saat Analisis Jabatan Task Inventory dibuat, seluruh anggota SME panel jabatan itu
di-*auto-populate* menjadi responden. Bila **jumlah anggota panel melebihi `max_responden`**
(default **10**), anggota yang berlebih **dibuang secara diam-diam** — sesi dibuat sukses (201),
admin diarahkan ke halaman detail, dan **tidak ada apa pun yang memberi tahu** bahwa sebagian
anggota panel tidak terdaftar.

Konsekuensinya nyata: admin mengira seluruh panel sudah terdaftar, lalu menjalankan Tahap 1 →
Tahap 2 → Tahap 3 → analisis, sementara sebagian ahli **tidak pernah diundang mengisi**. Hasil
ANJAB/ABK-nya bias tanpa siapa pun sadar. Ini persis kelas bug yang dilarang di
`CLAUDE.md` web-app (entri backlog 017): *aksi yang tampak sukses padahal datanya tidak lengkap*.

Ironisnya, **OPM menangani kasus yang sama dengan benar** — ia menolak keras dengan
`"Jumlah anggota SME panel (11) melebihi max_responden (10)."` alih-alih membuang diam-diam.
TI dan OPM harus konsisten.

## Kondisi sekarang (verified)

| # | Fakta | Verifikasi |
|---|---|---|
| 1 | `SqlTiSesiService.create()` memanggil `assign_ti_responden_banyak(self._s, rec.id, panel.partisipan_ids, max_responden=data.max_responden)` — komentarnya sendiri menyebut *"Auto-populate **best-effort**"* (`src/anjab_abk_backend/taskinv/services/sesi_sql.py:143-148` ✓) | ✓ dibaca langsung |
| 2 | `assign_ti_responden_banyak()` mengembalikan `BulkAssignResult` berisi `skipped[]` dengan alasan **`kapasitas_penuh`** saat `current >= max_responden` (`taskinv/services/responden_sql.py:99-101` ✓) | ✓ dibaca langsung |
| 3 | **`create()` membuang `BulkAssignResult` itu** — nilai kembaliannya tidak ditangkap, tidak di-log, tidak diteruskan ke respons `TiSesiRead`. Informasi `skipped` **hilang total** | ✓ dibaca langsung (`sesi_sql.py:147` — hasil panggilan tidak di-assign) |
| 4 | **Reproduksi produksi 2026-07-14**: panel **Guru Kelas SD** punya **11 anggota**; sesi TI dibuat dengan `max_responden` default **10** → sesi sukses dibuat, hanya **10 responden** terdaftar. Anggota ke-11 (Teresia Dwi Rustini) **tidak ada** di daftar responden, tanpa peringatan apa pun di UI | ✓ Playwright + tabel responden |
| 5 | Perilaku **OPM** pada kondisi yang sama: `POST /opm/sesi` untuk panel 11 anggota & `max_responden=10` → **ditolak** dengan pesan jelas *"Jumlah anggota SME panel (11) melebihi max_responden (10)."* | ✓ toast tertangkap di Playwright |
| 6 | Endpoint bulk-assign **manual** (`POST .../responden/bulk`) sudah menampilkan `skipped[]` ke UI dengan alasan berbahasa Indonesia (`src/lib/format/bulk-skip-alasan.ts` di web-app ✓, backlog 007/019) — jadi mekanisme pelaporan sudah ada, hanya **jalur auto-populate** yang melewatinya | ✓ |

## Keputusan yang perlu dikonfirmasi ke user

Pilih **satu** dari dua arah (jangan dua-duanya):

- **(A) Samakan dengan OPM — tolak keras.** `POST /task-inventory/sesi` gagal (422) bila
  `jumlah anggota panel > max_responden`, dengan pesan yang sama persis seperti OPM. Admin lalu
  menaikkan `max_responden` secara sadar.
  *Kelebihan:* konsisten, mustahil kehilangan data diam-diam. *Kekurangan:* admin tidak bisa
  lagi sengaja membatasi jumlah responden lebih kecil dari panel.
- **(B) Tetap best-effort, tapi laporkan.** Sesi tetap dibuat, tapi respons `TiSesiRead`
  membawa `responden_skipped[]`, dan UI **wajib** menampilkan ringkasan ("11 anggota panel, 10
  terdaftar, 1 dilewati: kapasitas penuh") memakai `bulk-skip-alasan.ts` yang sudah ada.
  *Kelebihan:* fleksibel. *Kekurangan:* menambah field ke kontrak API.

**Rekomendasi: (A)** — paling sedikit ruang untuk salah paham, konsisten dengan OPM, dan
"membatasi responden lebih kecil dari panel" bukan kebutuhan yang pernah diminta. Bila admin
memang ingin panel besar tapi responden sedikit, jalur yang benar adalah mengecilkan panel atau
menghapus responden setelah sesi dibuat (fitur hapus responden sudah ada saat DRAFT/TAHAP1).

## Langkah eksekusi

### Bila (A) dipilih

1. Di `SqlTiSesiService.create()` (`taskinv/services/sesi_sql.py`), **sebelum** `self._s.add(rec)`:
   bila `panel is not None and panel.anggota` dan `len(panel.partisipan_ids) > data.max_responden`
   → `raise ValidationAppError(f"Jumlah anggota SME panel ({len(...)}) melebihi max_responden ({data.max_responden}).")`.
   Tiru **persis** pesan & bentuk yang dipakai OPM agar konsisten (cari di
   `src/anjab_abk_backend/opm/services/sesi_sql.py`).
2. Pastikan `openapi.json` mencantumkan 422 untuk operasi ini (kemungkinan sudah).

### Bila (B) dipilih

1. Tangkap hasil `assign_ti_responden_banyak(...)` di `create()`, teruskan `skipped[]` ke
   skema respons baru (mis. `TiSesiRead.responden_skipped`).
2. Regenerasi `openapi.json` → buat item backlog turunan untuk web-app (tampilkan ringkasan) &
   MCP (docstring tool).

### Langkah bersama (kedua opsi)

3. **Perbaiki UX default di web app**: form "Mulai Analisis Jabatan" TI (dan OPM) sebaiknya
   memuat jumlah anggota panel begitu jabatan dipilih, lalu **menyarankan `max_responden` ≥
   jumlah anggota panel** (atau mengisinya otomatis). Ini mencegah masalahnya muncul sejak awal
   — buat sebagai item backlog web-app terpisah bila terlalu besar untuk item ini.

## Kriteria penerimaan

- [ ] (A) `POST /task-inventory/sesi` dengan panel 11 anggota & `max_responden=10` → **422**
      dengan pesan yang sama gayanya dengan OPM — **atau** (B) sesi dibuat & respons memuat
      `skipped[]` yang ditampilkan di UI
- [ ] Tidak ada lagi jalur di mana anggota panel hilang dari sesi **tanpa jejak** (tidak di
      respons, tidak di log)
- [ ] Perilaku TI dan OPM konsisten untuk kondisi input yang sama
- [ ] Sesi dengan panel ≤ `max_responden` tetap dibuat seperti sekarang (tidak ada regresi)

## Skenario uji

- Test backend: panel 11 anggota, `max_responden=10` → sesuai opsi terpilih (422, **atau** 201
  dengan `skipped` berisi 1 entri beralasan `kapasitas_penuh`).
- Test backend: panel 3 anggota, `max_responden=10` → 201, 3 responden, `skipped` kosong.
- Test regresi: jabatan **tanpa** panel → sesi tetap dibuat kosong tanpa error (perilaku
  eksisting, jangan berubah).
- `make test` hijau.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-backend`
- [ ] `openapi.json` diregenerasi bila kontrak berubah (opsi B)
- [ ] `CHANGELOG.md` diperbarui
- [ ] `CLAUDE.md` backend diperbarui bila alur create sesi berubah
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Data produksi yang sudah terlanjur kena**: sesi TI Guru Kelas SD `tises_070c04b0`
  (2026-07-14) sempat kehilangan 1 anggota panel karena bug ini. Dalam simulasi, anggota itu
  ditambahkan manual setelah menghapus responden lain — jadi sesi itu sendiri tidak lagi
  bermasalah, tapi **sesi TI produksi lain yang dibuat dari panel > 10 anggota patut dicek
  ulang**: bandingkan `jumlah responden` vs `jumlah anggota panel` untuk setiap sesi TI yang
  ada. Panel dengan >10 anggota di produksi (per 2026-07-14): Guru Kelas SD (11), Guru Mapel SMP
  (10, pas di batas), Guru Mapel SMA (10, pas di batas).
- Opsi (A) adalah **breaking change perilaku** untuk admin yang selama ini "berhasil" membuat
  sesi dari panel besar — mereka akan mulai melihat error. Itu memang tujuannya, tapi siapkan
  penjelasannya.
