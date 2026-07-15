# Backlog 040 — TI Tahap 3: hapus "AI Mode" & "Ada risiko DCS", Frekuensi jadi dropdown

> **Repo:** `anjab-abk-web-app`
> **Status:** Langkah Frekuensi **Siap dieksekusi** (murni web-app, independen); langkah AI Mode & Risiko DCS **Menunggu (blocked by 039)**
> **Blocked by:** 039 (backend: hapus `ai_mode` & `dcs_flag` dari model/skema TI) — **hanya** untuk langkah AI/DCS. Langkah Frekuensi tidak diblokir.
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Feedback user (foto, 2026-07-14) atas layar **Task Inventory Tahap 3** — isian CalHR per task
(`detail-form.tsx`). Tiga perubahan UI:

1. **Hilangkan dropdown "AI Mode"** (`ai_mode`) dari form Tahap 3 — komponen CalHR ini
   dinilai tidak relevan untuk konteks yayasan pendidikan. Dihapus **tuntas** (bukan disembunyikan);
   bagian backend-nya (kolom & skema) adalah item **039**.
2. **Hilangkan checkbox "Ada risiko DCS"** (`dcs_flag`) dari form Tahap 3 — sama, dihapus tuntas.
3. **Ubah field "Frekuensi"** dari input teks bebas menjadi **dropdown** dengan **4 opsi**:
   **Harian, Mingguan, Semesteran, Insidental**. Ini **aman & murni web-app**: `frekuensi_teks`
   tetap `string` di backend, tidak ada perubahan skema, tidak dipakai di agregasi apa pun.

Perubahan menyentuh **dua** layar yang memakai komponen CalHR yang sama:
- Form partisipan **Tahap 3** (`detail-form.tsx`) — sumber feedback.
- Form admin **Master Data → Uraian Tugas** (`uraian-tugas-form.tsx`) yang mengisi **nilai standar**
  (`std_ai_mode`, `std_dcs_flag`, `std_frekuensi_teks`) yang men-*seed* Tahap 3 — harus disesuaikan
  agar konsisten (AI/DCS hilang; frekuensi standar jadi dropdown yang sama).
- Tampilan **hasil agregasi TI** (`[sesi_id]/page.tsx`) yang menampilkan kolom **DCS**
  (`dcs_flag_count`) — kolomnya dihapus.

## Keputusan yang sudah dikunci

- **AI Mode & Risiko DCS dihapus tuntas dari web-app, bukan disembunyikan.** Tidak ada `hidden`,
  tidak ada `display:none`. Import, zod, RowState, seed, dan render — semua dicabut.
- **Frekuensi tetap `string` di backend.** Field zod TETAP `z.string().min(1).max(100)` — **BUKAN**
  `z.enum(...)`. Alasan: data lama bisa berisi nilai bebas ("Bulanan", "2 mingguan", dsb.) yang tidak
  ada di 4 opsi baru; membuat enum akan menolak record lama saat divalidasi ulang. Yang berubah hanya
  **bentuk input di UI** (dari `<input type="text">` menjadi `<select>`), bukan tipe datanya.
- **4 opsi frekuensi, dalam urutan ini:** `Harian`, `Mingguan`, `Semesteran`, `Insidental`.
  ("Insidental" adalah salah satu opsi — untuk tugas yang muncul sesekali/tak terjadwal.)
- **Default seed "Mingguan" dipertahankan** (`rowDariStandar` & `std_frekuensi_teks ?? "Mingguan"`).
  "Mingguan" ada di daftar 4 opsi → default tetap valid tanpa perubahan.
- **Opsi frekuensi didefinisikan terpusat** di `src/components/calhr.ts` sebagai konstanta
  `FREKUENSI` (pola identik `AI_MODE`/`SUMBER_BUKTI`/`KONDISI`/`VA_TYPE`), dipakai identik di
  `detail-form.tsx` dan `uraian-tugas-form.tsx`.
