# Backlog 027 — Web app: "Keluar" tidak mengakhiri sesi SSO Authentik (pengguna berikutnya auto-login sebagai pengguna sebelumnya)

> **Repo:** — (ternyata **nol perubahan kode**; root cause murni konfigurasi Authentik)
> **Status:** ✅ **SELESAI 2026-07-14** — diverifikasi di browser sungguhan di produksi
> **Blocked by:** —
> **Skill yang dipakai:** `authentik-login-skill`

## ✅ HASIL — root cause & perbaikan (2026-07-14)

**Kode aplikasi ternyata sudah benar sepenuhnya. Tidak ada satu baris pun yang diubah.**

Dua dari tiga hipotesis di bawah **gugur** setelah diverifikasi:

| Hipotesis | Hasil | Bukti |
|---|---|---|
| 1. URL `end-session` salah | ❌ **GUGUR** | `curl` metadata OIDC → `end_session_endpoint` = `https://sajati.cantum.co.id/application/o/anjab-abk-web/end-session/`, **identik** dengan yang dibangun `new URL("end-session/", issuer)` di `logout/route.ts:32` |
| 2. `idToken` tidak ter-persist | ❌ **GUGUR** | `src/lib/auth/auth.ts:57-58` menyimpan `account.id_token` → `token.idToken`; `:68` mengekspornya ke `session.idToken`. Terbukti terkirim: URL logout produksi memuat `id_token_hint=eyJ...` yang valid |
| 3. Konfigurasi Authentik | ✅ **TERKONFIRMASI** | Provider `anjab-abk-web` (pk 6) punya 2 `redirect_uris`, **keduanya bertipe `authorization`**. **Tidak ada satu pun bertipe `logout`** — sehingga `post_logout_redirect_uri` yang dikirim aplikasi tidak pernah terdaftar sebagai tujuan logout yang sah, dan RP-initiated logout tidak pernah tuntas |

**Perbaikan yang diterapkan** (via `mcp__Authentik_Sajati__authentik_provider_update`, atas persetujuan
eksplisit user): menambahkan **dua** entri `redirect_uris` bertipe **`logout`** ke provider
`anjab-abk-web` — `https://anjab-abk.cantum-ypii.com` dan varian bergaris-miring
`https://anjab-abk.cantum-ypii.com/`. Kedua varian didaftarkan karena Authentik mencocokkan
`matching_mode: strict`, sedangkan nilai `post_logout_redirect_uri` berasal dari env `AUTH_URL`
produksi (`src/lib/config.ts:27`) yang tidak bisa dibaca dari luar. **Perubahan bersifat aditif** —
dua URI `authorization` yang sudah ada tidak disentuh.

Yang **sudah benar** dan tidak perlu diubah: `invalidation_flow` provider menunjuk ke
`default-invalidation-flow` ("Logout", pk `b31bf85d-…`) yang **punya stage** — jadi Authentik memang
sudah disiapkan untuk benar-benar mengakhiri sesi, bukan sekadar menampilkan pesan.

**Verifikasi di produksi (Playwright, browser sungguhan):**
1. Sesi hidup sebagai `Claude Agent (ANJAB-ABK)` di `/dashboard` → klik **"Keluar"**
2. → redirect ke `sajati.cantum.co.id/if/flow/default-invalidation-flow/` dengan `id_token_hint` +
   `post_logout_redirect_uri=https%3A%2F%2Fanjab-abk.cantum-ypii.com` (cocok dgn URI logout baru)
