# Backlog 046 — Web app: pop-up petunjuk pengisian alat ukur DCS

> **Repo:** `anjab-abk-web-app`
> **Status:** Selesai 2026-07-15
> **Blocked by:** —
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`, `dokumentasi-penggunaan-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Halaman pengisian kuesioner **DCS** (Demand–Control–Support) di
`/dcs/isi/[responden_id]` langsung menampilkan 42 pernyataan Likert 1–5 **tanpa
penjelasan apa pun** — apa itu DCS, arti tiap angka skala, dan cara menjawab.
Partisipan (mayoritas guru/staf yayasan, bukan psikolog) tidak punya panduan, sehingga
kualitas & konsistensi jawaban rentan.

Tambahkan **penjelasan pengisian bergaya petunjuk instrumen psikologi** — detail, disertai
contoh (non-interaktif) — dalam **pop-up (modal)** yang:

1. **Muncul otomatis** setiap kali partisipan masuk halaman pengisian DCS (selama belum
   submit) — konsekuensi dari menekan "Isi Sekarang".
2. **Bisa dibuka lagi** kapan saja lewat tombol **"Petunjuk Pengisian"** saat mengisi.

Hasil akhir: partisipan membaca instruksi jelas sebelum mengisi → mengurangi kebingungan
dan meningkatkan validitas jawaban.

## Keputusan yang sudah dikunci

- **Kemunculan otomatis**: tiap kali halaman isi dibuka saat `!sudah_submit`. **Tidak**
  pakai `localStorage`, **tidak** ada "jangan tampilkan lagi". (Dikonfirmasi user 2026-07-15.)
- **Cakupan: DCS saja.** WCP (struktur mirip) **sengaja tidak disentuh** sekarang;
  komponen dibuat rapi agar mudah ditiru untuk WCP kelak.
- **Contoh non-interaktif**: contoh adalah ilustrasi statis (pernyataan + pil jawaban
  tersorot), **bukan** radio yang bisa diklik.
- **Modal di-hand-roll** meniru pola overlay yang sudah ada (`app-shell.tsx`) — **tidak**
  menambah dependency (`@radix-ui/react-dialog` tidak dipasang; tidak ada shadcn di repo).
- `dcs-form.tsx` **tidak disentuh**. Perubahan hanya di `page.tsx` + 1 komponen baru.

## Kondisi sekarang (verified)

> Agen pelaksana WAJIB membaca ulang file-nya sebelum mengedit — baris bisa bergeser.

| Fakta | Lokasi | ✓ |
|---|---|---|
| Halaman isi (Server Component) punya `responden.sudah_submit` + header "Kuesioner DCS" | `src/app/(auth)/dcs/isi/[responden_id]/page.tsx:64-67`, `:69`, `:85` | ✓ |
| Form pengisian (Client Component); **tidak diubah** | `.../dcs/isi/[responden_id]/dcs-form.tsx` | ✓ |
| Label skala 1–5 (`Sangat Tidak Setuju … Sangat Setuju`) — sumber teks konten | `dcs-form.tsx:10-16` | ✓ |
| Gaya pil jawaban (di-mock statis untuk contoh) — sorot `border-blue-500 bg-blue-50 text-blue-700` | `dcs-form.tsx:182-206` | ✓ |
| Subskala DCS: 3 buah urutan tetap `DEMAND → CONTROL → SUPPORT`; 14 item/subskala = 42 pernyataan; nama mis. "Demand (Tuntutan Kerja)" | `page.tsx:11` | ✓ |
| **Tidak ada** komponen modal/dialog; satu-satunya pola overlay = drawer mobile `fixed inset-0 z-30 bg-black/30` di-toggle `useState`, tanpa portal | `src/components/shell/app-shell.tsx:61-68` | ✓ |
| Styling Tailwind v4 + helper `cn()`; ikon `lucide-react` (`HelpCircle`, `X`); dark mode varian `dark:` | `src/lib/utils.ts`, `package.json` | ✓ |
| Tidak ada panggilan API di komponen ini (murni presentasi) → aturan jalur-baca `?? []` & notify tidak relevan | — | ✓ |

## Langkah eksekusi

### Langkah 1 — Komponen baru `petunjuk-dcs.tsx`

