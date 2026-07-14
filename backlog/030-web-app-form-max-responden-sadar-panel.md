# Backlog 030 — Web app: form "Mulai Analisis Jabatan" (TI & OPM) tidak sadar jumlah anggota panel → admin menabrak 422 `max_responden`

> **Repo:** `anjab-abk-web-app`
> **Status:** Siap dieksekusi
> **Blocked by:** — (backend 028 sudah code-complete; item ini melengkapinya di sisi UI)
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Backend **028** membuat `POST /task-inventory/sesi` **menolak keras (422)** bila jumlah anggota SME
panel melebihi `max_responden` — menyamakannya dengan OPM, yang sudah lama begitu. Itu perbaikan
yang benar (sebelumnya anggota panel dibuang diam-diam), tapi ia **memindahkan beban ke admin**:
kondisi yang dulu "sukses" kini memunculkan error, dan form-nya sendiri **tidak memberi petunjuk
apa pun** untuk menghindarinya.

Form "Mulai Analisis Jabatan" tidak tahu berapa anggota panel jabatan yang dipilih. Admin mengisi
`max_responden` (default **10**) secara buta, menekan Simpan, lalu ditolak — tanpa pernah diberi
tahu bahwa panelnya berisi 11 orang. Untuk **OPM** situasi ini sudah ada **sejak lama** tanpa
panduan UI sama sekali.

Tujuan item ini: **cegah masalahnya sejak awal** — form memuat jumlah anggota panel begitu jabatan
dipilih, lalu menyarankan/mengisi `max_responden` secara sadar.

## Kondisi sekarang (verified)

| # | Fakta | Verifikasi |
|---|---|---|
| 1 | Backend TI kini menolak `len(panel.partisipan_ids) > max_responden` dengan 422 `"Jumlah anggota SME panel (11) melebihi max_responden (10)."` (`taskinv/services/sesi_sql.py`, backlog 028) | ✓ dieksekusi 2026-07-14, `make test` hijau 623 test |
| 2 | Backend OPM sudah menolak dengan pesan yang sama persis (`opm/services/sesi_sql.py:167-172`) — **sejak sebelum 028** | ✓ dibaca langsung |
| 3 | Produksi 2026-07-14: panel **Guru Kelas SD** punya **11 anggota**; `max_responden` default **10** → inilah kondisi yang kini kena 422 | ✓ Playwright |
| 4 | Panel >10 anggota / pas di batas per 2026-07-14: Guru Kelas SD (11), Guru Mapel SMP (10), Guru Mapel SMA (10) | ✓ backlog 028 |
| 5 | `POST /api/v1/task-inventory/sesi` sudah mencantumkan `422` di `responses` — kontrak API tidak berubah, jadi item ini **murni UI** (tidak perlu regen tipe) | ✓ `openapi.json` diperiksa |

## Keputusan yang sudah dikunci

- **Jangan** "memperbaiki" dengan menaikkan default `max_responden`. Itu menyembunyikan masalah,
  bukan menyelesaikannya — admin tetap tidak tahu berapa anggota panelnya.
- Form **wajib menampilkan jumlah anggota panel** begitu jabatan dipilih. Itu informasi yang
  menentukan nilai `max_responden` yang benar, dan saat ini sama sekali tidak terlihat.
- Pesan **422 dari backend wajib tampil utuh** ke admin (lewat `notifyGagal`, pola backlog 017).
  Pesannya sudah menyebut kedua angka — jangan diganti dengan pesan generik "Gagal menyimpan".
- Berlaku untuk **TI dan OPM** sekaligus. OPM sudah menolak sejak lama tanpa panduan UI; membetulkan
  TI saja akan meninggalkan OPM tetap membingungkan.

## Langkah eksekusi

### Langkah 1 — Muat jumlah anggota panel saat jabatan dipilih

Di form "Mulai Analisis Jabatan" TI (dan padanannya di OPM): saat `jabatan_id` dipilih, ambil SME
panel jabatan itu dan tampilkan jumlah anggotanya (mis. *"SME panel: 11 anggota"*). Endpoint
`/sme-panel` sudah ada.

### Langkah 2 — Sarankan `max_responden` yang sadar panel

Isi otomatis `max_responden` = jumlah anggota panel (atau validasi di klien: tolak submit bila
`max_responden < jumlah anggota`, dengan pesan yang sama gayanya dengan backend). Putuskan salah
satu saat eksekusi — **prefill lebih disukai**, karena tidak menambah gesekan.

### Langkah 3 — Tampilkan 422 backend apa adanya

Pastikan pesan 422 backend sampai ke admin lewat `notifyGagal` + `X-Request-ID`. Ini bersinggungan
dengan invariant backlog **026** (error API dilarang ditelan senyap) — periksa jalur submit form ini
memang tidak menelannya.

### Langkah 4 — Jabatan tanpa panel

Jabatan **tanpa** SME panel tetap sah (sesi dibuat kosong, perilaku backend tidak berubah).
Jangan blokir submit-nya; tampilkan saja *"Jabatan ini belum punya SME panel"*.

## Kriteria penerimaan

- [ ] Memilih jabatan di form TI/OPM → jumlah anggota SME panel terlihat sebelum submit
- [ ] Panel 11 anggota → `max_responden` ter-prefill 11 (atau submit ditolak di klien dengan pesan jelas)
- [ ] Bila 422 backend tetap terjadi → pesannya tampil utuh (menyebut kedua angka), bukan pesan generik
- [ ] Jabatan tanpa panel → tetap bisa dibuat, tanpa error
- [ ] Perilaku TI dan OPM konsisten

## Skenario uji

- Test: pilih jabatan dengan panel 11 anggota → assert jumlah anggota terender & `max_responden` = 11.
- Test: mock submit → 422 → assert `notifyGagal` terpanggil dengan pesan backend utuh.
- Test: jabatan tanpa panel → assert submit tetap jalan, tidak ada error.
- `make test` hijau + `npm run build` sukses.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-web-app`, `npm run build` sukses
- [ ] `CHANGELOG.md` diperbarui
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- Item ini lahir dari eksekusi **028** (Langkah 3 di file itu, yang sengaja tidak dikerjakan karena
  menyentuh repo lain). Nilainya **naik** setelah 028, bukan turun: kondisi yang dulu (keliru)
  sukses kini memunculkan error, jadi UI perlu mencegahnya sejak awal.
- Tidak memblokir rilis 028 — backend tetap benar tanpa item ini, hanya kurang ramah.
