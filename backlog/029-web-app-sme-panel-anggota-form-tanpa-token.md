# Backlog 029 — Web app: `anggota-form.tsx` memanggil `/partisipan` tanpa token → akan 401 (senyap) begitu backend 025 di-deploy

> **Repo:** `anjab-abk-web-app`
> **Status:** Siap dieksekusi
> **Blocked by:** — (tidak diblokir, tapi **wajib dirilis bersama** backend 025 — lihat "Risiko & catatan")
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Backlog **025** memasang guard autentikasi di seluruh endpoint baca backend, termasuk
`GET /api/v1/partisipan`. Audit Langkah 5 item 025 menemukan **tepat satu** call site di web app
yang memanggil endpoint itu **tanpa Bearer token** — ia akan mulai menerima **401** begitu backend
025 di-deploy.

Yang membuatnya berbahaya: kegagalannya **senyap**. Komponen menelan error dan merender daftar
kosong, sehingga admin melihat **"Belum ada anggota"** pada SME panel yang sebenarnya **punya**
anggota — tanpa pesan error apa pun. Ini persis kelas bug *notifikasi bohong* / *error ditelan*
yang sudah diberantas backlog **017** (mutasi) dan **026** (jalur baca Server Component); call site
ini luput karena ia satu-satunya pemanggilan API dari **browser** (`useEffect`), bukan Server
Component.

## Kondisi sekarang (verified)

Diverifikasi 2026-07-14 lewat audit kode langsung (Langkah 5 backlog 025).

| # | Fakta | Verifikasi |
|---|---|---|
| 1 | `src/app/(auth)/master-data/sme-panel/[id]/anggota-form.tsx:230-235` memanggil `GET /api/v1/partisipan` memakai klien `api` **telanjang** (tanpa middleware Bearer) dari `useEffect` browser | ✓ dibaca langsung |
| 2 | Setelah backend 025 aktif, endpoint itu menuntut token → call site ini dapat **401** | ✓ konsekuensi langsung dari 025 |
| 3 | Kegagalannya **ditelan dua kali**: `data?.items ?? []` **dan** `.catch(() => setPartisipanList([]))` → daftar kosong, tanpa toast, tanpa error | ✓ dibaca langsung |
| 4 | Komponen **sudah menerima `accessToken` sebagai prop**, dan **tiga handler mutasi tetangganya di berkas yang sama** sudah memakai `withServerAuth(accessToken)` — jadi perbaikannya menyelaraskan dengan pola yang sudah ada di berkas itu sendiri | ✓ dibaca langsung |
| 5 | Ini **satu-satunya** call site bermasalah: 103 impor `withServerAuth` di `src/app/(auth)/**`, nol `fetch` mentah ke backend, nol pemakaian `api` telanjang lain, nol SSG/build-time fetch, halaman publik tidak memanggil API sama sekali | ✓ audit repo-wide (Langkah 5 item 025) |
| 6 | Satu-satunya call site `/search` (`task-inventory/[sesi_id]/page.tsx:74`) **sudah** terautentikasi — aman meski 025 ikut men-guard 9 `POST .../search` | ✓ dibaca langsung |

## Keputusan yang sudah dikunci

- Perbaikannya **bukan** sekadar menambahkan token lalu selesai. Pola telan-senyap
  (`?? []` + `.catch(() => setPartisipanList([]))`) **juga wajib dibereskan**, sejalan dengan
  invariant yang baru dikunci backlog 026 di `CLAUDE.md` web-app. Kalau hanya token yang
  ditambahkan, bug senyapnya tetap hidup dan akan menyembunyikan kegagalan **berikutnya**.
- Karena ini komponen klien (bukan Server Component), pelaporan gagalnya lewat
  **`notifyGagal`** (`src/lib/notify.ts`, backlog 017) — bukan `GagalMuat` (yang dirender di
  server, backlog 026).

## Langkah eksekusi

### Langkah 1 — Kirim token

Di `anggota-form.tsx:230-235`, ganti pemanggilan `api` telanjang dengan `withServerAuth(accessToken)`,
meniru **persis** pola tiga handler mutasi di berkas yang sama.

### Langkah 2 — Hentikan telan-senyap

Buang `.catch(() => setPartisipanList([]))`. Saat panggilan gagal: panggil `notifyGagal` (sertakan
`X-Request-ID` sesuai pola `ApiError` yang sudah ada), dan **jangan** merender daftar kosong yang
tak terbedakan dari "memang belum ada anggota" — bedakan state *gagal-muat* dari state *kosong*.

### Langkah 3 — Sisir pola yang sama di komponen klien lain

Audit 026 menyasar `src/app` (Server Component). Sisir sekali lagi khusus **komponen klien**
(`"use client"` + `useEffect` + panggilan API) untuk pola `api` telanjang / `.catch(() => set…([]))`
yang luput dari kedua audit. Catat temuannya; kalau nol, katakan nol.

## Kriteria penerimaan

- [ ] `anggota-form.tsx` mengirim Bearer token saat memanggil `GET /api/v1/partisipan`
- [ ] Backend dengan guard 025 aktif → halaman anggota SME panel **tetap berfungsi penuh** (daftar
      partisipan tampil, anggota bisa ditambah/dihapus)
- [ ] Panggilan gagal (401/500) → **pesan error terlihat** (`notifyGagal` + `X-Request-ID`),
      **bukan** "Belum ada anggota"
- [ ] State "gagal memuat" terbedakan dari state "memang belum ada anggota"
- [ ] Nol pemakaian klien `api` telanjang tersisa di komponen klien

## Skenario uji

- Test: mock `GET /api/v1/partisipan` → 401 → assert `notifyGagal` terpanggil **dan** UI tidak
  menampilkan "Belum ada anggota".
- Test: mock sukses dengan 0 partisipan → assert UI menampilkan state kosong yang sah (bukan error).
- Test: assert pemanggilan membawa header `Authorization`.
- `make test` hijau + `npm run build` sukses.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-web-app`, `npm run build` sukses
- [ ] `CHANGELOG.md` diperbarui
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Urutan rilis mengikat.** Backend 025 **tidak boleh** di-deploy sendirian tanpa item ini:
  begitu guard aktif, halaman anggota SME panel akan diam-diam menampilkan panel kosong. Deploy
  keduanya bersama, atau web-app lebih dulu (mengirim token ke endpoint yang belum menuntutnya
  tetap aman — token diabaikan).
- Item ini lahir sebagai **temuan Langkah 5 backlog 025** (audit "verifikasi web app tidak rusak"),
  bukan dari laporan pengguna. Tanpa audit itu, backend 025 akan merusak produksi secara senyap.