- **Fallback nilai frekuensi lama yang tak cocok:** saat me-render `<select>`, bila nilai tersimpan
  (`r.frekuensi_teks`) **tidak ada** di `FREKUENSI`, opsi tambahan untuk nilai itu **tetap
  ditambahkan** ke daftar (di awal) agar `<select>` menampilkannya apa adanya dan tidak diam-diam
  meloncat ke opsi pertama. Ini berlaku di kedua form (Tahap 3 & Master Data). Lihat Langkah 1.4.
- **`AI_MODE` di `calhr.ts` TIDAK dihapus** selama item 039 belum tuntas — hanya *pemakaiannya* di
  `detail-form.tsx` & `uraian-tugas-form.tsx` yang dicabut. Konstanta dibiarkan sampai backend bersih,
  supaya `gen:api` & tipe tidak pecah di tengah jalan. (Hapus `AI_MODE` dari `calhr.ts` sebagai langkah
  penutup setelah 039 mendarat — lihat Langkah 2.5.)

## Kondisi sekarang (verified)

> Agen pelaksana **wajib membaca ulang** file-nya sebelum mengedit — baris bisa bergeser.

### `src/components/calhr.ts` ✓
- `SUMBER_BUKTI` line 1, `KONDISI` line 2, `AI_MODE` line 3, `VA_TYPE` line 4-10. **Belum ada
  `FREKUENSI`.** ✓

### `src/app/(auth)/task-inventory/tahap3/[responden_id]/detail-form.tsx` ✓
- Import `AI_MODE` dari `@/components/calhr` — **line 9** (`AI_MODE, KONDISI, SUMBER_BUKTI, VA_TYPE`). ✓
- Zod `detailItemSchema`:
  - `frekuensi_teks: z.string().min(1, "Frekuensi wajib diisi").max(100)` — **line 17** ✓
  - `ai_mode: z.enum(["Human-led", "Co-Pilot", "AI-assisted"])` — **line 21** ✓
  - `dcs_flag: z.boolean().default(false)` — **line 29** ✓
- `RowState`: `frekuensi_teks: string` **line 39**, `ai_mode` **line 43**, `dcs_flag: boolean` **line 45** ✓
- `punyaStandar()`: cek `t.std_ai_mode != null` **line 57**, `t.std_dcs_flag != null` **line 59** ✓
- `rowDariStandar()` seed default: `frekuensi_teks: t.std_frekuensi_teks ?? "Mingguan"` **line 75**,
  `ai_mode: t.std_ai_mode ?? "Human-led"` **line 79**, `dcs_flag: t.std_dcs_flag ?? false` **line 81** ✓
- Seed dari `existing` (detail tersimpan): `frekuensi_teks: existing.frekuensi_teks` **line 104**,
  `ai_mode: existing.ai_mode` **line 108**, `dcs_flag: existing.dcs_flag` **line 110** ✓
- `buildDetailPayload()` merakit objek untuk `detailItemSchema.safeParse`: `frekuensi_teks` **line 147**,
  `ai_mode: r.ai_mode` **line 151**, `dcs_flag: r.dcs_flag` **line 153** ✓
- Render **Frekuensi** = `<input type="text">` — **line 364-373** (label "Frekuensi", `value={r.frekuensi_teks}`,
  `onChange` set `frekuensi_teks`) ✓
- Render **AI Mode** = `<select>` — **line 415-429** (label "AI Mode", map `AI_MODE`) ✓
- Render **Ada risiko DCS** = `<label><input type="checkbox">` — **line 445-454** (`checked={r.dcs_flag}`,
  teks "Ada risiko DCS") ✓
- Konstanta gaya kelas `selectCls` **line 252**, `numCls` **line 254** — dipakai ulang. ✓

### `src/app/(auth)/master-data/uraian-tugas/tambah/uraian-tugas-form.tsx` ✓
- Import `AI_MODE` — **line 12** (`AI_MODE, KONDISI, SUMBER_BUKTI, VA_TYPE`) ✓
- Zod `schema`:
  - `std_frekuensi_teks: z.string().max(100).optional()` — **line 28** ✓
  - `std_ai_mode: z.enum(AI_MODE).optional()` — **line 32** ✓
  - `std_dcs_flag: z.boolean().optional()` — **line 34** ✓
