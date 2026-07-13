# Backlog 009 — Web app: perbaikan label & teks UI Task Inventory (sisa migrasi alur 2 → 3 tahap)

> **Repo:** `anjab-abk-web-app`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`, `dokumentasi-penggunaan-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Alur Task Inventory berubah dari 2 tahap menjadi 3 tahap (lihat entri `[2026-06-21]` di `CLAUDE.md`
web app), tapi beberapa bagian UI masih menyisakan asumsi lama. Simulasi end-to-end TI di deployment
YPII (2026-07-13) menemukan empat cacat yang semuanya **menyesatkan pengguna**, bukan sekadar kosmetik:

1. Sesi berstatus **TAHAP3 menampilkan kode mentah `TAHAP3`** di halaman daftar — statusnya tidak ada
   di map label.
2. Status **TAHAP2 dilabeli "Tahap 2 — Detailing"** di halaman daftar, padahal Tahap 2 = Review
   Koordinator dan Tahap 3 = Detailing. Admin membaca label yang salah persis pada tahap yang paling
   mudah dilewati.
3. Subjudul & kartu dashboard masih menulis **"alur 2 tahap"**.
4. Banner Tahap 3 menyuruh pengguna **"biarkan tercentang"**, padahal saat halaman dibuka **tidak ada
   satu pun task yang tercentang**.

Ditambah satu cacat interaksi yang ditemukan di komponen yang sama: dialog konfirmasi transisi
memakai `paksa = !confirm(...)` — menekan **Cancel** justru **memaksa** transisi berjalan.

## Keputusan yang sudah dikunci

1. **Sumber kebenaran label status = alur 3 tahap.** `TAHAP2` = "Tahap 2 — Review Koordinator",
   `TAHAP3` = "Tahap 3 — Detailing". Ini konsisten dengan label di halaman detail
   (`transisi-sesi.tsx`) dan dengan `docs-usage/ik/task-inventory.md`.
2. **Map status harus lengkap** — keenam status (`DRAFT`, `TAHAP1`, `TAHAP2`, `TAHAP3`, `CLOSED`,
   `ANALYZED`) punya label. Fallback ke kode mentah dipertahankan sebagai jaring pengaman, tapi tidak
   boleh lagi tercapai untuk status yang valid.
3. **Semantik dialog konfirmasi dibalik menjadi intuitif:** OK = lanjutkan, Cancel = batal (tidak
   terjadi apa-apa). Opsi "paksa lanjut walau belum semua submit" **tidak boleh** dipetakan ke tombol
   Cancel. Bila mode paksa tetap dibutuhkan, jadikan ia kontrol tersendiri yang eksplisit (mis. checkbox
   "Lanjutkan walau belum semua partisipan submit" di dekat tombol) — jangan sembunyikan di balik Cancel.
4. **Banner Tahap 3 diselaraskan dengan perilaku aktual**, bukan sebaliknya. **Jangan** mengubah default
   checkbox menjadi tercentang — mencentang otomatis akan membuat partisipan tanpa sadar mengklaim
   mengerjakan task yang tidak ia kerjakan, dan itu merusak data ABK. Yang diperbaiki adalah teksnya.
5. Perubahan ini **murni UI/teks**. Tidak ada perubahan kontrak API, `schema.ts`, atau alur data.

## Kondisi sekarang (verified)

| Fakta | Lokasi | ✓ |
|---|---|---|
| Map label status daftar TI — **`TAHAP3` tidak ada**, `TAHAP2` dilabeli "Detailing" | `src/app/(auth)/task-inventory/page.tsx:10-16` | ✓ |
| Fallback ke kode mentah bila status tak dikenal | `src/app/(auth)/task-inventory/page.tsx:84-87` | ✓ |
| Status valid per tipe generated: `"DRAFT" \| "TAHAP1" \| "TAHAP2" \| "TAHAP3" \| "CLOSED" \| "ANALYZED"` | `src/lib/api/schema.ts:4967` | ✓ |
| Halaman Kuesioner **sudah benar** — punya `TAHAP3: "Tahap 3"` (jadikan acuan) | `src/app/(auth)/kuesioner/page.tsx:24` | ✓ |
| Teks usang "2 tahap" — kartu dashboard | `src/app/(auth)/dashboard/page.tsx:33` | ✓ |
| Teks usang "2 tahap" — subtitle halaman TI | `src/app/(auth)/task-inventory/page.tsx:40` | ✓ |
| Banner "Sebagian tugas sudah terisi dengan nilai standar… biarkan tercentang" | `src/app/(auth)/task-inventory/tahap3/[responden_id]/detail-form.tsx:235-240` | ✓ |
| Kondisi banner: `adaTaskBerstandar = tasks.some(punyaStandar)` | `detail-form.tsx:134`, `punyaStandar` di `:47-60` | ✓ |
| Task belum diisi → `rowDariStandar(t)` menyetel **`checked: false`** meski `setuju_standar: true` | `detail-form.tsx:70-71` (dipakai di `:93-114`) | ✓ |
| Payload submit melewati task yang `!r.checked` | `detail-form.tsx:141` | ✓ |
| Komponen transisi status (semua tombol tahap) | `src/app/(auth)/task-inventory/[sesi_id]/transisi-sesi.tsx` | ✓ |
| **Cancel = paksa**: `const paksa = !confirm(...)` | `transisi-sesi.tsx:43` (Tahap 2), `:66` (Tahap 3) | ✓ |
| Semua transisi memanggil `router.refresh()` setelah sukses; error 4xx di-render `role="alert"` | `transisi-sesi.tsx:34`, `:57`, `:80`; render error `:113-117` | ✓ |
| `toApiError` memetakan envelope `{error,message,details}`; body non-envelope → pesan generik | `src/lib/api/errors.ts:37-47` | ✓ |

