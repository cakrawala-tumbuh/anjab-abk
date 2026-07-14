# Backlog 019 — Web app: tampilkan responden yang di-skip pada assign DCS & WCP

> **Repo:** `anjab-abk-web-app`
> **Status:** Menunggu (blocked by 018)
> **Blocked by:** 018
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Setelah item **018** membuat `POST /api/v1/dcs/responden` & `POST /api/v1/wcp/responden` mengembalikan
`BulkAssignResult` (`created[]` + `skipped[]`), web app harus **menampilkan** hasilnya — persis seperti
yang sudah dilakukan panel bulk TI/OPM/Time Study.

Sekarang kedua komponen ini hanya membersihkan selection lalu `router.refresh()`, tanpa konfirmasi apa
pun. Memilih 10 partisipan lalu 7 di-skip terlihat identik dengan sukses penuh.

Ini melengkapi item **017**, yang menegakkan prinsip: setiap penyimpanan data punya notifikasi jujur.

## Keputusan yang sudah dikunci

1. **Tiru persis panel ringkasan yang sudah ada** di
   `src/app/(auth)/opm/[sesi_id]/assign-responden-banyak.tsx` (L91-106) — daftar `created` (jumlah) +
   `<ul>` `skipped` dengan `formatAlasanSkip(s.alasan)`. Jangan mendesain bentuk baru.
2. Reuse helper `formatAlasanSkip()` yang sudah ada — **jangan** duplikasi pemetaan alasan.
3. Selection **tidak** dibersihkan untuk partisipan yang di-skip — hanya yang berhasil dibuat yang
   di-uncheck, supaya user bisa retry tanpa memilih ulang. (Perilaku sekarang: `setSelected(new Set())`
   membersihkan semuanya — ini diperbaiki.)
4. Toast dari item 017 tetap dipanggil berdampingan dengan panel ringkasan.

## Kondisi sekarang (verified)

✓ Dibaca 2026-07-13:

| Berkas : baris | Kondisi |
|---|---|
| `src/app/(auth)/dcs/assign-responden.tsx:51` | POST `/api/v1/dcs/responden`; sukses → `setSelected(new Set())` + `router.refresh()` (L56-57). **Tanpa konfirmasi.** Error → inline `<div role="alert" className="bg-red-50">` (L75-79) |
| `src/app/(auth)/wcp/assign-responden.tsx:51` | Struktur identik, baris sama |
| `src/app/(auth)/opm/[sesi_id]/assign-responden-banyak.tsx:63,91-106` | **Acuan** — panel ringkasan `created` + `skipped` |
| `src/app/(auth)/task-inventory/[sesi_id]/assign-responden-banyak.tsx:64,92-107` | Acuan kedua, pola sama |
| `src/app/(auth)/time-study/tugaskan-banyak/ts-penugasan-bulk-form.tsx:64,99-114` | Acuan ketiga, pola sama |

Setelah 018 dirilis, `src/lib/api/schema.ts` **wajib diregenerasi** (`npm run gen:api`) — tipe response
kedua endpoint berubah dari array menjadi objek, dan TypeScript akan menolak kode lama. Itu justru
jaring pengaman: `npm run build` akan gagal sampai kedua komponen disesuaikan.

## Langkah eksekusi

### Langkah 1 — Regenerasi tipe

```bash
npm run gen:api
```

Pastikan `openapi/openapi.json` sudah yang versi 018. `npm run build` akan error di
`dcs/assign-responden.tsx` & `wcp/assign-responden.tsx` — itu ekspektasinya.

### Langkah 2 — Sesuaikan kedua komponen

Di `dcs/assign-responden.tsx` dan `wcp/assign-responden.tsx`:

1. Tambahkan state `result` (bertipe hasil `BulkAssignResult` dari schema generated).
2. Pada jalur sukses: `setResult(data)`, uncheck **hanya** id yang ada di `data.created`, lalu
   `router.refresh()`.
3. Render panel ringkasan meniru `opm/[sesi_id]/assign-responden-banyak.tsx` L91-106.
4. Panggil `notifySukses(...)` / `notifyGagal(err)` dari `src/lib/notify.ts` (item 017).

### Langkah 3 — Test

## Kriteria penerimaan

- [ ] `npm run build` sukses dengan `schema.ts` hasil regenerasi.
- [ ] Assign dengan sebagian di-skip → panel menampilkan jumlah `created` **dan** daftar `skipped`
      beserta alasan ber-Bahasa Indonesia.
- [ ] Assign yang **0 dibuat, semua di-skip** → user melihat dengan jelas bahwa tidak ada yang
      ditambahkan (tidak terlihat seperti sukses).
- [ ] Checkbox partisipan yang di-skip **tetap tercentang** setelah submit.
- [ ] `formatAlasanSkip` di-reuse, tidak diduplikasi.

## Skenario uji

`src/test/dcs-assign-responden.test.tsx` & `src/test/wcp-assign-responden.test.tsx`:

- Response `{created: [3 item], skipped: []}` → panel memuat "3 responden berhasil ditambahkan",
  tak ada daftar skip.
- Response `{created: [1], skipped: [2 item]}` → panel memuat kedua bagian; alasan ter-render lewat
  `formatAlasanSkip`.
- Response `{created: [], skipped: [2]}` → panel **tidak** menyiratkan sukses.
- Setelah sukses parsial, checkbox id yang di-skip masih tercentang.

Perintah: `make test` + `npm run build`.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-web-app`
- [ ] `npm run build` sukses
- [ ] `CHANGELOG.md` diperbarui
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Jangan mulai sebelum 018 dirilis** — `schema.ts` yang diregenerasi dari `openapi.json` lama akan
  tetap menghasilkan tipe array dan pekerjaan ini mustahil diselesaikan dengan benar.
- 018 + 019 harus masuk **rilis yang sama**; melepas 018 sendirian akan membuat halaman assign DCS/WCP
  di deployment yang sudah jalan menerima objek padahal mengharapkan array.