- `onSubmit` body: `std_frekuensi_teks: values.std_frekuensi_teks || null` **line 112**,
  `std_ai_mode: values.std_ai_mode || null` **line 116**, `std_dcs_flag: values.std_dcs_flag ?? null` **line 118** ✓
- Render **std_frekuensi_teks** = `<input type="text">` — **line 367-378** (label "Frekuensi",
  placeholder "cth. Mingguan") ✓
- Render **std_ai_mode** = `<select>` dengan opsi "— tidak ada standar —" + map `AI_MODE` — **line 425-441** ✓
- Render **std_dcs_flag** = `<label><input type="checkbox">` "Ada risiko DCS" — **line 461-471** ✓

### `src/app/(auth)/master-data/uraian-tugas/[id]/page.tsx` (mode edit — defaultValues) ✓
- `std_frekuensi_teks: uraianTugas.std_frekuensi_teks ?? undefined` **line 77** ✓
- `std_ai_mode: uraianTugas.std_ai_mode ?? undefined` **line 81** ✓
- `std_dcs_flag: uraianTugas.std_dcs_flag ?? undefined` **line 83** ✓

### `src/app/(auth)/master-data/uraian-tugas/page.tsx` (list) ✓
- **line 96** `{ut.std_frekuensi_teks !== null && (…badge "Standar"…)}` — hanya membaca `std_frekuensi_teks`
  (yang **tetap ada**). **TIDAK perlu diubah** — bukan `ai_mode`/`dcs_flag`. ✓

### `src/app/(auth)/task-inventory/[sesi_id]/page.tsx` (hasil agregasi TI) ✓
- Kolom **DCS**: header `<th>DCS</th>` (di blok `thead` Hasil Agregasi) dan sel
  `{t.dcs_flag_count > 0 ? `⚠ ${t.dcs_flag_count}` : "—"}` — **line 440** ✓
- **`ai_mode_dist` TIDAK ADA** di file ini (grep nol hasil) — tidak ada distribusi AI Mode yang perlu
  dihapus. Hanya `dcs_flag_count`. ✓
- File ini **tidak** meng-import `AI_MODE`/`calhr` (grep nol). ✓

### `src/lib/api/schema.ts` (GENERATED) ✓
- **JANGAN edit tangan.** Tipe `TiDetailItem.ai_mode`, `.dcs_flag`, `TiTaskTerpilihRead.std_ai_mode`,
  `.std_dcs_flag`, `TiHasilTaskRead.dcs_flag_count` bersumber dari `openapi.json` backend. Regen via
  `npm run gen:api` **setelah** item 039 mendarat & `openapi/openapi.json` diperbarui. Sampai saat itu,
  langkah AI/DCS tidak bisa diselesaikan tuntas tanpa error tipe (lihat Risiko).

### Test terdampak ✓
- `src/test/taskinv-form-schema.test.ts`:
  - `VALID_DETAIL` berisi `frekuensi_teks: "Mingguan"` **line 16**, `ai_mode: "Human-led"` **line 20**,
    `dcs_flag: false` **line 22** ✓
  - `it("menolak enum ai_mode/va_type yang salah")` **line 65-68** (menguji `ai_mode: "X"` → false) ✓
  - `it("menolak frekuensi kosong")` **line 74-76** ✓
  - `it("menerapkan default peak4w_hours & dcs_flag")` **line 78-87** (assert `dcs_flag === false`) ✓
- `src/test/detail-form-default-unchecked.test.tsx`:
  - `taskBerstandar` berisi `std_frekuensi_teks: "Mingguan"` **line 29**, `std_ai_mode: "Human-led"`
    **line 33**, `std_dcs_flag: false` **line 35** ✓
- `src/test/tahap3-data.test.ts`: memakai objek task minimal (`{ kode: "TIa" }`) via `as`-cast/mock —
  **tidak** menyentuh `ai_mode`/`dcs_flag`/`frekuensi` secara langsung. Kemungkinan tidak perlu diubah;
  **verifikasi** setelah regen (bila tipe berubah membuat mock error). ✓

---

## Langkah eksekusi