Buat `src/app/(auth)/dcs/isi/[responden_id]/petunjuk-dcs.tsx` (`"use client"`).
Props: `{ defaultOpen: boolean }`. Swasembada: tombol pemicu + modal + isi konten.

Perilaku:
- `const [open, setOpen] = useState(defaultOpen)` → auto-buka sekali per mount saat
  `defaultOpen` true (tiap kunjungan halaman = mount baru = auto-buka).
- **Tombol pemicu selalu terlihat**: `<button>` bergaya garis, ikon `HelpCircle` +
  teks "Petunjuk Pengisian" (`onClick={() => setOpen(true)}`). Pakai `cn()`.
- Saat `open`, render **modal hand-rolled** (meniru `app-shell.tsx`, tanpa portal):
  - Backdrop `fixed inset-0 z-50 bg-black/50` — klik menutup (`onClick={() => setOpen(false)}`).
  - Panel terpusat `role="dialog" aria-modal="true" aria-labelledby="petunjuk-dcs-judul"`,
    `w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-lg bg-white p-6 shadow-xl
    dark:bg-gray-900 dark:border dark:border-gray-700`; `onClick` panel `stopPropagation`
    supaya klik di dalam tidak menutup.
  - Tombol tutup `X` (ikon `X`, `aria-label="Tutup"`) pojok kanan atas.
  - **Escape menutup**: `useEffect` menambah listener `keydown` saat `open`, cleanup saat
    tutup/unmount.
  - Tombol utama di bawah konten: **"Saya Mengerti, Mulai Mengisi"** → `setOpen(false)`.

Konten petunjuk (gaya instrumen psikologi, **statis**, Bahasa Indonesia). Pakai kartu-aksen
yang sudah lazim di repo (`rounded-md bg-blue-50 … dark:…`):

1. **Judul** (`id="petunjuk-dcs-judul"`): "Petunjuk Pengisian Kuesioner DCS".
2. **Pengantar**: DCS memotret pengalaman kerja Anda pada tiga aspek — **Tuntutan Kerja
   (Demand)**, **Kendali Kerja (Control)**, **Dukungan Sosial (Support)**. Bukan tes; tidak
   ada jawaban benar atau salah.
3. **Petunjuk Umum** (daftar butir):
   - Baca tiap pernyataan dengan saksama.
   - Jawab berdasarkan **apa yang benar-benar Anda alami dan rasakan** dalam pekerjaan
     selama ini — bukan yang ideal/seharusnya.
   - Tidak ada jawaban benar/salah; semua sama baiknya selama menggambarkan Anda dengan jujur.
   - Jawab **spontan** — kesan pertama biasanya paling menggambarkan keadaan Anda; jangan
     terlalu lama pada satu pernyataan.
   - Isi **semua 42 pernyataan**; tombol "Kirim Jawaban" baru aktif bila seluruhnya
     terjawab. Bisa menekan **"Simpan"** untuk melanjutkan nanti.
   - Jawaban **rahasia**, dipakai untuk analisis jabatan/beban kerja — bukan menilai kinerja
     individu.
4. **Pilihan Jawaban (Skala 1–5)** — jelaskan tiap angka (label sumber `dcs-form.tsx:10-16`):
   - 1 = Sangat Tidak Setuju — sama sekali tidak menggambarkan keadaan Anda
   - 2 = Tidak Setuju — kurang menggambarkan
   - 3 = Ragu-ragu — di antara setuju dan tidak
   - 4 = Setuju — cukup menggambarkan
   - 5 = Sangat Setuju — sangat menggambarkan
5. **Cara Menjawab** (langkah bernomor): baca → renungkan seberapa sesuai → klik satu dari
   1–5 → lanjut hingga selesai.
6. **Contoh Pengisian (non-interaktif)** — 2 contoh sebagai ilustrasi statis (bukan radio),
   meniru gaya pil jawaban `dcs-form.tsx:182-206` dengan satu pil tersorot:
   - Contoh A — *"Saya harus menyelesaikan banyak pekerjaan dalam waktu yang terbatas."*
     Bila sering terjadi & sangat sesuai → pilih **5 (Sangat Setuju)** (pil "5" tersorot).
   - Contoh B — *"Saya memiliki keleluasaan untuk memutuskan cara menyelesaikan pekerjaan
     saya."* Bila kurang sesuai → pilih **2 (Tidak Setuju)** (pil "2" tersorot).
   - Catatan tegas: contoh ini **hanya ilustrasi**; jawablah tiap pernyataan sesuai keadaan
     Anda sendiri.

