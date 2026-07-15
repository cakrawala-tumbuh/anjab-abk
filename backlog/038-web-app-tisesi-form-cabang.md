# Backlog 038 — Form "Mulai Analisis Jabatan" (TI): Periode → Cabang, buang Min/Maks Responden

> **Repo:** `anjab-abk-web-app`
> **Status:** Menunggu (blocked by 037)
> **Blocked by:** 037 (backend: ganti `periode`→`cabang` di TI + hapus `min/max_responden` + regen `openapi.json`)
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Menindaklanjuti feedback user (foto tulisan tangan, 2026-07-14) tentang form **"Mulai Analisis
Jabatan"** dan listing awal Task Inventory. Tiga perubahan tampilan, semuanya di frontend,
**menyusul** perubahan kontrak backend item 037:

1. Field **"Periode"** (input teks `YYYY-MM`) diganti dropdown **"Cabang"** dengan **dua opsi:
   Bandung, Semarang**.
2. Field **"Min. Responden"** dan **"Maks. Responden"** **dihapus** dari form.
3. Halaman **listing** Task Inventory: kolom **"Periode"** diganti **"Cabang"**.

Perubahan ini murni konsekuensi dari perubahan model backend (item 037): studi ANJAB/ABK di YPII
dijalankan per **cabang** (Bandung / Semarang), bukan per periode bulanan; dan jumlah responden TI
sudah selalu = seluruh anggota SME panel (auto-populate, item 028), sehingga `min/max_responden`
tidak lagi punya makna operasional.

## Keputusan yang sudah dikunci

Agen pelaksana **tidak** perlu menginterpretasi ulang keputusan-keputusan berikut:

1. **Dropdown "Cabang" = tepat 2 opsi statis: `Bandung`, `Semarang`.** Field **wajib** (tidak boleh
   kosong). Nilai literal yang dikirim ke backend **mengikuti kontrak 037** — baca ulang
   `TiSesiCreate` di `src/lib/api/schema.ts` **setelah** `gen:api`. Jika backend mendefinisikan enum
   `"Bandung" | "Semarang"`, kirim persis itu (case-sensitive). **Jangan menebak** casing/format —
   verifikasi ke schema hasil regen.
2. **`min_responden` & `max_responden` dihapus tuntas dari form** — bukan disembunyikan. Ini
   mencakup: field render, aturan zod (`min_responden`, `max_responden`, `.refine` max≥min),
   `defaultValues`, payload POST, **dan** prefill panel-aware fitur 030 (prop `petaAnggota` +
   `useEffect` yang mem-`setValue("max_responden")`).
3. **`SmePanelInfo` DIHAPUS dari form TI.** Alasan: satu-satunya fungsinya (fitur 030) adalah
   memandu pengisian `max_responden` — teks komponennya secara eksplisit berbunyi *"…jadi Maks.
   Responden diisi {jumlah}…"* (`src/components/sme-panel-info.tsx:29-30`). Tanpa field
   `max_responden`, keterangan itu jadi menyesatkan.
   - **Komponen `src/components/sme-panel-info.tsx` TIDAK dihapus dan TIDAK diubah** — masih dipakai
     **identik oleh form OPM** (`opm/buat/opm-sesi-form.tsx`), yang **di luar cakupan** item ini.
   - **`src/lib/sme-panel.ts` (`petaJumlahAnggotaPanel`, `jumlahAnggotaPanel`, `PetaAnggotaPanel`)
     TIDAK dihapus** — masih dipakai OPM.
   - Bila kelak user ingin panel-size tetap tampil di form TI sebagai info murni, itu **item
     terpisah** (butuh teks baru yang tidak menyebut `max_responden`). Jangan dikerjakan di sini.
4. **Scope = TI saja.** Form OPM (`opm/buat/`) dan listing OPM **tidak disentuh** — item 037 (per
   deskripsinya) hanya mengubah kontrak TI. Jangan meng-generalisasi ke OPM tanpa item backend
   yang mendasarinya.