> **Urutan disarankan:** kerjakan **Langkah 1 (Frekuensi) lebih dulu** — independen, tidak diblokir,
> bisa di-commit & dirilis sendiri. **Langkah 2 (AI/DCS)** menunggu item 039 mendarat + `gen:api`.
> Boleh dipisah menjadi dua PR.

### Langkah 1 — Frekuensi jadi dropdown (SIAP DIEKSEKUSI, independen dari 039)

#### 1.1 Definisikan konstanta terpusat
Di `src/components/calhr.ts`, tambahkan:
```ts
export const FREKUENSI = ["Harian", "Mingguan", "Semesteran", "Insidental"] as const;
```

#### 1.2 Tahap 3 (`detail-form.tsx`)
- Tambahkan `FREKUENSI` ke import baris 9 (`import { AI_MODE, FREKUENSI, KONDISI, SUMBER_BUKTI, VA_TYPE } …`).
- Zod (line 17): **tidak diubah** — tetap `z.string().min(1, "Frekuensi wajib diisi").max(100)`.
- Ganti render Frekuensi (line 364-373) dari `<input type="text">` menjadi `<select>` bergaya
  `selectCls`, mempertahankan `disabled={terkunci}` dan `onChange` yang mem-`update` `frekuensi_teks`.
  Terapkan pola fallback nilai lama (lihat 1.4).

#### 1.3 Master Data (`uraian-tugas-form.tsx`)
- Tambahkan `FREKUENSI` ke import baris 12.
- Zod (line 28): **tidak diubah** — tetap `z.string().max(100).optional()`.
- Ganti render `std_frekuensi_teks` (line 367-378) dari `<input type="text" placeholder="cth. Mingguan">`
  menjadi `<select>` dengan opsi pertama `<option value="">— tidak ada standar —</option>` (konsisten
  dengan `std_sumber_bukti`/`std_kondisi`/`std_ai_mode` lain di form ini yang optional) diikuti map
  `FREKUENSI`. Terapkan fallback nilai lama (1.4).

#### 1.4 Fallback nilai frekuensi lama yang tak ada di 4 opsi
Sebelum me-render opsi, hitung daftar opsi efektif agar nilai tersimpan yang tak cocok tetap tampil:
```tsx
// Tahap 3 — nilai wajib terisi
const opsiFrek = FREKUENSI.includes(r.frekuensi_teks as (typeof FREKUENSI)[number])
  ? FREKUENSI
  : [r.frekuensi_teks, ...FREKUENSI];
// render: opsiFrek.map((v) => <option key={v}>{v}</option>)
```
Untuk Master Data (nilai boleh kosong), sisipkan `<option value="">— tidak ada standar —</option>`
di atas, lalu opsi tambahan hanya bila `std_frekuensi_teks` non-kosong & tak ada di `FREKUENSI`.
Tujuannya: record lama ("Bulanan", dll.) tidak diam-diam berubah nilai saat form dibuka lalu disimpan.

#### 1.5 Test Frekuensi
- `taskinv-form-schema.test.ts`: tambahkan test bahwa `frekuensi_teks` **string bebas tetap diterima**
  (mis. `{ ...VALID_DETAIL, frekuensi_teks: "Bulanan" }` → `success === true`) — mengunci keputusan
  "tetap string, bukan enum". Pertahankan test "menolak frekuensi kosong" (line 74-76).
- (Opsional) test render `detail-form-*.test.tsx`: pastikan `<select>` Frekuensi ada dan memuat 4 opsi.

### Langkah 2 — Hapus AI Mode & Risiko DCS (BLOCKED BY 039)

> Kerjakan **hanya setelah** item 039 (backend) mendarat & `openapi/openapi.json` diperbarui, lalu
> jalankan `npm run gen:api`. Tanpa itu `tsc` akan error: tipe `TiDetailItem`/`TiTaskTerpilihRead`/
> `TiHasilTaskRead` masih memuat field yang kode ini hapus (atau sebaliknya). Lihat Risiko.