Agen pelaksana **wajib membaca ulang** file-file di atas sebelum mengedit — nomor baris bisa bergeser.

## Langkah eksekusi

### Langkah 1 — Lengkapi & betulkan map label status

`src/app/(auth)/task-inventory/page.tsx:10-16`:

```ts
const STATUS_LABEL: Record<string, { label: string; cls: string }> = {
  DRAFT: { label: "Draft", cls: "bg-gray-100 text-gray-600" },
  TAHAP1: { label: "Tahap 1 — Seleksi", cls: "bg-blue-100 text-blue-700" },
  TAHAP2: { label: "Tahap 2 — Review Koordinator", cls: "bg-indigo-100 text-indigo-700" },
  TAHAP3: { label: "Tahap 3 — Detailing", cls: "bg-purple-100 text-purple-700" },
  CLOSED: { label: "Tertutup", cls: "bg-yellow-100 text-yellow-700" },
  ANALYZED: { label: "Teranalisis", cls: "bg-green-100 text-green-700" },
};
```

Pertahankan fallback di `:84-87`. Pilih kelas warna TAHAP3 yang belum dipakai status lain (contoh di atas
`purple`), konsisten dengan palet yang ada.

### Langkah 2 — Buang teks "2 tahap"

- `src/app/(auth)/dashboard/page.tsx:33` → mis. `"Inventori tugas 3 tahap: seleksi relevansi, review koordinator, lalu detailing beban kerja."`
- `src/app/(auth)/task-inventory/page.tsx:40` → mis. `"Inventori tugas (CalHR 5-komponen) — alur 3 tahap: seleksi, review koordinator, detailing."`

Jangan menyentuh `CLAUDE.md:179` dan `CHANGELOG.md:823` — keduanya catatan historis.

### Langkah 3 — Selaraskan banner Tahap 3 dengan perilaku aktual

`detail-form.tsx:235-240`. Ganti teks agar menggambarkan yang benar-benar terjadi: task **tidak**
tercentang secara default; pengguna mencentang task yang ia kerjakan, dan begitu dicentang, rinciannya
sudah terisi nilai standar yang bisa langsung dipakai atau diubah.

Usulan teks:

> Centang tugas yang Anda kerjakan. Sebagian tugas sudah punya isian standar yang otomatis terpakai saat
> dicentang — bila sudah sesuai, biarkan apa adanya; bila tidak, hapus centang "Setuju dengan isian
> standar" lalu ubah isiannya.

**Jangan** mengubah `rowDariStandar` (`:70-71`) agar `checked: true` — lihat keputusan #4.

### Langkah 4 — Perbaiki semantik dialog konfirmasi transisi

`transisi-sesi.tsx:42-64` (Tahap 2) dan `:65-88` (Tahap 3). Hapus pola `const paksa = !confirm(...)`.

Bentuk yang diinginkan:
- `confirm(...)` hanya menjawab "lanjut atau batal". Cancel → `return` tanpa efek samping.
- Mode paksa jadi state komponen sendiri (mis. `const [paksa, setPaksa] = useState(false)`), dikendalikan
  checkbox eksplisit yang hanya muncul saat masih ada partisipan yang belum submit. Teks konfirmasi
  menyesuaikan: sebutkan berapa yang belum submit bila `paksa` aktif.

Rapikan juga duplikasi: Tahap 2 & Tahap 3 meng-copy blok try/catch yang sama dengan helper `post()`
(`:19-40`). Satukan ke satu helper yang menerima query opsional `paksa`.

### Langkah 5 — Dokumentasi penggunaan