5. **Invariant jalur baca (026/029/031) tetap berlaku.** Setiap fetch yang disentuh wajib
   `if (!res.data) throw apiErrorDari(res);` — jangan memperkenalkan `?? []`/`?? null`.
6. **`schema.ts` TIDAK diedit tangan** — hanya lewat `npm run gen:api` dari `openapi.json` versi
   037. Item ini **tidak boleh dimulai** sebelum `openapi.json` baru tersedia (lihat Risiko).

## Kondisi sekarang (verified)

Baris bisa bergeser — agen pelaksana WAJIB baca ulang file sebelum mengedit.

### Form: `src/app/(auth)/task-inventory/buat/ti-sesi-form.tsx` ✓

| Fakta | Lokasi (verified 2026-07-15) |
|---|---|
| zod `periode` (regex `^\d{4}-\d{2}$`, min/max 7) | baris 19-23 ✓ |
| zod `min_responden` (`.default(3)`) | baris 24-28 ✓ |
| zod `max_responden` (`.default(10)`) | baris 29-33 ✓ |
| `.refine(max ≥ min)` | baris 36-39 ✓ |
| Props `petaAnggota: PetaAnggotaPanel` | baris 44-46 ✓ |
| `defaultValues: { jabatan_id:"", min_responden:3, max_responden:10 }` | baris 73 ✓ |
| `watch("jabatan_id")` → `jumlahAnggota` (dipakai HANYA utk panel/prefill) | baris 76-77 ✓ |
| `useEffect` prefill `max_responden` = jumlah anggota (fitur 030) | baris 82-86 ✓ |
| payload POST: `periode` (95), `min_responden` (96), `max_responden` (97) | baris 92-100 ✓ |
| `<SmePanelInfo jumlah={jumlahAnggota} />` | baris 137 ✓ |
| render input **"Periode *"** | baris 145-165 ✓ |
| render dua input **Min/Maks Responden** | baris 167-205 ✓ |
| field `catatan` (dipertahankan) | baris 207-218 ✓ |

### Parent page: `src/app/(auth)/task-inventory/buat/page.tsx` ✓

- `fetchPageData` mem-fetch **dua** endpoint: `catalog/kombinasi` **dan** `GET /api/v1/sme-panel`
  (untuk `petaAnggota`), baris 16-29 ✓.
- Mem-`petaJumlahAnggotaPanel(...)` dan meneruskan prop `petaAnggota` ke `<TiSesiForm>`, baris
  28 & 56-60 ✓.
- Subtext halaman menyebut *"…beserta periode…"*, baris 50-53 ✓.
- Impor `petaJumlahAnggotaPanel`, `PetaAnggotaPanel`, `SMEPanelRead`, baris 6-7 ✓.

### Listing: `src/app/(auth)/task-inventory/page.tsx` ✓

- Header kolom **"Periode"**, baris 65-67 ✓.
- Nilai sel `{s.periode}` dengan class `font-mono`, baris 92 ✓.

### Schema & tooling ✓

- `TiSesiCreate` saat ini punya `periode: string`, `min_responden`, `max_responden`
  (`src/lib/api/schema.ts:4923-4961`) ✓ — akan berubah oleh 037.
- `gen:api` = `openapi-typescript ./openapi/openapi.json -o ./src/lib/api/schema.ts`
  (`package.json:14`) ✓. Butuh `openapi/openapi.json` versi 037 (Gotcha CLAUDE.md).

### Test yang terdampak ✓

- `src/test/ti-sesi-form.test.tsx` ✓ — sangat bergantung pada field lama: helper `isiPeriode()`
  (baris 38-40), `maxInput()` (46-48), `petaAnggota={ jbt_gr_sd: 11 }` (30), assertion prefill
  `maxInput().value === "11"` (67,74), `max_responden: 11` di payload (91), dan blok **"422 backend
  tampil utuh"** yang berbasis pesan `max_responden` (116-143). **Perlu ditulis ulang.**