#### 2.1 Tahap 3 (`detail-form.tsx`) — cabut AI Mode & DCS
- Import (line 9): buang `AI_MODE` (sisakan `FREKUENSI, KONDISI, SUMBER_BUKTI, VA_TYPE`).
- Zod: hapus `ai_mode:` (line 21) & `dcs_flag:` (line 29).
- `RowState`: hapus `ai_mode` (line 43) & `dcs_flag` (line 45).
- `punyaStandar()`: hapus klausa `t.std_ai_mode != null` (line 57) & `t.std_dcs_flag != null` (line 59).
- `rowDariStandar()`: hapus `ai_mode:` (line 79) & `dcs_flag:` (line 81).
- Seed `existing`: hapus `ai_mode:` (line 108) & `dcs_flag:` (line 110).
- `buildDetailPayload()`: hapus `ai_mode:` (line 151) & `dcs_flag:` (line 153).
- Render: hapus blok `<select>` AI Mode (line 415-429) & blok checkbox "Ada risiko DCS" (line 445-454).

#### 2.2 Master Data (`uraian-tugas-form.tsx`) — cabut std AI Mode & std DCS
- Import (line 12): buang `AI_MODE`.
- Zod: hapus `std_ai_mode` (line 32) & `std_dcs_flag` (line 34).
- `onSubmit` body: hapus `std_ai_mode:` (line 116) & `std_dcs_flag:` (line 118).
- Render: hapus blok `<select>` std_ai_mode (line 425-441) & blok checkbox std_dcs_flag (line 461-471).

#### 2.3 Master Data edit (`[id]/page.tsx`) — defaultValues
- Hapus `std_ai_mode:` (line 81) & `std_dcs_flag:` (line 83) dari `defaultValues`.

#### 2.4 Hasil agregasi TI (`[sesi_id]/page.tsx`) — hapus kolom DCS
- Hapus header `<th>…DCS…</th>` di `thead` Hasil Agregasi dan sel `<td>{t.dcs_flag_count > 0 ? …}</td>`
  (line 440). Pastikan jumlah kolom `thead`/`tbody` tetap seimbang.

#### 2.5 Bersihkan konstanta yang jadi yatim
- Setelah semua pemakaian `AI_MODE` nol, **hapus** `export const AI_MODE` dari `src/components/calhr.ts`
  (line 3). Verifikasi `grep -rn "AI_MODE" src` → nol hasil sebelum menghapus.

#### 2.6 Regen skema & rapikan test
- `npm run gen:api` (butuh `openapi/openapi.json` dari backend ber-039).
- `taskinv-form-schema.test.ts`: buang `ai_mode`/`dcs_flag` dari `VALID_DETAIL`; ganti test
  "menolak enum ai_mode/va_type" (line 65) menjadi hanya `va_type`; buang assertion `dcs_flag` dari
  test default (line 85), sisakan `peak4w_hours`.
- `detail-form-default-unchecked.test.tsx`: buang `std_ai_mode` (line 33) & `std_dcs_flag` (line 35)
  dari `taskBerstandar`.
- `tahap3-data.test.ts`: jalankan; sesuaikan bila mock jadi tak sesuai tipe hasil regen.

---

## Kriteria penerimaan

**Langkah 1 (Frekuensi) — dapat diverifikasi tanpa 039:**
- [ ] Field "Frekuensi" di Tahap 3 (`detail-form.tsx`) adalah `<select>` dengan 4 opsi
      Harian/Mingguan/Semesteran/Insidental (urutan itu).
- [ ] Field "Frekuensi" di Master Data (`uraian-tugas-form.tsx`) adalah `<select>` yang sama, ditambah
      opsi "— tidak ada standar —" (nilai kosong).
- [ ] Membuka record lama ber-frekuensi di luar 4 opsi (mis. "Bulanan") **menampilkan** nilai itu di
      `<select>` (opsi tambahan), tidak diam-diam berubah ke opsi pertama.
- [ ] Default seed tetap "Mingguan"; `frekuensi_teks` tetap `string` di payload (bukan enum).
- [ ] `FREKUENSI` didefinisikan sekali di `calhr.ts` dan dipakai di kedua form.

