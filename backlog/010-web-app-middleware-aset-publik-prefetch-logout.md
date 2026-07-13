# Backlog 010 — Web app: middleware menelan aset PWA, dan link "Keluar" di-prefetch Next.js

> **Repo:** `anjab-abk-web-app`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Dua cacat infrastruktur frontend yang ditemukan saat simulasi end-to-end TI di deployment YPII
(2026-07-13) — keduanya muncul di **setiap halaman**, terlepas dari alat ukur mana yang dipakai:

**A. PWA rusak total.** `matcher` middleware Auth.js tidak mengecualikan aset publik, sehingga
`GET /manifest.webmanifest` di-redirect ke `/login` dan mengembalikan **HTML**. Browser melaporkan
`Manifest: Line: 1, column: 1, Syntax error` di console tiap halaman, dan aplikasi **tidak bisa
di-install sebagai PWA** — padahal PWA installable adalah syarat wajib per `frontend-development-skill`.
Nasib yang sama menimpa `sw.js` (service worker tidak akan pernah ter-serve sebagai JS), `icon.svg`,
dan `favicon.svg`.

**B. Link "Keluar" di-prefetch.** Tombol Keluar memakai `<Link href="/api/auth/logout">` tanpa
`prefetch={false}`. Karena link ini selalu ada di top bar (selalu di viewport), Next.js mem-**prefetch**
route handler logout tanpa klik pengguna. Yang teramati di console: rentetan error CORS ke endpoint
`end-session` Authentik pada setiap page load. Yang **berpotensi** lebih buruk: prefetch menembak GET ke
route handler logout sungguhan — bila handler itu punya efek samping (menghapus cookie sesi / meng-invalidate
sesi Authentik), pengguna bisa ter-logout spontan tanpa menekan apa pun.

## Keputusan yang sudah dikunci

1. **Aset publik tidak boleh melewati middleware auth.** `manifest.webmanifest`, `sw.js`, `icon.svg`,
   `favicon.svg` (dan berkas statis di `public/`) harus dapat diakses **tanpa login** — manifest & service
   worker memang di-fetch browser di luar konteks sesi.
2. **Logout tidak boleh bisa dipicu oleh prefetch.** Minimal `prefetch={false}`. Bila ternyata handler
   logout punya efek samping destruktif pada GET, itu masalah tersendiri yang **harus** ikut diperbaiki
   dalam item ini (lihat Langkah 3) — aksi yang mengubah state tidak boleh aman-diasumsikan pada GET
   yang bisa di-prefetch/di-crawl.
3. **Jangan melonggarkan matcher secara membabi buta.** Kecualikan berkas aset yang spesifik, bukan
   mematikan middleware untuk semua path ber-ekstensi.
4. Perubahan ini **tidak menyentuh** kontrak API atau `schema.ts`.

## Kondisi sekarang (verified)

| Fakta | Lokasi | ✓ |
|---|---|---|
| Matcher middleware — tidak mengecualikan manifest/sw/ikon | `src/middleware.ts:12` → `matcher: ["/((?!api/auth\|_next/static\|_next/image\|favicon.ico\|login\|$).*)"]` | ✓ |
| Manifest di-generate route metadata Next (TS, bukan JSON statis) — **tidak ada masalah sintaks di sumbernya** | `src/app/manifest.ts` (33 baris) | ✓ |
| Manifest di-link dari root layout | `src/app/layout.tsx:27` (`manifest: "/manifest.webmanifest"`) | ✓ |
| Tidak ada `public/manifest.webmanifest` (jadi bukan file statis yang rusak) | — | ✓ |
| Service worker sebagai file statis | `public/sw.js` | ✓ |
| Link "Keluar" pakai `<Link>` tanpa `prefetch={false}` | `src/components/shell/top-bar.tsx:40-45` | ✓ |
| `grep prefetch src/` → **0 hasil** (tidak ada satu pun link yang mematikan prefetch) | — | ✓ |
| Target logout adalah Route Handler nyata | `src/app/api/auth/logout/route.ts` | ✓ |

Gejala teramati di browser (simulasi 2026-07-13, live `anjab-abk.cantum-ypii.com`):
`Manifest: Line: 1, column: 1, Syntax error` berulang di tiap halaman, dan
`Access to fetch at 'https://sajati.cantum.co.id/application/o/anjab-abk-web/end-session/…' …
has been blocked by CORS policy` yang dipicu `GET /api/auth/logout?_rsc=…` (jelas sebuah prefetch RSC,
bukan klik).

Agen pelaksana **wajib membaca ulang** file-file di atas sebelum mengedit — nomor baris bisa bergeser.

## Langkah eksekusi

### Langkah 1 — Kecualikan aset publik dari middleware

`src/middleware.ts:12`. Tambahkan aset ke negative lookahead:

```ts
export const config = {
  matcher: [
    "/((?!api/auth|_next/static|_next/image|favicon.ico|favicon.svg|icon.svg|manifest.webmanifest|sw.js|login|$).*)",
  ],
};
```