- `src/test/taskinv-form-schema.test.ts` ✓ — `VALID_SESI` berisi `periode/min/max` (5-10), test
  *"menolak format periode yang salah"* (35-39), *"menolak max < min"* (41-51). **Perlu diperbarui.**
- `src/test/sme-panel.test.ts` — menguji `src/lib/sme-panel.ts` yang **tetap dipakai OPM**; **jangan
  diubah** kecuali gagal (seharusnya tidak).

## Langkah eksekusi

> **PRA-SYARAT MUTLAK:** item 037 sudah rilis dan `anjab-abk-web-app/openapi/openapi.json` sudah
> diperbarui ke kontrak baru. Jalankan `npm run gen:api` **lebih dulu**, lalu baca `TiSesiCreate`
> hasil regen untuk memastikan nama field (`cabang`) & tipe nilai (enum Bandung/Semarang) sebelum
> menyentuh komponen. Jika `openapi.json` belum berubah, **STOP** — item masih terblokir.

### Langkah 0 — Regenerasi schema

1. Pastikan `openapi/openapi.json` sudah versi 037 (field TI: `cabang`, tanpa `min/max_responden`).
2. `npm run gen:api`.
3. Baca `TiSesiCreate` di `src/lib/api/schema.ts`: konfirmasi field `cabang` + tipe nilainya, dan
   konfirmasi `min_responden`/`max_responden` sudah hilang. Konfirmasi `TiSesiRead` punya `cabang`
   (untuk listing).

### Langkah 1 — `ti-sesi-form.tsx`: Periode→Cabang, buang Min/Maks & panel-aware

Di `src/app/(auth)/task-inventory/buat/ti-sesi-form.tsx`:

1. **Zod `schema`**:
   - Hapus blok `periode`, ganti dengan `cabang: z.enum(["Bandung", "Semarang"], { … })` (atau
     `z.string().min(1)` bila kontrak backend bukan enum ketat — samakan dengan schema hasil regen).
     Sesuaikan pesan "Cabang wajib dipilih".
   - Hapus `min_responden`, `max_responden`, dan `.refine(max ≥ min)`. Setelah `.refine` hilang,
     `z.object({...})` cukup diakhiri tanpa `.refine`.
2. **Props**: hapus `petaAnggota` dari `interface Props` dan destructuring.
3. **`defaultValues`**: jadi `{ jabatan_id: "", cabang: "" }` (atau tanpa `cabang` bila enum tanpa
   default — pastikan dropdown punya opsi placeholder `-- Pilih cabang --`).
4. **Hapus** blok `watch("jabatan_id")` + `jumlahAnggota` (baris 76-77) **dan** `useEffect` prefill
   (baris 82-86), plus impor `jumlahAnggotaPanel`, `PetaAnggotaPanel`, `SmePanelInfo` yang tak lagi
   dipakai. (Impor `useEffect`/`setValue`/`watch` juga dibuang bila jadi unused — biarkan lint
   memandu.)
5. **Payload `onSubmit`**: hapus `periode`, `min_responden`, `max_responden`; tambahkan
   `cabang: values.cabang`. Pertahankan `jabatan_id`, `catatan`.
6. **Render**:
   - Hapus `<SmePanelInfo … />` (baris 137).
   - Ganti blok input "Periode" (145-165) dengan `<select>` "Cabang *" berisi opsi placeholder +
     `Bandung` + `Semarang`, pakai `{...register("cabang")}`, `aria-invalid`, dan `<p className="form-error">`
     untuk `errors.cabang`. Ikuti pola markup `<select>` "Jabatan" yang sudah ada di file yang sama
     (baris 124-136) agar konsisten.
   - Hapus seluruh blok dua input Min/Maks Responden (167-205).
   - Field "Catatan" dan tombol submit/batal tidak berubah.

