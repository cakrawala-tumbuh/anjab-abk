# Rencana: Revisi Master Data Task Inventory dari Task Bank v2_19

**Status**: siap dieksekusi — semua keputusan lengkap
**Tanggal**: 2026-07-12
**Sumber**: `data/task-inventory/Task_Bank_Complete_AllRoles_v2_19 (1).xlsx`, sheet **`05_Raw_Task_Migration`** (1.235 baris data, 44 kolom)

---

## 1. Verifikasi pemetaan kolom

Pemetaan sumber **terverifikasi benar**. Satu koreksi: nama sheet sebenarnya `05_Raw_Task_Migration` (bukan `Raw Task Migration`).

| Entitas | Kolom | Header asli |
|---|---|---|
| **Jabatan** | D | `Role_Name` |
| **Tugas Pokok** | D, I | `Role_Name`, `Duty_Area` |
| **Detail Tugas** | D, I, J | + `Sub_Duty` |
| **Uraian Tugas** | D, I, J, L | + `Task_Statement_5C` |
| ↳ CalHR | V, Y, Z, AA, AB | `Preliminary_VA_Category`, `Formal_Actual`, `Baseline_Peak`, `Frequency`, `Duration_Estimate` |

---

## 2. Keputusan

| # | Isu | Keputusan |
|---|---|---|
| 1 | Katalog lama (2.738 baris) vs Excel — tanpa join key | **Ganti total (replace)** |
| 2 | Kolom G `Jenjang` (92% = `ALL`) vs kolom DB `unit` NOT NULL | **Abaikan kolom G** → isi konstanta `"ALL"` |
| 3 | Kolom V — 26% di luar domain `VaType` | **Perluas `VaType` jadi 5 nilai** (§5.3) |
| 4 | Kolom AR `Final_Decision` | **Buang 95 baris `Retire`** → seed 1.140 baris |
| 5 | Kolom Z terkontaminasi nilai frekuensi | **Direkonstruksi**, bukan di-NULL-kan (§5.2) |
| 6 | Kolom AB free-text vs kolom DB Integer | **Ubah tipe** `std_durasi_per_kali` → `String(100)`, nilai apa adanya |
| 7 | Peleburan Tugas Pokok | **Diterima** — 1 record `"Koordinasi"` + M2M ke 17 jabatan |

### Keputusan #4 membereskan hampir semua cacat data

95 baris `Retire` bukan sekadar task yang dipensiunkan — di situlah **seluruh cacat data berkumpul**:

| Masalah | Sebelum (1.235) | Sesudah buang Retire (1.140) |
|---|---|---|
| Uraian (kolom L) kosong | 28 baris | **0** — fallback ke kolom K tidak diperlukan |
| Duplikat sejati (D,I,J,L) | 4 grup | **0** |
| Kolom Y di luar domain | 82 baris | **2** (lalu 0, §5.2) |

Sisa: `Keep` 949, `Merge` 110, `Revise` 81. Jabatan `Guru Bidang Studi` ikut hilang (2 barisnya dua-duanya `Retire`).

---

## 3. Blocker: sudah diselidiki, semuanya aman

### ✅ Purge katalog lama — AMAN

Kekhawatiran awal: menghapus 2.738 baris katalog akan memutus relasi ke jawaban responden, dan **tidak ada FK di database** yang mencegahnya (gagal senyap → baris yatim).

**Hasil pengecekan: `daftar_ti_sesi` → `total: 0`.** Tidak ada satu pun sesi Task Inventory, sehingga tidak ada responden, seleksi Tahap 1, keputusan Tahap 2, maupun detail Tahap 3. Purge aman sepenuhnya.

> **Jendela sempit.** `ti_seleksi`, `ti_tahap2`, dan `ti_detail` merujuk katalog lewat **`task_kode` (String(20))**, bukan ID (`models.py:501,513,528`). Karena skema kode berubah total (`TIf0b59714` → `KS-ALL-LEAD-001`), penggantian katalog **setelah** ada sesi berjalan akan merusak data transaksi. Kerjakan sekarang, selagi kosong.

### ✅ `unit = "ALL"` — AMAN

- **Tidak ada** array hardcoded `["TK","SD","SMP","SMA"]` di web-app; daftar unit selalu diturunkan dari data (`Object.keys(grouped).sort()`).
- **Tidak ada** union type/enum yang membatasi `unit` — bertipe `string` bebas di `schema.ts`, dan `String(20)` tanpa CHECK di `models.py:412`.
- Alur sesi & kuesioner **tidak menyentuh `unit`** — semuanya lewat `valid_kodes_for_jabatan(jabatan_id)` yang memang lintas-unit. Sesi TI bahkan sudah tidak punya field `unit` (revisi 2026-06-25).
- Dampak satu-satunya **kosmetik**: halaman `/master-data/task-inventory` yang mengelompokkan per unit akan punya satu grup berjudul "ALL". Justru menghilangkan duplikasi kartu antar-unit.