### Langkah 2 — Sisipkan ke `page.tsx`

Di `src/app/(auth)/dcs/isi/[responden_id]/page.tsx`:
- `import { PetunjukDcs } from "./petunjuk-dcs";`
- Render `<PetunjukDcs defaultOpen={!responden.sudah_submit} />` di blok header (dekat judul
  "Kuesioner DCS", sekitar `page.tsx:64-67`) supaya tombol "Petunjuk Pengisian" selalu
  terlihat & pop-up auto-buka saat halaman dibuka untuk mengisi.
- Tidak ada perubahan lain; alur fetch/guard tetap.

### Langkah 3 — Test unit

Buat `src/test/petunjuk-dcs.test.tsx` (Vitest + Testing Library, ikuti pola
`src/test/*.test.tsx`).

### Langkah 4 — Dokumentasi pengguna

Perbarui halaman pengisian DCS di `docs-usage/` (lewat skill `dokumentasi-penggunaan`):
sebutkan pop-up petunjuk yang muncul otomatis + tombol "Petunjuk Pengisian".

## Kriteria penerimaan

- [ ] Membuka `/dcs/isi/{id}` (belum submit) → pop-up petunjuk **muncul otomatis**.
- [ ] Menutup pop-up (X / "Saya Mengerti, Mulai Mengisi" / klik backdrop / Escape) → pop-up
      tertutup, form bisa diisi.
- [ ] Tombol "Petunjuk Pengisian" selalu terlihat; mengkliknya **memunculkan pop-up lagi**.
- [ ] Halaman `sudah_submit` (lihat jawaban) → pop-up **tidak** auto-buka; tombol tetap ada.
- [ ] Konten memuat: pengantar 3 aspek DCS, petunjuk umum ("tidak ada jawaban benar/salah"),
      makna skala 1–5, langkah menjawab, dan **2 contoh non-interaktif**.
- [ ] Tampil rapi di light & dark, mobile & desktop; panjang konten bisa di-scroll dalam
      panel (`max-h-[85vh] overflow-y-auto`), body tidak melebar horizontal.
- [ ] `dcs-form.tsx` tidak berubah.

## Skenario uji

`src/test/petunjuk-dcs.test.tsx` minimal:

- `defaultOpen={false}` → modal tidak ter-render; `defaultOpen={true}` → modal ter-render
  saat mount.
- Klik tombol "Petunjuk Pengisian" → modal muncul.
- Klik "X" → modal tertutup; klik "Saya Mengerti, Mulai Mengisi" → modal tertutup; klik
  backdrop → modal tertutup.
- Konten memuat teks kunci: mis. `/tidak ada jawaban benar atau salah/i`,
  `/Sangat Tidak Setuju/`, `/Contoh/`.

Perintah: `make test` (lint + typecheck + unit, di Docker) — harus hijau.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-web-app` **dan** `npm run build` sukses.
- [ ] `docs-usage/` diperbarui (halaman pengisian DCS).
- [ ] `CHANGELOG.md` (web-app) diperbarui.
- [ ] `CLAUDE.md` (web-app) — tambah entri "Revisi Desain" bila dianggap perubahan alur UI
      (fitur layar baru).
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`.

## Risiko & catatan

- **Tanpa portal**: modal `fixed` bergantung pada tidak adanya ancestor ber-`transform`/
  `overflow:hidden` yang meng-clip. Pola identik sudah dipakai `app-shell.tsx` di struktur
  `<main>` yang sama → aman. Bila kelak ada wrapper ber-transform, pertimbangkan `createPortal`.
- **Ruang lingkup**: hanya DCS. Jangan diam-diam melebar ke WCP/OPM/TI — bila diinginkan,
  buat item backlog terpisah yang meniru komponen ini.
- **Bukan jalur data**: komponen ini tidak memanggil backend, jadi invariant jalur-baca
  (`?? []`) dan aturan `notify*` tidak berlaku di sini.
