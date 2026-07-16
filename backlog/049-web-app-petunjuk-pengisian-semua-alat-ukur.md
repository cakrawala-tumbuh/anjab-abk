# Backlog 049 — Web app: petunjuk pengisian di semua alat ukur (meniru DCS)

> **Repo:** `anjab-abk-web-app`
> **Status:** Siap dieksekusi
> **Blocked by:** — (murni presentasi; tidak menyentuh backend / `openapi.json` / `schema.ts`)
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`, `dokumentasi-penggunaan-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Halaman pengisian **DCS** (`/dcs/isi/[responden_id]`) sudah punya pop-up **"Petunjuk
Pengisian"** (backlog 046, rilis 2026-07-15): modal hand-rolled yang auto-muncul tiap kunjungan
selama belum submit, plus tombol pemicu yang selalu terlihat. Alat ukur lain — **WCP, OPM,
Time Study, dan Task Inventory Tahap 1/2/3** — **belum punya** petunjuk apa pun; partisipan
(mayoritas guru/staf yayasan, bukan psikolog/analis) langsung dihadapkan ke form tanpa
penjelasan cara mengisi, sehingga kualitas & konsistensi jawaban rentan.

Terapkan pola petunjuk gaya-DCS ke **semua alat ukur**. Khusus **Task Inventory, buat petunjuk
di semua tahapan** (Tahap 1 seleksi, Tahap 2 review koordinator, Tahap 3 detailing).

## Keputusan yang sudah dikunci

> Dikonfirmasi user 2026-07-16. Agen pelaksana TIDAK boleh menawar ulang.

1. **Auto-muncul ikut pola DCS** — pop-up muncul otomatis tiap kunjungan **selama alat ukur
   masih bisa diisi**; tombol "Petunjuk Pengisian" selalu terlihat untuk membuka lagi. **Tanpa
   `localStorage`, tanpa "jangan tampilkan lagi"** (konsisten dengan keputusan DCS 046).
2. **Komponen bersama + refactor DCS** — ekstrak mekanik modal ke satu komponen bersama
   `PetunjukModal`; **DCS ikut di-refactor** memakainya. Konten per alat ukur diisi sebagai
   `children`. Satu implementasi modal untuk 7 alat ukur.
3. **Cakupan: DCS (refactor) + WCP + OPM + Time Study + TI Tahap 1/2/3.** Konten statis,
   non-interaktif (contoh = ilustrasi, bukan input yang bisa diklik). **Tanpa dependency baru**
   (tak ada shadcn/radix di repo; pola overlay hand-rolled meniru `app-shell.tsx`).
4. **`defaultOpen` per alat ukur** — lihat tabel di "Langkah eksekusi". TS & TI-2 memakai
   interpretasi eksplisit "selama masih bisa diisi" (lihat catatan).

## Kondisi sekarang (verified)

> Agen pelaksana WAJIB membaca ulang tiap file sebelum mengedit — baris bisa bergeser.

