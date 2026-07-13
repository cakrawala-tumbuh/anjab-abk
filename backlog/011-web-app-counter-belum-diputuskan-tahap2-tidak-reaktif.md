# Backlog 011 — Counter "Belum diputuskan" di header Tahap 2 tidak reaktif

> **Repo:** `anjab-abk-web-app`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Temuan simulasi end-to-end Task Inventory di deployment YPII (`anjab-abk.cantum-ypii.com`,
2026-07-13, panel Kepala Sekolah): di halaman Review Koordinator Tahap 2
(`/task-inventory/tahap2/[sesi_id]`), counter header **"Belum diputuskan: N"** tidak berubah
saat koordinator/admin mengklik **Ya**/**Tidak** per baris task — tetap menampilkan angka awal
sampai `router.refresh()` terpicu (mis. setelah klik **Simpan Keputusan**). Ini membingungkan
karena counter LAIN di halaman yang sama (action bar dekat tombol Simpan) sudah reaktif dan
langsung menghilang begitu semua task diputuskan, sebelum disimpan — sehingga dua indikator
untuk fakta yang sama menunjukkan angka berbeda pada saat bersamaan.

## Keputusan yang sudah dikunci

- Sumber kebenaran untuk "berapa task belum diputuskan" harus **satu**: state client
  (`keputusan`) yang sudah reaktif di `review-form.tsx`, bukan `review.jumlah_belum_diputuskan`
  hasil fetch server yang statis sejak render awal.
- Header di `page.tsx` (Server Component) **tidak** boleh lagi menampilkan angka
  `jumlah_belum_diputuskan` yang stale. Pindahkan tampilan counter tersebut ke dalam
  `review-form.tsx` (Client Component) yang sudah memegang state `keputusan`, dipakai ulang untuk
  kedua lokasi (header atas dan action bar).
- "Total partial" (jumlah total task partial) boleh tetap tampil dari `page.tsx` karena angka ini
  memang tidak berubah oleh interaksi Ya/Tidak.

## Kondisi sekarang (verified)

- `src/app/(auth)/task-inventory/tahap2/[sesi_id]/page.tsx:120-129` — header, Server Component,
  computed dari `review.jumlah_belum_diputuskan` (hasil `GET /api/v1/task-inventory/sesi/{sesi_id}/tahap2`
  yang di-fetch sekali di `fetchPageData()`, baris 20-50, khususnya `reviewRes` baris 30-32):
  ```tsx
  <div className="flex gap-4 text-sm text-gray-600">
    <span>
      Total partial: <strong>{review.tasks.length}</strong>
    </span>
    {!readOnly && review.jumlah_belum_diputuskan > 0 && (
      <span className="text-amber-600">
        Belum diputuskan: <strong>{review.jumlah_belum_diputuskan}</strong>
      </span>
    )}
  </div>
  ```
- `src/app/(auth)/task-inventory/tahap2/[sesi_id]/review-form.tsx:21-31` — state client reaktif:
  ```tsx
  const [keputusan, setKeputusan] = useState<Keputusan>(() => {
    const init: Keputusan = {};
    for (const t of review.tasks) {
      init[t.task_kode] = t.disetujui ?? null;
    }
    return init;
  });
  ...
  const belumDiputuskan = Object.values(keputusan).filter((v) => v === null).length;
  ```
  Dipakai di action bar atas & bawah, baris 95-97 dan 202-204:
  ```tsx
  {belumDiputuskan > 0 && (
    <span className="text-xs text-amber-600">{belumDiputuskan} belum diputuskan</span>
  )}
  ```
  Tombol Ya/Tidak (baris 156, 166) memanggil `setKeputusan((p) => ({ ...p, [t.task_kode]: true/false }))`
  — inilah yang membuat action bar reaktif, sedangkan header di `page.tsx` tidak pernah tersentuh
  oleh state ini karena berada di komponen server yang berbeda.
- Setelah submit sukses, `review-form.tsx:62` memanggil `router.refresh()` yang barulah membuat
  `page.tsx` re-fetch dan header ikut update — tapi ini baru terjadi setelah **Simpan Keputusan**,
  bukan saat user masih memutuskan per baris.

## Langkah eksekusi

### Langkah 1 — Pindahkan tampilan counter "Belum diputuskan" ke `review-form.tsx`

Di `src/app/(auth)/task-inventory/tahap2/[sesi_id]/review-form.tsx`, render blok
"Belum diputuskan: N" (gaya sama dengan versi lama di `page.tsx`, termasuk kondisi
`!readOnly && belumDiputuskan > 0`) memakai `belumDiputuskan` yang sudah ada sebagai bagian dari
header form ini — letakkan di tempat yang secara visual menggantikan posisi lama (header atas
halaman), bukan hanya di action bar.

### Langkah 2 — Lepas counter statis dari `page.tsx`

Di `src/app/(auth)/task-inventory/tahap2/[sesi_id]/page.tsx:120-129`, hapus span
`Belum diputuskan: {review.jumlah_belum_diputuskan}` — sisakan hanya "Total partial:
{review.tasks.length}" di header server. Pastikan prop yang diteruskan ke `<ReviewForm>` tidak
berubah (komponen ini sudah menerima `review` secara penuh).

### Langkah 3 — Cek mode read-only (anggota panel non-koordinator)

Bagian `!readOnly` di kondisi lama harus tetap dihormati — pastikan `review-form.tsx` juga punya
akses ke flag `readOnly` (atau counter ini memang hanya relevan saat form interaktif ditampilkan,
sehingga di mode read-only elemen ini otomatis tidak muncul karena `ReviewForm` interaktif memang
tidak dirender untuk anggota panel — cek pola render read-only yang sudah ada di halaman ini
sebelum mengasumsikan).

## Kriteria penerimaan

- [ ] Saat koordinator mengklik Ya/Tidak pada task partial, counter "Belum diputuskan: N" di
      bagian atas halaman berubah **seketika** (tanpa reload/refresh), konsisten dengan counter di
      action bar.
- [ ] Begitu semua task sudah diputuskan (tanpa klik Simpan), kedua tampilan counter
      hilang/menampilkan 0 secara bersamaan.
- [ ] Tampilan mode read-only (anggota panel non-koordinator melihat Tahap 2) tidak menampilkan
      tombol Ya/Tidak/Simpan — tidak berubah dari perilaku sekarang.
- [ ] "Total partial" tetap benar dan tidak terpengaruh perubahan ini.

## Skenario uji

- Test komponen `review-form.tsx` (Vitest + Testing Library): render dengan beberapa task partial
  berstatus belum diputuskan, klik Ya pada satu task, assert counter berkurang tanpa perlu
  re-render dari props baru.
- Test bahwa saat semua task diputuskan via klik, elemen counter tidak lagi dirender (query
  `getByText` mengembalikan null / `queryByText`).
- Jalankan via `make test` (lint + unit).

## Definition of done

- [ ] `make test` hijau di `anjab-abk-web-app`
- [ ] `npm run build` sukses
- [ ] `CHANGELOG.md` diperbarui
- [ ] `docs-usage/` diupdate bila teks/perilaku halaman berubah secara kasat mata (biasanya tidak
      perlu untuk perbaikan reaktivitas murni, kecuali ada perubahan copy)
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- Perubahan ini murni UI/state — tidak menyentuh endpoint atau kontrak API, risiko rendah.
- Ditemukan lewat simulasi Playwright manual (bukan e2e otomatis) di panel Kepala Sekolah,
  2026-07-13. Verifikasi e2e/Playwright otomatis untuk halaman ini boleh sengaja dilewati sesuai
  pola item 009/010, kecuali user memintanya.