### Langkah 2 — `buat/page.tsx`: berhenti fetch/teruskan panel

Di `src/app/(auth)/task-inventory/buat/page.tsx`:

1. `fetchPageData`: hapus fetch `GET /api/v1/sme-panel` dan komputasi `petaAnggota`; kembalikan
   hanya `{ kombinasi }`. Pertahankan guard `if (!kombinasiRes.data) throw apiErrorDari(...)`.
2. Hapus impor `petaJumlahAnggotaPanel`, `PetaAnggotaPanel`, `SMEPanelRead` yang jadi unused.
3. Hapus prop `petaAnggota={...}` dari `<TiSesiForm>`.
4. Ubah subtext (baris 50-53): *"…beserta periode…"* → *"…beserta cabang…"* (kalimat disesuaikan).

### Langkah 3 — `task-inventory/page.tsx` (listing): Periode→Cabang

Di `src/app/(auth)/task-inventory/page.tsx`:

1. Header kolom (baris 65-67): "Periode" → "Cabang".
2. Nilai sel (baris 92): `{s.periode}` → `{s.cabang}`. Pertimbangkan menghapus class `font-mono`
   (nilai bukan lagi kode `YYYY-MM` monospace; teks biasa lebih cocok). Bila `TiSesiRead.cabang`
   bisa null di kontrak 037, tampilkan fallback `{s.cabang ?? "—"}`.

### Langkah 4 — Perbarui test

1. **`src/test/taskinv-form-schema.test.ts`**:
   - `VALID_SESI`: buang `periode/min_responden/max_responden`, tambah `cabang: "Bandung"`.
   - Hapus test *"menolak format periode yang salah"* dan *"menolak max < min"*.
   - Tambah test: menerima `cabang` valid (`Bandung`/`Semarang`); menolak `cabang` kosong/tidak
     dikenal (mis. `"Jakarta"`).
2. **`src/test/ti-sesi-form.test.tsx`** — tulis ulang:
   - Buang helper `isiPeriode`, `maxInput`, prop `petaAnggota`, semua assertion prefill/panel, dan
     blok "422 backend tampil utuh" berbasis `max_responden`.
   - Test baru minimal:
     - Dropdown "Cabang" merender **dua** opsi (`Bandung`, `Semarang`) + placeholder.
     - Input "Periode", "Min. Responden", "Maks. Responden" **tidak ada** di DOM
       (`queryByLabelText(/Periode|Responden/)` → null).
     - `SmePanelInfo` tidak dirender (`queryByTestId("sme-panel-info")` → null).
     - Submit sukses mengirim payload `{ jabatan_id, cabang }` (tanpa `periode/min/max`) lalu
       `push("/task-inventory/<id>")`.
     - Regresi notifikasi (026/017): 4xx/5xx menampilkan `toast.error` + error inline (pola sama
       seperti test lama, tapi tanpa konteks `max_responden`).

### Langkah 5 — Dokumentasi & changelog

1. `docs-usage/` bila ada layar/langkah yang berubah (skill `dokumentasi-penggunaan`): IK Task
   Inventory yang menyebut "Periode"/"Min/Maks Responden" → "Cabang".
2. Tambah entri "Revisi Desain" di `CLAUDE.md` repo web app (ringkas keputusan 1-6 di atas).
3. `CHANGELOG.md`.

## Kriteria penerimaan

- [ ] Form "Mulai Analisis Jabatan" menampilkan dropdown **"Cabang"** dengan **tepat 2 opsi**
      (Bandung, Semarang) + placeholder; field wajib.
- [ ] Input **"Periode"**, **"Min. Responden"**, **"Maks. Responden"** **tidak ada** di form.
- [ ] `SmePanelInfo` tidak lagi dirender di form TI; komponen & pemakaian OPM **tetap utuh**.
- [ ] Submit form mengirim payload berisi `cabang` (nilai sesuai kontrak 037), **tanpa** `periode`/
      `min_responden`/`max_responden`.