| Fakta | Lokasi | ✓ |
|---|---|---|
| Komponen petunjuk DCS (template) — hand-rolled modal, props `{defaultOpen}`, mekanik: trigger `HelpCircle`+"Petunjuk Pengisian", backdrop `fixed inset-0 z-50 bg-black/50`, panel `role="dialog" aria-modal aria-labelledby`, X `aria-label="Tutup"`, Escape, CTA "Saya Mengerti, Mulai Mengisi" | `src/app/(auth)/dcs/isi/[responden_id]/petunjuk-dcs.tsx` (1-219) | ✓ |
| Test DCS yang WAJIB tetap hijau tanpa diubah (mengunci label & struktur: `role="dialog"` anak langsung backdrop via `dialog.parentElement`, nama tombol "Tutup"/"Petunjuk Pengisian"/"Saya Mengerti, Mulai Mengisi") | `src/test/petunjuk-dcs.test.tsx` (1-48) | ✓ |
| WCP fill page — header `<div><h1/><p/></div>`, `responden.sudah_submit`; skala 1–5 label di form; 12 dimensi (`SC…RA`), sebagian `is_risk` "Dimensi Risiko" | `wcp/isi/[responden_id]/page.tsx:77-99`, `wcp-form.tsx:10-16`, `:166-172` | ✓ |
| WCP nama lengkap = **Workplace Climate Profile** | `wcp/page.tsx:83` (`WCP — Workplace Climate Profile`) | ✓ |
| OPM fill page — `responden.sudah_submit`; 3 dimensi Importance/Frequency/Criticality dgn anchor 1&5; catatan opsional; "Simpan" MEMBUANG task belum lengkap 3 dimensi | `opm/isi/[responden_id]/page.tsx:63-66`, `opm-form.tsx:19-32`, `:125-134` | ✓ |
| TS fill = **daftar log** + tombol "+ Tambah Log"; header sudah `flex justify-between`; `penugasan.aktif`, `logs.length`; 6 kategori & 3 warna hari di form tambah | `time-study/isi/[penugasan_id]/page.tsx:70-83`, `.../tambah/ts-log-form.tsx:13-20`, `:211-214` | ✓ |
| TI Tahap 1 — header `<div><h1/><p/></div>`, `responden.tahap1_submit`, `sesi.status`; wizard 3 level Tugas Pokok→Detil→Uraian | `task-inventory/tahap1/[responden_id]/page.tsx:52-74`, `seleksi-form.tsx:30-38` | ✓ |
| TI Tahap 2 — `canEdit` (admin/koordinator) & `readOnly` dihitung di page; `sesi.status`; rasio `n_relevan/n_total`; task partial vs unanimous | `task-inventory/tahap2/[sesi_id]/page.tsx:84-113`, `review-form.tsx:148-150` | ✓ |
| TI Tahap 3 — `responden.tahap3_submit`, `sesi.status`; kolom CalHR (Sumber Bukti/Kondisi/Frekuensi/Durasi/Jam·mgg/Jam peak/VA Type); "Setuju dengan isian standar" | `task-inventory/tahap3/[responden_id]/page.tsx:52-58`, `detail-form.tsx:256-262`, `:319-423`, `@/components/calhr` | ✓ |
| Utility: `cn()` di `@/lib/utils`; ikon `HelpCircle`,`X` dari `lucide-react`; kartu-aksen `rounded-md bg-blue-50 … dark:bg-blue-950/40`; gaya pil `dcs-form.tsx:178-190` | — | ✓ |
| Komponen ini murni presentasi — **tidak** memanggil backend → aturan jalur-baca (`?? []`) & `notify*` tidak relevan | — | ✓ |

## Langkah eksekusi

### Langkah 1 — Komponen bersama `src/components/petunjuk-modal.tsx` (`"use client"`)

Ekstrak mekanik modal dari `petunjuk-dcs.tsx` **apa adanya**. Props:

```ts
interface Props {
  title: string;            // dirender <h2 id={useId()}> + aria-labelledby
  defaultOpen: boolean;
  children: ReactNode;      // isi petunjuk per alat ukur
  ctaLabel?: string;        // default "Saya Mengerti, Mulai Mengisi"
  triggerLabel?: string;    // default "Petunjuk Pengisian"
}
```

**Invariant WAJIB dipertahankan** (agar `petunjuk-dcs.test.tsx` tetap hijau tanpa diubah):
- Tombol pemicu `triggerLabel` (ikon `HelpCircle`, selalu terlihat) → `setOpen(true)`; gaya
  garis + `cn()` seperti `petunjuk-dcs.tsx:57-67`.
- `const [open, setOpen] = useState(defaultOpen)` (auto-buka sekali per mount).
- Saat `open`: backdrop `fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4`
  (klik → tutup) **membungkus** panel `role="dialog" aria-modal="true" aria-labelledby={id}`
  `w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-lg bg-white p-6 shadow-xl
  dark:border dark:border-gray-700 dark:bg-gray-900` (`stopPropagation`). Dialog **anak
  langsung** backdrop.
- `<h2 id={id}>` = `title`; tombol X `aria-label="Tutup"`; Escape menutup (`useEffect`
  listener `keydown` saat `open`); CTA `ctaLabel` di bawah konten → `setOpen(false)`.
- Tanpa portal. Tanpa dependency baru.

### Langkah 2 — Refactor `petunjuk-dcs.tsx`

`PetunjukDcs({ defaultOpen })` me-render `<PetunjukModal title="Petunjuk Pengisian Kuesioner
DCS" defaultOpen={defaultOpen}>{…konten DCS…}</PetunjukModal>`. Pindahkan blok konten
(`CONTOH`, `SKALA`, pengantar, petunjuk umum, skala, cara menjawab, contoh) ke `children`
**tanpa mengubah teks**. `dcs/isi/[responden_id]/page.tsx` **tidak** berubah.

### Langkah 3 — Komponen konten baru (satu per alat ukur), co-located

Semua memanggil `<PetunjukModal title=… defaultOpen={defaultOpen}>…</PetunjukModal>` dan memakai
kartu-aksen lazim repo + (bila ada skala) pil non-interaktif meniru `dcs-form.tsx:178-190`.
Konten statis, Bahasa Indonesia, gaya petunjuk instrumen. Props tiap komponen: `{ defaultOpen:
boolean }`.