3. → flow invalidasi **berjalan tuntas**, sesi SSO mati, redirect balik ke aplikasi
4. → aplikasi menampilkan **form login Authentik dengan kolom username KOSONG**
5. → navigasi langsung ke `/dashboard` (repro persis fakta #3 di bawah) → **dilempar ke
   `/login?callbackUrl=…`**, BUKAN auto-login sebagai pengguna sebelumnya ✅

**Keputusan user (dikonfirmasi eksplisit):** logout aplikasi **memang harus** mengakhiri sesi SSO —
konteksnya komputer bersama (ruang guru, lab, perangkat pinjaman), di mana "Keluar" yang menyisakan
sesi hidup memberi rasa aman palsu. Alternatif di "Risiko & catatan" (biarkan sesi IdP hidup, cukup
perjelas UI) **ditolak**.

**Tidak ada entri `CHANGELOG.md`** dan tidak ada test baru: nol perubahan kode, jadi tidak ada yang
dirilis maupun yang bisa diregresikan oleh test unit. Yang menjaga perbaikan ini adalah konfigurasi
Authentik, bukan repo — lihat "Risiko & catatan" di bawah.

---

## Catatan investigasi asli (dipertahankan sebagai jejak keputusan)

> **Repo:** `anjab-abk-web-app` (kemungkinan juga konfigurasi Authentik — lihat "Langkah eksekusi")
> **Status:** ~~Menunggu investigasi (root cause belum dikonfirmasi)~~ — lihat hasil di atas
> **Blocked by:** —
> **Skill yang dipakai:** `frontend-development-skill`, `authentik-login-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Menekan tombol **"Keluar"** menghapus sesi aplikasi (cookie Auth.js) dan mengarahkan ke Authentik,
**tetapi sesi SSO di Authentik tetap hidup**. Akibatnya, begitu pengguna (atau siapa pun yang
memakai browser/komputer yang sama sesudahnya) membuka kembali halaman terproteksi, ia
**langsung masuk lagi sebagai pengguna yang sama — tanpa diminta password**.

Dampak nyata: di komputer bersama (ruang guru, lab, perangkat pinjaman — konteks yang sangat
mungkin di lingkungan sekolah), "Keluar" memberi **rasa aman yang palsu**. Pengguna berikutnya
mewarisi sesi pengguna sebelumnya, termasuk seluruh akses partisipan/admin-nya.

## Kondisi sekarang (verified)

| # | Fakta | Verifikasi |
|---|---|---|
| 1 | Route `POST /api/auth/logout` (`src/app/api/auth/logout/route.ts` ✓) **sudah** mencoba RP-initiated logout: membaca `session.idToken`, membangun URL `end-session/` dari `config.auth.issuer`, memasang `id_token_hint` & `post_logout_redirect_uri`, lalu `NextResponse.redirect(targetUrl, {status: 303})` | ✓ dibaca langsung |
| 2 | Route yang sama menghapus **semua** cookie Auth.js dengan benar, termasuk cookie ter-*chunk* (`authjs.session-token.0`, `.1`, …) dan varian `__Secure-`/`__Host-` — bagian ini terlihat sudah matang & sengaja diperbaiki sebelumnya | ✓ dibaca langsung |
| 3 | **Reproduksi produksi 2026-07-14**: klik "Keluar" sebagai partisipan → terarah ke halaman Authentik. Lalu navigasi ke `https://anjab-abk.cantum-ypii.com/dashboard` → **langsung masuk kembali sebagai pengguna yang SAMA**, tanpa prompt password | ✓ Playwright, diulang beberapa kali |
| 4 | Satu-satunya cara benar-benar berganti pengguna dalam pengujian adalah `page.context().clearCookies()` (menghapus cookie Authentik dari sisi klien) — bukti bahwa **cookie sesi Authentik masih hidup** setelah logout aplikasi | ✓ Playwright |
| 5 | `https://sajati.cantum.co.id/if/session-end/` (ditebak manual) → **404** — endpoint end-session yang benar perlu dipastikan dari metadata OIDC, bukan ditebak | ✓ `curl`/navigasi |

## Hipotesis penyebab (belum diverifikasi — ini yang harus dijawab lebih dulu)

1. **URL `end-session` salah.** Kode membangunnya sebagai `new URL("end-session/", issuer)`.
   Bila `issuer` = `https://sajati.cantum.co.id/application/o/anjab-abk-web/`, hasilnya
   `…/application/o/anjab-abk-web/end-session/` — **perlu dicek terhadap
   `end_session_endpoint` yang sebenarnya** di
   `{issuer}/.well-known/openid-configuration`. Bila salah, Authentik tidak pernah menerima
   permintaan logout, redirect gagal senyap, dan sesi IdP tetap hidup.
2. **`idToken` tidak tersedia di sesi.** Bila `session.idToken` `undefined` (mis. tidak
   di-*persist* di callback Auth.js), `id_token_hint` tidak terkirim → Authentik biasanya
   **menampilkan halaman konfirmasi logout** alih-alih langsung mengakhiri sesi; bila redirect
   lalu tidak diikuti sampai selesai, sesi tetap hidup.
3. **Authentik butuh konfirmasi/konfigurasi.** Provider OIDC di Authentik mungkin belum
   mengizinkan `post_logout_redirect_uri` yang dikirim, sehingga permintaan ditolak.

## Langkah eksekusi

### Langkah 1 — Tentukan `end_session_endpoint` yang benar (WAJIB pertama)

```bash
curl -s https://sajati.cantum.co.id/application/o/anjab-abk-web/.well-known/openid-configuration \
  | python3 -m json.tool | grep -i end_session
```
Bandingkan dengan URL yang dibangun `logout/route.ts`. Bila beda → itu penyebabnya; ambil
`end_session_endpoint` dari metadata (jangan hard-code `"end-session/"`).

### Langkah 2 — Pastikan `idToken` benar-benar ada di sesi

Cek `src/lib/auth/auth.ts` — apakah `id_token` disimpan ke token/sesi di callback `jwt`/`session`.
Bila tidak, `id_token_hint` tak pernah terkirim. Tambahkan bila perlu.

### Langkah 3 — Daftarkan `post_logout_redirect_uri` di Authentik

Lewat `mcp__Authentik_Sajati__*`: pastikan provider `anjab-abk-web` mengizinkan
`post_logout_redirect_uri` = URL aplikasi. (Skill `authentik-login-skill`.)

### Langkah 4 — Perbaiki & verifikasi

Perbaiki sesuai temuan Langkah 1–3, lalu **verifikasi manual di browser sungguhan**: login →
Keluar → buka `/dashboard` → **harus** diminta login lagi (prompt password), bukan auto-masuk.

## Kriteria penerimaan

- [ ] Setelah "Keluar", membuka `/dashboard` **meminta autentikasi ulang** (password), tidak
      auto-login sebagai pengguna sebelumnya
- [ ] Berlaku untuk akun partisipan maupun admin
- [ ] Logout tetap tidak bisa dipicu navigasi pasif (tetap `POST`-only — jangan regresikan
      perbaikan dari entri `[2026-07-13]` di `CLAUDE.md` web-app ✓)
- [ ] Bila Authentik menampilkan halaman konfirmasi logout, alur tetap berakhir di aplikasi
      (`post_logout_redirect_uri` bekerja)

## Skenario uji

- Unit test route logout: assert URL redirect yang dibangun **sama persis** dengan
  `end_session_endpoint` dari metadata (mock metadata), dan `id_token_hint` ikut terpasang saat
  `idToken` ada.
- `e2e/auth.spec.ts`: tambah test — login sebagai user A → logout → kunjungi halaman terproteksi
  → **harus** mendarat di form login Authentik (bukan dashboard sebagai A).
- `make test` hijau + `npm run build` sukses.

## Definition of done

- [ ] `make test` hijau, `npm run build` sukses
- [ ] Diverifikasi manual di browser sungguhan (bukan hanya unit test)
- [ ] `CHANGELOG.md` diperbarui
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Perbaikan ini hidup di Authentik, bukan di repo.** Tidak ada kode, test, atau `CHANGELOG` yang
  menjaganya — sehingga ia bisa **hilang diam-diam** bila provider `anjab-abk-web` dibuat ulang,
  di-restore dari blueprint/backup lama, atau dimigrasikan ke instance Authentik lain. Bila gejala
  auto-login muncul lagi, **periksa `redirect_uris` bertipe `logout` lebih dulu** sebelum menduga
  ada regresi kode.
- Konsekuensinya: **domain aplikasi tidak boleh berubah tanpa memperbarui URI logout ini.** Bila
  `AUTH_URL` produksi diganti (mis. pindah domain), kedua entri `logout` harus ikut diperbarui —
  kalau tidak, logout kembali gagal senyap dengan gejala yang persis sama.
- ~~Bila ternyata perilaku ini **disengaja** (SSO: logout aplikasi ≠ logout IdP, agar pengguna
  tetap login ke aplikasi lain di Cantum/Sajati), maka perbaikannya bukan memaksa logout IdP,
  melainkan **memperjelas UI**: ganti label "Keluar" atau tambahkan opsi kedua ("Keluar dari
  semua aplikasi"). **Konfirmasikan ke user** sebelum memilih arah — jangan asumsikan.~~
  → **Sudah dikonfirmasi ke user: logout WAJIB mengakhiri sesi SSO.** Alternatif ini ditolak.
- Temuan ini muncul saat simulasi SOP TI+OPM 2026-07-14 (memori `ti-opm-test-2-2026-07-14`),
  ketika berganti-ganti akun partisipan di Playwright ternyata selalu "nyangkut" di akun
  sebelumnya sampai cookie dibersihkan paksa.
