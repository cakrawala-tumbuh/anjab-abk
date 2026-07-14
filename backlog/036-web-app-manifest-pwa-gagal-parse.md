# Backlog 036 — Web app: PWA manifest gagal di-parse browser → aplikasi tidak installable

> **Repo:** `anjab-abk-web-app`
> **Status:** Siap dieksekusi (Langkah 1 = reproduksi; penyebab belum terkunci)
> **Blocked by:** —
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Browser menolak `manifest.webmanifest` dengan
`Manifest: Line: 1, column: 1, Syntax error` — **di setiap halaman** aplikasi produksi. Akibatnya
aplikasi **tidak dapat dipasang sebagai PWA**, padahal `frontend-development-skill` mensyaratkan
setiap web app installable sebagai PWA.

## Kondisi sekarang (verified)

Diamati di produksi 2026-07-14. Yang membingungkan: **berkasnya sendiri valid.**

| # | Fakta | Verifikasi |
|---|---|---|
| 1 | Console error muncul di **tiap** navigasi halaman: `Manifest: Line: 1, column: 1, Syntax error. @ https://anjab-abk.cantum-ypii.com/manifest.webmanifest` | ✓ `browser_console_messages` — satu-satunya jenis error konsol yang muncul di seluruh sesi pengujian |
| 2 | `curl https://…/manifest.webmanifest` → **200**, `content-type: application/manifest+json`, body **JSON valid** (557 byte, `json.loads()` sukses) | ✓ |
| 3 | **Tidak ada BOM** — 8 byte pertama = `7b 22 6e 61 6d 65 22 3a` (`{"name":`) | ✓ `xxd` |
| 4 | Respons membawa `vary: rsc, next-router-state-tree, next-router-prefetch, next-router-segment-prefetch` dan `x-nextjs-cache: HIT` | ✓ header `curl -i` |
| 5 | Diambil dengan header ala-browser (`Sec-Fetch-Dest: manifest`, `Accept: application/manifest+json`) → tetap JSON valid | ✓ |

⇒ Berkas valid saat diambil **tanpa kredensial/RSC**, tapi browser (yang mengirim cookie sesi dan
tunduk pada `Vary: rsc`) menerima sesuatu yang **bukan JSON**. Kandidat terkuat: **negosiasi
konten/caching RSC Next.js** menyajikan varian RSC/HTML untuk URL manifest, atau middleware
mengembalikan HTML (redirect login) untuk request manifest yang dianggap tak berkredensial.

Catatan: **backlog 010** ("middleware menelan aset PWA (manifest/sw)") sudah pernah menyentuh area
ini dan berstatus Selesai — jadi perbaikan middleware saja **tidak cukup**, atau ada regresi.

## Langkah eksekusi

### Langkah 1 — tangkap respons yang BENAR-BENAR diterima browser (jangan menebak)

Jalankan Playwright di produksi dan intersep request manifest, lalu **dump body + header apa
adanya**:

```js
page.on('response', async (r) => {
  if (r.url().includes('manifest.webmanifest')) {
    console.log(r.status(), JSON.stringify(r.headers(), null, 1));
    console.log((await r.text()).slice(0, 300));   // ← inilah yang gagal di-parse
  }
});
```

Bandingkan dengan hasil `curl`. Perbedaannya **adalah** bug-nya. Jangan menulis perbaikan sebelum
langkah ini menghasilkan bukti.

### Langkah 2 — perbaiki sesuai temuan Langkah 1

Kemungkinan & tindak lanjutnya:
- **Body = HTML halaman login** → middleware masih menahan `/manifest.webmanifest` untuk request
  tanpa/‌dengan kredensial tertentu → kecualikan path-nya (cek regresi backlog 010).
- **Body = payload RSC** → `Vary: rsc` + cache Next.js menyajikan varian salah; sajikan manifest
  sebagai **berkas statis di `public/`** alih-alih route handler, sehingga tidak ikut pipeline RSC.
- **Body kosong / terpotong** → isu di layer Traefik/proxy.

### Langkah 3 — jaring pengaman

Tambahkan test yang menegaskan manifest dapat di-`JSON.parse` **dari konteks browser** (bukan
`curl`), agar regresi ini tidak kembali diam-diam. Error ini sudah ada entah sejak kapan tanpa
pernah dilaporkan justru karena tidak ada yang memeriksa konsol.

## Kriteria penerimaan

- [ ] Nol error `Manifest: … Syntax error` di konsol pada seluruh halaman.
- [ ] Chrome DevTools → Application → Manifest menampilkan nama, ikon, dan tema tanpa error.
- [ ] Aplikasi dapat dipasang (prompt install muncul / kriteria installability terpenuhi).
- [ ] `make test` hijau, `npm run build` sukses.

## Risiko & catatan

Dampaknya **bukan** fungsional untuk alur ANJAB/ABK (semua fitur tetap jalan) — ini murni soal
PWA/installability + kebersihan konsol. Prioritas di bawah 023/024, tapi ia satu-satunya error
konsol yang tersisa, sehingga membiarkannya berarti error sungguhan berikutnya akan tenggelam
di antara noise.