**3a. `wcp/isi/[responden_id]/petunjuk-wcp.tsx`** — title *"Petunjuk Pengisian Kuesioner WCP"*.
- Pengantar: **WCP (Workplace Climate Profile)** memotret persepsi Anda terhadap iklim/suasana
  tempat kerja pada beberapa dimensi (sebagian ditandai **"Dimensi Risiko"** — hanya penanda
  kelompok; cara menjawab sama). Bukan tes; tidak ada jawaban benar/salah.
- Petunjuk Umum (sama semangat DCS): baca saksama; jawab sesuai pengalaman nyata; tidak ada
  benar/salah; spontan; isi **semua pernyataan** ("Kirim Jawaban" aktif bila semua terjawab,
  bisa "Simpan"); jawaban rahasia.
- Skala 1–5 (identik DCS, `wcp-form.tsx:10-16`): 1 Sangat Tidak Setuju … 5 Sangat Setuju.
- Cara Menjawab: baca → renungkan → klik 1–5 → lanjut.
- **2 contoh non-interaktif**: A pernyataan iklim positif → pil **5** tersorot; B pernyataan
  beban berlebih (nuansa dimensi risiko) → pil **2** tersorot. Catatan: contoh hanya ilustrasi.

**3b. `opm/isi/[responden_id]/petunjuk-opm.tsx`** — title *"Petunjuk Pengisian Kuesioner OPM —
Rating Tugas"*.
- Pengantar: OPM menilai tiap tugas jabatan pada **tiga dimensi**, masing-masing skala 1–5.
- Arti tiga dimensi (anchor dari `opm-form.tsx:19-32`): **Importance** 1 Tidak penting … 5
  Sangat penting; **Frequency** 1 Insidental … 5 Sangat sering/Harian; **Criticality** 1
  Dampak minimal … 5 Dampak kritis.
- Petunjuk Umum: tiap tugas **wajib dinilai pada KETIGA dimensi** agar terhitung lengkap;
  catatan opsional; **peringatan** — saat "Simpan" draft, task yang belum lengkap 3 dimensi
  **tidak ikut tersimpan** (`opm-form.tsx:125-134`); "Kirim Jawaban" aktif bila semua tugas
  lengkap.
- Cara Menjawab: untuk tiap kartu tugas pilih satu nilai 1–5 pada Importance/Frequency/
  Criticality, isi catatan bila perlu, ulangi hingga semua lengkap.
- **1 contoh non-interaktif**: satu kartu tugas dgn I=5, F=4, C=4 (ilustrasi).

**3c. `time-study/isi/[penugasan_id]/petunjuk-ts.tsx`** — title *"Petunjuk Pengisian Log Harian
Time Study"*.
- Pengantar: mencatat distribusi waktu kerja per hari untuk mengukur beban kerja; isi satu log
  tiap hari kerja selama penugasan aktif (jangan menumpuk di akhir).
- Petunjuk Umum: isi waktu masuk & keluar; bagi durasi kerja ke **enam kategori** (jam+menit);
  pilih Kategori Hari; log bisa diedit selama penugasan aktif.
- **Enam Kategori Aktivitas** (label persis `ts-log-form.tsx:13-20`): Pekerjaan Inti, Asesmen
  Karakter, Pengembangan Diri, Pekerjaan Strategis, Administrasi, Istirahat Terstruktur —
  "kelompokkan aktivitas Anda ke kategori yang paling sesuai; isi sejujurnya". (Jangan
  meng-invent definisi rinci tiap kategori.)
- **Kategori Hari** (`:211-214`): Hijau (Hari Biasa), Kuning (Hari Sibuk), Merah (Hari Puncak).
- Cara: pilih tanggal → isi masuk/keluar → isi jam+menit tiap kategori → pilih Kategori Hari →
  "Simpan Log". Ulangi tiap hari.

**3d. `task-inventory/tahap1/[responden_id]/petunjuk-tahap1.tsx`** — title *"Petunjuk — Tahap 1:
Seleksi Relevansi"*.
- Pengantar: pilih tugas yang **relevan** dengan jabatan Anda dari katalog, **bertingkat 3
  level**: Tugas Pokok → Detil Tugas → Uraian Tugas (`seleksi-form.tsx:30-38`).
- Petunjuk Umum: centang yang relevan tiap level; hanya turunan dari yang dipilih yang muncul di
  level berikutnya; minimal satu tiap level; bisa "Simpan"; **"Kirim Seleksi" mengunci** (tak
  bisa diubah — hubungi admin bila keliru). Jujur — pilih hanya yang benar-benar bagian dari
  pekerjaan Anda.