**Langkah 2 (AI/DCS) — setelah 039:**
- [ ] Tidak ada dropdown "AI Mode" maupun checkbox "Ada risiko DCS" di Tahap 3.
- [ ] Tidak ada input std_ai_mode / std_dcs_flag di form Master Data Uraian Tugas.
- [ ] Kolom "DCS" hilang dari tabel Hasil Agregasi TI (`[sesi_id]/page.tsx`).
- [ ] `grep -rn "ai_mode\|dcs_flag\|AI_MODE" src` → **nol hasil** (setelah `gen:api` skema bersih).
- [ ] `tsc --noEmit` hijau (tidak ada referensi ke field yang sudah tak ada di skema).

## Skenario uji

- `src/test/taskinv-form-schema.test.ts`
  - (L1) Tambah: `frekuensi_teks` string bebas ("Bulanan") tetap `success === true`; "" tetap `false`.
  - (L2) Hapus assertion `ai_mode`/`dcs_flag`; sisakan `va_type` & `peak4w_hours`.
- `src/test/detail-form-default-unchecked.test.tsx`
  - (L2) Hapus `std_ai_mode`/`std_dcs_flag` dari fixture; test perilaku checkbox tetap lulus.
- `src/test/tahap3-data.test.ts` — jalankan; sesuaikan hanya bila regen tipe memaksanya.
- (Opsional, L1) test render baru: `<select>` Frekuensi memuat 4 opsi + fallback nilai lama.
- Perintah gate: `make test` (lint + typecheck + unit, di Docker) **dan** `npm run build`.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-web-app`.
- [ ] `npm run build` sukses.
- [ ] `CHANGELOG.md` diperbarui.
- [ ] `CLAUDE.md` repo web-app diperbarui bila alur/skema berubah (tambah entri "Revisi Desain"
      ringkas: AI Mode & DCS dicabut dari Tahap 3; Frekuensi jadi dropdown terkontrol).
- [ ] `docs-usage/` disesuaikan bila layar Tahap 3 / Master Data Uraian Tugas didokumentasikan.
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md` (bila Langkah 1 & 2 sudah kelar; bila hanya
      Langkah 1 dulu, catat statusnya sebagai parsial di indeks).

## Risiko & catatan

- **Ketergantungan 039 hanya untuk AI/DCS.** Menghapus pemakaian `ai_mode`/`dcs_flag` di web-app
  **sebelum** backend berhenti mengirim/menerima field itu masih aman untuk *mengirim* (tidak
  menyertakan field opsional), **tetapi** `src/lib/api/schema.ts` masih mendeklarasikan field itu
  hingga `gen:api` dijalankan atas `openapi.json` ber-039. Jangan meng-edit `schema.ts` tangan untuk
  "mempercepat" — itu artefak generate dan akan tertimpa. Karena itu Langkah 2 **menunggu** 039.
- **Frekuensi independen & tidak berisiko hitung.** `frekuensi_teks` tidak dipakai di agregasi apa pun
  (jam murni dari `jam_per_minggu` × 45 minggu efektif) — mengubah input jadi dropdown **tidak**
  memengaruhi `total_jam_per_minggu`/`total_jam_per_tahun`/`durasi_per_kali_mean`. Aman dirilis lebih
  dulu, terpisah dari 039.
- **Data historis frekuensi bebas** ("Bulanan", "2 mingguan", dsb.) tetap sah tersimpan; fallback di
  Langkah 1.4 memastikan record lama tidak korup saat form dibuka & disimpan ulang. Jangan mengganti
  zod `frekuensi_teks` menjadi `z.enum` — itu akan menolak record lama.
- **Jangan sentuh `master-data/uraian-tugas/page.tsx` line 96** — badge "Standar" membaca
  `std_frekuensi_teks` yang tetap ada; bukan bagian dari perubahan ini.
- **Interaksi dengan backlog 033** (kebocoran `disabled` "Setuju dengan isian standar" & semantik
  durasi standar) — berbagi file `detail-form.tsx`. Bila 033 dikerjakan berdekatan, koordinasikan edit
  agar tidak bentrok pada blok render CalHR yang sama.
- **Jaring pengaman jalur baca (CLAUDE.md web-app)** tidak terdampak — perubahan ini tidak menambah
  jalur baca `?? []`. Tetap jalankan `make test` yang memuat `jaring-pengaman-jalur-baca.test.ts`.