Verifikasi setelahnya: `curl -I https://<host>/manifest.webmanifest` (tanpa cookie sesi) harus membalas
`200` dengan `content-type: application/manifest+json` — **bukan** `307`/`302` ke `/login` dan bukan
`text/html`. Idem `sw.js` → `application/javascript` (atau `text/javascript`).

### Langkah 2 — Matikan prefetch pada link Keluar

`src/components/shell/top-bar.tsx:40-45`:

```tsx
<Link href="/api/auth/logout" prefetch={false} className="…">
  Keluar
</Link>
```

### Langkah 3 — Periksa apakah handler logout aman terhadap GET

Baca `src/app/api/auth/logout/route.ts`. Tentukan apakah GET-nya punya efek samping (menghapus cookie
sesi, memanggil `end-session` Authentik).

- Bila **ya** (kemungkinan besar, mengingat gejala CORS ke `end-session` muncul dari sebuah prefetch):
  `prefetch={false}` saja **tidak cukup** sebagai pengaman — ia hanya menutup satu jalur pemicu. Ubah
  logout menjadi aksi yang tidak bisa dipicu navigasi pasif: form `POST` (`<form action="/api/auth/logout" method="post">`
  dengan tombol submit bergaya link) atau server action. Route handler `GET` dipertahankan hanya bila
  memang dibutuhkan untuk callback provider.
- Bila **tidak** (GET hanya merender halaman/redirect tanpa efek samping): cukup `prefetch={false}`, dan
  catat temuan itu di CHANGELOG agar tidak diselidiki ulang.

Langkah ini **wajib menghasilkan keputusan tertulis** (di CHANGELOG / entri Revisi Desain `CLAUDE.md`),
bukan dilewati diam-diam.

## Kriteria penerimaan

- [ ] `GET /manifest.webmanifest` tanpa sesi → `200`, `content-type: application/manifest+json`, body JSON valid.
- [ ] `GET /sw.js` tanpa sesi → `200` dengan content-type JavaScript.
- [ ] Console browser bersih dari `Manifest: … Syntax error` di seluruh halaman.
- [ ] Aplikasi lolos audit "installable" (Lighthouse/DevTools → Application → Manifest tampil utuh).
- [ ] Memuat halaman mana pun **tidak** menghasilkan request ke `/api/auth/logout` (cek tab Network:
      tidak ada `GET /api/auth/logout?_rsc=…`).
- [ ] Console bersih dari error CORS `end-session` saat page load.
- [ ] Halaman yang butuh auth **tetap** dilindungi middleware (kecualian tidak bocor ke route aplikasi).

## Skenario uji

1. **Unit/integration (Vitest, `src/test/`):** uji `config.matcher` — impor regex matcher dan pastikan
   `/manifest.webmanifest`, `/sw.js`, `/icon.svg`, `/favicon.svg` **tidak** cocok, sementara
   `/dashboard`, `/task-inventory`, `/kuesioner` **cocok** (masih dilindungi). Ini menjaga agar
   pelonggaran tidak kebablasan.
2. **Komponen:** render `top-bar` dan pastikan link Keluar punya `prefetch={false}` (atau, bila Langkah 3
   memilih form POST, pastikan ia berupa `<form method="post">` — bukan `<a>`/`<Link>` GET).
3. **Manual (setelah deploy):** DevTools → Application → Manifest harus menampilkan nama, ikon, dan
   `display: standalone` tanpa error; tab Network saat page load tidak memuat request ke
   `/api/auth/logout`; logout lewat klik tetap berfungsi.

```bash
cd anjab-abk-web-app && make test   # lint + typecheck + unit
npm run build                        # wajib sukses sebelum lapor selesai
```

## Definition of done

- [ ] `make test` hijau **dan** `npm run build` sukses
- [ ] `CHANGELOG.md` diperbarui (sebutkan hasil investigasi Langkah 3)
- [ ] `CLAUDE.md` repo diperbarui bila bentuk logout berubah (Revisi Desain)
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Melonggarkan matcher berisiko membuka route aplikasi tanpa auth bila polanya salah.** Test regex
  matcher (Skenario uji #1) bukan pelengkap — ia penjaga utama. Jangan lewatkan.
- Bila logout diubah menjadi form POST, tautan dari luar aplikasi (bookmark ke `/api/auth/logout`) berhenti
  bekerja. Ini konsekuensi yang diterima; konfirmasikan ke user bila ada dokumentasi/otomasi yang mengandalkan
  URL logout GET.
- Service worker (`public/sw.js`) selama ini kemungkinan **tidak pernah aktif** bagi pengguna. Setelah
  perbaikan ini ia mulai ter-register — perhatikan perilaku caching-nya pada rilis berikutnya (aset lama
  bisa nyangkut di cache). Periksa isi `sw.js` sebelum menganggap perbaikan ini bebas efek samping.
- Ikon PWA saat ini hanya SVG (`favicon.svg`, `icon.svg`). Sebagian platform (Android/Chrome) meminta
  PNG 192×192 & 512×512 untuk prompt install penuh. Di luar ruang lingkup item ini, tapi bila setelah
  perbaikan aplikasi masih belum menawarkan install, **inilah** kemungkinan penyebab lanjutannya —
  buat item terpisah.