- Cara Menjawab (langkah bernomor sesuai wizard): 1) Tugas Pokok → "Lanjut ke Detil Tugas";
  2) Detil Tugas → "Lanjut ke Uraian Tugas"; 3) Uraian Tugas → "Simpan"/"Kirim Seleksi".

**3e. `task-inventory/tahap2/[sesi_id]/petunjuk-tahap2.tsx`** — title *"Petunjuk — Tahap 2:
Review Koordinator"*.
- Pengantar: sebagai koordinator panel, Anda memutuskan **task partial** (tidak dipilih bulat/
  unanimous oleh anggota di Tahap 1); task unanimous otomatis lolos tanpa review.
- Petunjuk Umum: tiap baris = task + rasio anggota yang menilainya relevan (`n_relevan/n_total`,
  `review-form.tsx:148-150`); tetapkan **Ya** (masuk) / **Tidak** (tolak); ada "Setujui Semua"/
  "Tolak Semua"; task tanpa keputusan tidak disertakan; keputusan digabung dengan task unanimous
  saat masuk Tahap 3.
- Catatan: bagi **anggota panel non-koordinator** halaman ini hanya-baca.

**3f. `task-inventory/tahap3/[responden_id]/petunjuk-tahap3.tsx`** — title *"Petunjuk — Tahap 3:
Detailing Tugas (CalHR)"*.
- Pengantar: rinci beban kerja (CalHR) untuk tugas yang **benar-benar Anda kerjakan** dari
  daftar final.
- Petunjuk Umum: centang tugas yang Anda kerjakan; sebagian tugas punya **isian standar** yang
  otomatis terpakai saat dicentang (`detail-form.tsx:256-262`) — bila sesuai biarkan ("Setuju
  dengan isian standar"); bila tidak, hapus centang lalu ubah; minimal satu tugas; "Simpan";
  **"Kirim Detail" mengunci**.
- Arti kolom CalHR (dari `@/components/calhr` + `detail-form.tsx:319-423`): Sumber Bukti
  (Formal/Aktual/Keduanya), Kondisi (Baseline/Peak/Both), Frekuensi (Harian/Mingguan/
  Semesteran/Insidental), Durasi/kali (menit), Jam/minggu, Jam peak (4 minggu), VA Type
  (VA-Core/VA-Enable/NVA-Residual/Context-Dependent/Needs Validation). Catatan: "(petunjuk
  standar: …)" di samping Durasi hanya acuan — tetap isi angka sendiri.

### Langkah 4 — Sisipkan ke tiap `page.tsx` (blok header)

Nilai `defaultOpen`:

| Alat ukur | page.tsx | `defaultOpen` |
|---|---|---|
| WCP | `wcp/isi/[responden_id]/page.tsx` (header `:77-80`) | `!responden.sudah_submit` |
| OPM | `opm/isi/[responden_id]/page.tsx` (header `:63-66`) | `!responden.sudah_submit` |
| TS | `time-study/isi/[penugasan_id]/page.tsx` (header `:70-83`) | `penugasan.aktif && logs.length === 0` |
| TI Tahap 1 | `task-inventory/tahap1/[responden_id]/page.tsx` (header `:52-57`) | `!responden.tahap1_submit && sesi.status === "TAHAP1"` |
| TI Tahap 2 | `task-inventory/tahap2/[sesi_id]/page.tsx` (header `:107-113`) | `canEdit && sesi.status === "TAHAP2"` |
| TI Tahap 3 | `task-inventory/tahap3/[responden_id]/page.tsx` (header `:52-58`) | `!responden.tahap3_submit && sesi.status === "TAHAP3"` |

- WCP/OPM/TI-1/TI-2/TI-3: ubah blok header `<div>…<h1/><p/>…</div>` menjadi
  `<div className="flex items-start justify-between gap-4">` dengan blok judul di kiri &
  `<PetunjukX defaultOpen={…} />` di kanan (pola DCS `page.tsx` header).
- **TS**: header sudah `flex … justify-between` dengan tombol "+ Tambah Log" — sisipkan
  `<PetunjukTs defaultOpen={…} />` berdampingan (mis. sebelum tombol Tambah Log).
- Import komponen; **tidak ada perubahan alur fetch/guard**. `canEdit` TI-2 sudah dihitung di
  `page.tsx:84`.