`docs-usage/ik/task-inventory.md` bagian C ("Transisi Tahap") saat ini mendokumentasikan perilaku lama:
"Cancel untuk memaksa lanjut". Setelah Langkah 4, perbarui blok `!!! warning "Dialog konfirmasi"` agar
sesuai kontrol baru. Perbarui juga bagian F bila teks banner Tahap 3 dikutip di sana.

## Kriteria penerimaan

- [ ] Sesi berstatus TAHAP3 menampilkan "Tahap 3 — Detailing" di halaman daftar (bukan `TAHAP3`).
- [ ] Sesi berstatus TAHAP2 menampilkan "Tahap 2 — Review Koordinator" (bukan "Detailing").
- [ ] Keenam status punya label; tidak ada status valid yang jatuh ke fallback kode mentah.
- [ ] Tidak ada lagi string "2 tahap" di `src/`.
- [ ] Menekan **Cancel** pada dialog transisi Tahap 2/Tahap 3 **tidak mengubah status sesi**.
- [ ] Mode paksa hanya aktif lewat kontrol eksplisit, dan hanya tampil saat memang ada yang belum submit.
- [ ] Banner Tahap 3 tidak lagi menyuruh "biarkan tercentang" saat tidak ada yang tercentang.
- [ ] Default checkbox Tahap 3 tetap **tidak tercentang**.

## Skenario uji

Vitest + Testing Library (`src/test/`). Tambahkan:

1. **Map label status** — render halaman daftar (atau ekspor `STATUS_LABEL` agar testable) dan pastikan
   keenam status memetakan ke label yang benar; khususnya `TAHAP2` → "Review Koordinator" dan
   `TAHAP3` → "Detailing".
2. **Transisi — Cancel membatalkan.** Mock `window.confirm` → `false`; klik "Mulai Tahap 2"; pastikan
   **tidak ada** request POST yang terkirim (mock klien API) dan status tidak berubah.
3. **Transisi — OK melanjutkan.** `confirm` → `true`; pastikan POST terkirim **tanpa** `paksa=true` selama
   checkbox paksa tidak dicentang.
4. **Tahap 3 — default tidak tercentang.** Render `detail-form` dengan task berstandar dan tanpa detail
   tersimpan; pastikan seluruh checkbox "dikerjakan" `unchecked`, dan submit tanpa mencentang apa pun
   tidak mengirim task apa pun.

```bash
cd anjab-abk-web-app && make test   # lint + typecheck + unit
npm run build                        # wajib sukses sebelum lapor selesai
```

Verifikasi manual (Playwright/manual) di alur nyata: buat sesi → Tahap 1 → Tahap 2 → Tahap 3, dan
pastikan label di halaman **daftar** cocok dengan label di halaman **detail** pada tiap tahap.

## Definition of done

- [ ] `make test` hijau **dan** `npm run build` sukses
- [ ] `CHANGELOG.md` diperbarui
- [ ] `CLAUDE.md` repo diperbarui (tambahkan entri Revisi Desain bila kontrol "paksa" berubah bentuk)
- [ ] `docs-usage/ik/task-inventory.md` diperbarui (Langkah 5)
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Item 004** (terminologi "Sesi" → "Analisis Jabatan") menyentuh berkas yang sama
  (`task-inventory/page.tsx`, kartu dashboard). Bila 004 dikerjakan lebih dulu, teks usulan di sini harus
  diselaraskan dengan istilah "Analisis Jabatan". Tidak ada konflik struktural — hanya string.
- Mengubah semantik dialog transisi mengubah kebiasaan admin yang sudah terlanjur hafal "Cancel = paksa".
  Perubahan ini disengaja (pola lama berbahaya pada aksi yang tidak bisa dibatalkan), tapi **sebutkan di
  CHANGELOG** dengan jelas.
- Selama simulasi, transisi "Mulai Tahap 1" tampak tidak me-refresh tampilan setelah POST sukses (status
  tetap "Draft" sampai halaman dibuka ulang lewat navigasi), sehingga klik kedua menghasilkan 422
  ("Transisi dari 'TAHAP1' ke 'TAHAP1' tidak valid"). Pembacaan kode menunjukkan `router.refresh()` **sudah**
  dipanggil di semua jalur transisi (`transisi-sesi.tsx:34`) dan error **sudah** dirender (`:113-117`), jadi
  akar masalahnya belum terkonfirmasi — kemungkinan caching RSC (tidak ada `revalidatePath`/server action).
  **Reproduksi dulu sebelum menambal**; jangan menebak. Bila terkonfirmasi, tangani di item ini sebagai
  langkah tambahan (mis. jadikan transisi server action + `revalidatePath`), atau pecah jadi item sendiri.