- [ ] Listing `/task-inventory` menampilkan kolom **"Cabang"** dengan nilai `s.cabang`.
- [ ] `buat/page.tsx` tidak lagi mem-fetch `/api/v1/sme-panel`; subtext menyebut "cabang".
- [ ] Tidak ada `?? []`/`?? null` baru di jalur baca yang disentuh (jaring pengaman
      `src/test/jaring-pengaman-jalur-baca.test.ts` hijau).
- [ ] `npm run build` sukses; `make test` hijau.

## Skenario uji

- **File test yang diperbarui**: `src/test/taskinv-form-schema.test.ts`,
  `src/test/ti-sesi-form.test.tsx` (lihat Langkah 4 untuk kasus konkret).
- **File test yang TIDAK boleh berubah**: `src/test/sme-panel.test.ts` (menjaga `sme-panel.ts` untuk
  OPM) — jika ia gagal, berarti `sme-panel.ts`/OPM tersentuh secara keliru.
- **Perintah**: `make test` (lint + typecheck + unit di Docker, identik CI) **dan** `npm run build`.
- Verifikasi manual (opsional, bila stack E2E hidup): buka `/task-inventory/buat`, pastikan dropdown
  Cabang tampil & tidak ada field Periode/Responden; buat 1 sesi cabang "Bandung", cek muncul di
  listing dengan kolom "Cabang".

## Definition of done

- [ ] `make test` hijau di `anjab-abk-web-app`
- [ ] `npm run build` sukses
- [ ] `CHANGELOG.md` diperbarui
- [ ] `CLAUDE.md` repo web app diperbarui (entri "Revisi Desain" untuk perubahan ini)
- [ ] `docs-usage/` diperbarui bila layar/langkah berubah
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **BLOKIR KERAS oleh 037.** `schema.ts` adalah artefak generate; ia **tidak bisa** diregen sampai
  backend 037 rilis `openapi.json` baru (field `cabang`, tanpa `min/max_responden`). Memulai item
  ini sebelum itu berarti menebak nama/tipe field dan mengedit `schema.ts` tangan — **dilarang**.
  Tunggu `openapi.json` berubah.
- **Nilai literal Cabang belum 100% dikunci ke kontrak.** Deskripsi feedback menyebut opsi "Bandung"
  & "Semarang", tapi casing/format nilai yang benar-benar diterima backend ditentukan 037. Langkah 0
  memaksa verifikasi ke schema hasil regen sebelum menulis `z.enum`. Bila 037 memakai enum yang
  berbeda (mis. kode/slug), samakan dropdown value dengan enum itu dan label tampilan tetap
  "Bandung"/"Semarang".
- **`TiSesiRead.cabang` bisa null?** Jika kontrak 037 menandai `cabang` opsional pada Read, listing
  wajib fallback `?? "—"` (bukan `?? []` di jalur data inti — ini fallback tampilan sel, bukan
  penelanan kegagalan API). Konfirmasi ke schema.
- **Jangan menyeret OPM.** Godaan menyamakan OPM (yang juga punya form serupa + `SmePanelInfo`) harus
  ditahan: OPM tidak punya item backend yang mengubah kontraknya di sini. Menyentuh OPM tanpa 037-nya
  akan memecah build (`schema.ts` OPM belum berubah) dan di luar cakupan feedback ini.
- **Pesan konflik dengan CLAUDE.md revisi 030.** Entri "Revisi Desain [2026-07-14] Form … sadar
  jumlah anggota SME panel" menjelaskan fitur yang **dihapus dari TI** oleh item ini. Tambahkan
  entri revisi baru yang menyatakan pencabutan itu untuk TI (OPM tetap), jangan hapus entri lama —
  ia tetap jejak keputusan & masih berlaku untuk OPM.