### ✅ Peleburan Tugas Pokok — diterima

Backend **tidak mendukung** Tugas Pokok per-jabatan: `TiTugasPokokModel.nama` di-`unique=True` (`models.py:351`), service menolak duplikat dengan `ConflictError` (`tugas_pokok_sql.py:83-86`). Format yang didukung adalah **M2M**: satu record `"Koordinasi"`, ditautkan ke banyak jabatan lewat `ti_tugas_pokok_jabatan`.

Konsekuensinya 156 pasangan (D,I) melebur jadi **89** record: `"Koordinasi"` → 1 record milik **17 jabatan**, `"Pengembangan Diri"` → 8, `"Perencanaan Pembelajaran"` → 6.

**Yang tidak hilang**: Detail Tugas & Uraian Tugas tetap terpisah per jabatan (`ti_uraian_tugas.jabatan_id` = M2O). Uraian "Koordinasi" milik Kepala Sekolah tetap beda record dari milik Wali Kelas — yang melebur hanya **label tugas pokoknya**.

Efek samping yang perlu disadari: mengedit nama tugas pokok `"Koordinasi"` akan berdampak ke 17 jabatan sekaligus.

---

## 4. Bentuk data hasil ekstraksi

| Entitas | Hasil |
|---|---|
| Jabatan | **24** (auto-create dari `Role_Name`) |
| Tugas Pokok | **89** unik-by-nama (30 di antaranya dipakai >1 jabatan) |
| Detail Tugas | **251** unik-by-(tugas_pokok, nama) |
| Uraian Tugas | **1.140** — `kode` = `Task_ID` (unik, ≤20 char, muat di `String(20)`) |

2 baris ber-`Sub_Duty` kosong; `detil_tugas_id` **nullable**, jadi keduanya digantung langsung di Tugas Pokok.

---

## 5. Nilai standar CalHR

### 5.1 Cakupan akhir — 5 dari 9 kolom terisi penuh

| Kolom Excel → field DB | Tipe | Terisi |
|---|---|---|
| V → `std_va_type` | `VaType` (5 nilai, diperluas) | **1.140 / 1.140** |
| Y → `std_sumber_bukti` | `Formal \| Aktual \| Keduanya` | **1.140 / 1.140** |
| Z → `std_kondisi` | `Baseline \| Peak \| Both` | **1.140 / 1.140** (265 direkonstruksi) |
| AA → `std_frekuensi_teks` | free text (100) | **1.140 / 1.140** |
| AB → `std_durasi_per_kali` | `String(100)` (diubah) | **1.140 / 1.140** |

Empat kolom sisanya **tetap NULL — tidak ada sumbernya di Excel**: `std_jam_per_minggu`, `std_peak4w_hours`, `std_ai_mode`, `std_dcs_flag`.

Ini **tidak merusak** apa pun — Tahap 3 sudah dirancang menoleransi master tanpa nilai standar (`models.py:538-540`: *"Task yang masternya tidak punya nilai standar tetap True — tidak ada standar untuk dibantah"*). Konsekuensinya: partisipan mengisi keempat komponen itu dari nol, tanpa nilai awal.

### 5.2 Rekonstruksi kolom Z

265 baris kolom Z terkontaminasi nilai frekuensi. Alih-alih menebak dari asumsi, **aturannya dipelajari dari 874 baris kolom Z yang bersih** — polanya konsisten & masuk akal secara domain (tugas berulang-rapat = beban dasar; tugas jarang/musiman = beban puncak):

| Frekuensi | Baseline | Peak | Kesimpulan |
|---|---|---|---|
| Harian | 67 | 5 | **Baseline** (93%) |
| Mingguan | 91 | 9 | **Baseline** (91%) |
| Bulanan | 94 | 15 | **Baseline** (86%) |
| Semesteran | 63 | 137 | **Peak** (68%) |
| Tahunan | 41 | 232 | **Peak** (85%) |
| Insidental | 21 | 99 | **Peak** (82%) |

Nilai `Both` tidak pernah dipakai sama sekali (0 dari 874). Aturan diperhalus dengan `CF30_Cluster` (min. 5 sampel/sel, fallback ke frekuensi saja). **Divalidasi silang 5-fold: 85,0%** — naik dari 82,4% bila hanya frekuensi; perbaikannya bertahan di luar sampel, jadi bukan overfitting.

Hasil → **`data/task-inventory/tebakan_kondisi_kolom_Z.csv`**:

| Kasus | Jumlah | Penanganan |
|---|---|---|
| **TERTUKAR** (Z=frekuensi, AA=kondisi) | 14 | **Pemulihan pasti** (keyakinan 1,00) — bukan tebakan, nilainya tinggal ditukar balik |
| **Z tertimpa frekuensi** (Z = AA) | 249 | Diinferensi dari aturan di atas |
| **Z = `Perlu Validasi`** | 2 | **Disalin dari induk kanonik** — `Reviewer_Notes` menunjuk eksplisit ke `STSAR-ALL-LEAD-025` ("padanan kanonik"), yang ber-`Duty_Area` & `Sub_Duty` identik: `Baseline`/`Mingguan`/`Formal`. Keyakinan 0,90. |

Distribusi hasil: **Baseline 106, Peak 159**. Nol baris kosong.

Salinan induk kanonik itu sekaligus mengisi 2 nilai terakhir di **kolom Y** (`Perlu Validasi` → `Formal`), sehingga `std_sumber_bukti` juga terisi penuh.

> ⚠️ **89 baris berkeyakinan <75%** ditandai `perlu_review = ya` di CSV (mayoritas `Semesteran`/`Insidental` — dua frekuensi paling ambigu; di `Semesteran` yang hanya 68% condong ke Peak, kira-kira 1 dari 3 tebakan berpotensi meleset). **Keputusan: diterima apa adanya, seed langsung.** CSV tetap jadi jejak audit — tiap baris memuat nilai asli Z & AA, cluster, metode, skor keyakinan, sehingga bisa dikoreksi belakangan tanpa mengulang dari nol.

### 5.3 Kolom V — `VaType` diperluas jadi 5 nilai

292 baris (26%) bernilai `Context-Dependent` (290) atau `Needs Validation` (2) — di luar domain `VaType`.

**Inferensi tidak layak, dan itu memang benar secara semantik.** Prediktor terbaik yang tersedia (kolom U `Legacy_VA_NVA`) hanya seakurat lempar koin: untuk `U=VA`, sebarannya VA-Enable 325 vs VA-Core 313 → **49%** (bandingkan kolom Z: 85%). Sebabnya terbaca di kolom W (`VA_Rationale`): *"nilai bergantung apakah menghasilkan keputusan/dampak (Context-Dependent)"* — jadi `Context-Dependent` **bukan nilai yang hilang**, melainkan **status kurasi** yang berarti "belum diputuskan". Tidak ada yang bisa ditebak karena jawabannya memang belum ada; justru itulah yang akan diputuskan SME di Tahap 3.

**Keputusan: perluas `VaType` (`schemas/calhr.py:10`) menjadi 5 nilai**, dipakai bersama master & jawaban responden:

```python
VaType = Literal["VA-Core", "VA-Enable", "NVA-Residual", "Context-Dependent", "Needs Validation"]
```

**Tanpa migrasi DB** — kolomnya sudah `String(20)`; `Context-Dependent` (17 char) dan `Needs Validation` (16 char) muat. Yang berubah hanya `Literal` Pydantic + enum frontend.

Hasil `std_va_type`: VA-Enable 388, VA-Core 321, Context-Dependent 290, NVA-Residual 139, Needs Validation 2.

> ⚠️ **Konsekuensi yang diterima sadar**: karena `VaType` dipakai bersama, responden Tahap 3 **kini bisa memilih `Context-Dependent`/`Needs Validation` sebagai jawaban final** — artinya boleh tidak memutuskan kategori VA, padahal memutuskan itulah tujuan Tahap 3. Bila kelak banyak jawaban mengendap di `Context-Dependent`, obatnya: pisahkan `StdVaType` (5 nilai, master) dari `VaType` (3 nilai, jawaban responden).

---

## 6. Rencana implementasi

### 6.1 Script ekstraksi — `data/task-inventory/extract_task_bank.py`

Mandiri (stdlib + `openpyxl`), **murni membaca**: tidak menyentuh DB, tidak menyentuh jaringan, aman dijalankan berulang.

- **Input**: path `.xlsx` + nama sheet (default: file v2_19, `05_Raw_Task_Migration`).
- **Filter**: buang baris `Final_Decision == "Retire"`.
- **Output 1** → `task_catalog.json` (menggantikan `anjab-abk-backend/src/anjab_abk_backend/taskinv/data/task_catalog.json`).
- **Output 2** → `anomali_task_bank.csv` — jejak audit tiap nilai yang direkonstruksi/ditolak.
- **Output 3** → ringkasan rekonsiliasi ke stdout (baris dibaca → dibuang → entitas dihasilkan).

Skema JSON diperluas dari bentuk lama (`kode, unit, kategori_jabatan, tugas_pokok, detil_tugas, uraian_tugas, urutan`) dengan **5** field CalHR: `std_va_type`, `std_sumber_bukti`, `std_kondisi`, `std_frekuensi_teks`, `std_durasi_per_kali`.