**Catatan TS:** Time Study diisi berulang (log harian) & **tak punya "submit"**. Padanan
terdekat DCS `!sudah_submit` = "penugasan aktif **dan** belum ada log" → auto-muncul saat mulai,
tak menghalangi tiap menambah log. Tombol pemicu tetap selalu terlihat.
**Catatan TI-2:** anggota non-koordinator (`readOnly`) → tidak auto-muncul, tombol tetap ada.

### Langkah 5 — Test (Vitest + Testing Library)

- **Baru `src/test/petunjuk-modal.test.tsx`** (shell): `defaultOpen` false→dialog tak ada,
  true→ada; klik trigger→muncul; klik X / CTA / backdrop / Escape→tertutup; `children`
  ter-render; `title` tampil.
- **`src/test/petunjuk-dcs.test.tsx` tetap ada & hijau tanpa diubah** (bukti refactor tak
  mengubah perilaku). Bila ada pergeseran kecil tak terhindar, sesuaikan seperlunya.
- **Satu test ringan per komponen konten baru** (`petunjuk-wcp/opm/ts/tahap1/tahap2/tahap3
  .test.tsx`): `defaultOpen={true}` → dialog ada + frasa kunci: WCP `/Workplace Climate
  Profile/`, OPM `/Criticality/`, TS `/Kategori Hari/`, TI-1 `/Uraian Tugas/`, TI-2
  `/unanimous|partial/i`, TI-3 `/CalHR/`.

Perintah: `make test` (lint + typecheck + unit, di Docker) — harus hijau.

### Langkah 6 — Dokumentasi pengguna

Perbarui `docs-usage/` (skill `dokumentasi-penggunaan`) untuk tiap halaman pengisian (WCP, OPM,
Time Study, TI Tahap 1/2/3): sebutkan pop-up petunjuk yang muncul otomatis + tombol "Petunjuk
Pengisian".

## Kriteria penerimaan

- [ ] Buka fill page tiap alat ukur (kondisi masih bisa diisi) → pop-up petunjuk **auto-muncul**
      sesuai `defaultOpen`.
- [ ] Tutup (X / CTA / backdrop / Escape) → tertutup, form bisa dipakai.
- [ ] Tombol "Petunjuk Pengisian" selalu terlihat; mengkliknya memunculkan pop-up lagi.
- [ ] Kondisi sudah-submit (WCP/OPM/TI-1/TI-3) / read-only anggota (TI-2) / TS sudah punya log →
      pop-up **tidak** auto-muncul, tombol tetap ada.
- [ ] TI mencakup **Tahap 1, 2, dan 3**.
- [ ] Konten tiap alat ukur akurat (skala/dimensi/kategori sesuai form-nya).
- [ ] Rapi di light & dark, mobile & desktop; konten panjang di-scroll dalam panel
      (`max-h-[85vh] overflow-y-auto`); body tak melebar horizontal.
- [ ] `petunjuk-dcs.tsx` perilaku & teks tak berubah (hanya di-refactor ke shell bersama).
- [ ] Form tiap alat ukur (`*-form.tsx`) **tidak** diubah.

## Skenario uji

Lihat Langkah 5. Minimal: `petunjuk-modal.test.tsx` (shell) + `petunjuk-dcs.test.tsx` lama
tetap hijau + satu test per komponen konten baru. `make test` hijau; `npm run build` sukses.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-web-app` **dan** `npm run build` sukses.
- [ ] Ketujuh alat ukur punya petunjuk (DCS refactor + WCP + OPM + TS + TI 1/2/3).
- [ ] `docs-usage/` diperbarui.
- [ ] `CHANGELOG.md` (web-app) diperbarui.
- [ ] `CLAUDE.md` (web-app) — tambah entri "Revisi Desain".
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`.

## Risiko & catatan

- **Refactor DCS berisiko regresi** — mitigasi: `PetunjukModal` mempertahankan label & struktur
  DOM persis, sehingga `petunjuk-dcs.test.tsx` lolos tanpa diubah (itu jaring pengamannya).
- **Tanpa portal**: modal `fixed` bergantung pada tak adanya ancestor ber-`transform`/
  `overflow:hidden` yang meng-clip — sama seperti DCS/`app-shell.tsx`, aman.
- **Nama & konten dimensi diambil dari kode aktual**, bukan diinvent: WCP = "Workplace Climate
  Profile" (`wcp/page.tsx:83`); jangan mengarang ekspansi kode dimensi (SC/TM/…), nama dimensi
  datang dinamis dari backend. Kategori TS & kolom CalHR pakai label persis dari form.
- **Bukan jalur data** — komponen tak memanggil backend; aturan `?? []` & `notify*` tak berlaku.
- **Lingkup sengaja hanya petunjuk** — tak menyentuh logika form, endpoint, atau `schema.ts`.