### 6.2 Backend — 1 migrasi Alembic + perluasan Literal

**Migrasi (keputusan #6)**: `std_durasi_per_kali` Integer → `String(100)` (`make migration m="ubah std_durasi_per_kali jadi teks bebas"`).

Aman untuk perhitungan ABK: `std_durasi_per_kali` **tidak pernah dipakai aritmetika** — hanya diteruskan untuk ditampilkan (`catalog.py:163`, `analisis.py:46`). Hitungan beban kerja (`fmean(d.durasi_per_kali)`, `analisis.py:81`) jalan di **`ti_detail.durasi_per_kali`** — kolom Integer terpisah milik jawaban responden, yang **tidak diubah**.

**Tanpa migrasi (keputusan #3)**: perluas `VaType` di `schemas/calhr.py:10` jadi 5 nilai. Kolom DB sudah `String(20)`, cukup menampung.

### 6.3 Patch seeder — nilai CalHR saat ini **dibuang diam-diam**

Bug tak terlaporkan: `CatalogItem` (`taskinv/seed.py:36-45`) adalah TypedDict 7 field **tanpa `std_*`**, dan langkah 4 (`seed.py:220-231`) membangun `UraianTugasCreate` tanpa satu pun field CalHR. Jadi sekalipun JSON-nya berisi, kolom `std_*` di DB **tetap NULL**.

1. Tambah 5 field `std_*` ke `CatalogItem`, teruskan ke `UraianTugasCreate`.
2. **Unit test penjaga**: item katalog ber-`std_*` → benar-benar tersimpan ke kolom DB. Mencegah regresi senyap ini terulang.

### 6.4 Purge — `anjab-abk-backend/scripts/purge_task_catalog.py`

Seeder bersifat *insert-if-absent* (`ConflictError` → `pass`, `seed.py:232-233`) — ia **tidak pernah menghapus maupun mem-backfill**. "Ganti total" karenanya butuh purge eksplisit atas `ti_uraian_tugas`, `ti_detil_tugas`, `ti_tugas_pokok` + baris link M2M.

### 6.5 Frontend — 3 berkas

| Berkas | Masalah | Perbaikan |
|---|---|---|
| `task-inventory/tahap3/[responden_id]/detail-form.tsx:64` | `durasi_per_kali: t.std_durasi_per_kali ?? 60` — mem-prefill field **Integer NOT NULL** milik responden dari nilai standar. Begitu standar berisi `"Bervariasi"`, prefill rusak. | Berhenti mem-prefill dari `std_durasi_per_kali`; tampilkan teksnya sebagai **petunjuk** di samping input, responden isi angkanya sendiri. |
| `task-inventory/tahap3/[responden_id]/detail-form.tsx:21` | `z.enum(["VA-Core","VA-Enable","NVA-Residual"])` — akan menolak standar `Context-Dependent` | → 5 nilai |
| `master-data/uraian-tugas/tambah/uraian-tugas-form.tsx:28` | `z.number().int().min(0)` | → `z.string().max(100)`; input `type="number"` → `type="text"` |
| `components/calhr` (konstanta `VA_TYPE`) | daftar opsi dropdown VA | → 5 nilai |

### 6.6 Urutan eksekusi

1. **`make backup`** — snapshot DB dulu (target sudah ada di Makefile).
2. Jalankan script ekstraksi → `task_catalog.json` + CSV anomali.
3. Backend: migrasi Alembic + perluas `VaType` + patch `seed.py` + unit test → `make test` hijau.
4. Frontend: perbaiki 3 berkas (§6.5).
5. Purge katalog lama → jalankan `seed_all`.
6. Verifikasi via MCP: `daftar_uraian_tugas` → `total` = 1.140; sampel record memastikan kelima `std_*` terisi.

### 6.7 Yang **tidak** dilakukan

- Tidak menyentuh `anjab-abk-mcp`.
- Tidak memperluas `SumberBukti` / `Kondisi` — kolom Y & Z sudah direkonstruksi ke domain yang sah.
- Tidak mengubah `ti_detail.durasi_per_kali` (Integer, dipakai hitung beban kerja).
- Tidak ada commit tanpa instruksi eksplisit.

---

## 7. Cakupan perubahan

| Repo | Perubahan |
|---|---|
| `anjab-abk` (induk) | rencana ini + `data/task-inventory/extract_task_bank.py` + CSV anomali & tebakan Z |
| `anjab-abk-backend` | 1 migrasi Alembic (tipe AB), perluasan `VaType`, patch `seed.py`, script purge, unit test |
| `anjab-abk-web-app` | 3 berkas (§6.5) |

**Semua keputusan lengkap. Siap dieksekusi.**
