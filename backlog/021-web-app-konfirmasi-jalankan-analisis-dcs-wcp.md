# Backlog 021 — Web app: konfirmasi sebelum "Jalankan Analisis" DCS & WCP

> **Repo:** `anjab-abk-web-app`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Ditemukan saat menjalankan SOP Persiapan+Pelaksanaan DCS end-to-end via Playwright (3 responden
uji coba di `https://anjab-abk.cantum-ypii.com`, 2026-07-14): tombol **"Jalankan Analisis"** pada
instrumen DCS maupun WCP mengeksekusi aksi langsung tanpa dialog konfirmasi apa pun — berbeda dari
tombol **"Tutup Pengisian"** di komponen yang sama, yang sudah memakai `confirm()`.

Ini janggal karena dokumentasi SOP (`docs-usage/sop/pelaksanaan-dcs.md` dan `pelaksanaan-wcp.md`)
dan IK (`docs-usage/ik/dcs.md#b-aksi-instrumen`) secara eksplisit memperingatkan:

> **"Analisis tidak dapat dibatalkan"** — Setelah **Jalankan Analisis** berhasil (status
> Teranalisis), instrumen tidak dapat dibuka ulang lagi.

Aksi yang paling ireversibel di seluruh alur DCS/WCP justru satu-satunya yang tidak minta
konfirmasi eksplisit ke admin.

## Keputusan yang sudah dikunci

- Konfirmasi memakai `confirm()` browser biasa (native), pola identik `doTutup()` di komponen yang
  sama — BUKAN modal kustom baru.
- **Teks pesan sudah dikunci, pakai persis ini** (bukan placeholder — jangan improvisasi ulang):
  - DCS: `"Jalankan analisis DCS? Setelah analisis berhasil, instrumen TIDAK DAPAT dibuka ulang lagi."`
  - WCP: `"Jalankan analisis WCP? Setelah analisis berhasil, instrumen TIDAK DAPAT dibuka ulang lagi."`
- **Struktur `try/catch` `doAnalisis()` yang sudah ada TIDAK diubah** — fungsi ini SENGAJA tidak
  punya blok `finally` (beda dari `doTutup()`): `setLoading(false)` dipanggil manual di dalam
  `catch`, TIDAK dipanggil sama sekali di jalur sukses (karena jalur sukses langsung
  `router.push()` pindah halaman, `setLoading(false)` tidak perlu). Guard `confirm()` yang baru
  HANYA ditambah di baris paling atas fungsi, tidak menyentuh apa pun setelahnya.
- Cakupan: **DCS dan WCP**, dua file terpisah dengan struktur identik baris-per-baris (hanya beda
  penamaan DCS/WCP, path endpoint, dan target `router.push`) — satu perubahan yang sama diterapkan
  ke keduanya dalam satu commit/PR.
- **Tidak ada test existing untuk `aksi-instrumen` (DCS maupun WCP)** — dua file test baru dibuat
  dari nol (lihat Langkah 3), bukan menambah ke file yang sudah ada.

## Kondisi sekarang (verified 2026-07-14, baca ulang file sebelum edit — baris bisa bergeser)

- ✓ `src/app/(auth)/dcs/aksi-instrumen.tsx` — `doTutup()` baris 25–47 (SUDAH benar, referensi
  pola):
  ```tsx
  async function doTutup() {
    if (
      !confirm(
        "Tutup pengisian DCS? Setelah ditutup, partisipan tidak dapat lagi mengisi atau mengubah jawaban.",
      )
    )
      return;
    setLoading(true);
    setError(null);
    try {
      const client = withServerAuth(accessToken);
      const { error: apiError, response } = await client.POST("/api/v1/dcs/instrumen/tutup", {});
      const reqId = response.headers.get("x-request-id");
      if (apiError) throw toApiError(apiError, reqId);
      notifySukses("Instrumen ditutup.");
      router.refresh();
    } catch (err) {
      setError(pesanGagal(err));
      notifyGagal(err);
    } finally {
      setLoading(false);
    }
  }
  ```
- ✓ `src/app/(auth)/dcs/aksi-instrumen.tsx` — `doAnalisis()` baris 70–85 (BELUM ada guard, target
  perubahan):
  ```tsx
  async function doAnalisis() {
    setLoading(true);
    setError(null);
    try {
      const client = withServerAuth(accessToken);
      const { error: apiError, response } = await client.POST("/api/v1/dcs/analisis", {});
      const reqId = response.headers.get("x-request-id");
      if (apiError) throw toApiError(apiError, reqId);
      notifySukses("Analisis selesai.");
      router.push("/dcs/hasil");
    } catch (err) {
      setError(pesanGagal(err));
      notifyGagal(err);
      setLoading(false);
    }
  }
  ```
- ✓ `src/app/(auth)/wcp/aksi-instrumen.tsx` — struktur IDENTIK baris-per-baris dengan file DCS
  (`doTutup()` baris 25–47, `doAnalisis()` baris 70–85), hanya beda: teks "WCP" alih-alih "DCS" di
  pesan `doTutup`, endpoint `/api/v1/wcp/instrumen/tutup` & `/api/v1/wcp/analisis`, dan
  `router.push("/wcp/hasil")`.
- ✓ Tidak ada test file untuk komponen ini — `find src/test -maxdepth 1 -name "*.test.tsx"` tidak
  menghasilkan `dcs-aksi-instrumen.test.tsx`/`wcp-aksi-instrumen.test.tsx` maupun nama lain yang
  meng-import `AksiInstrumen`. Grep `"Tutup Pengisian"` dan `"Jalankan Analisis"` di `src/test/`
  nihil.
- ✓ Reproduksi manual: instrumen DCS live (status CLOSED, 3/3 responden ≥ `min_responden`), klik
  "Jalankan Analisis" → langsung `POST /api/v1/dcs/analisis` (200) → redirect ke `/dcs/hasil`,
  tanpa dialog apa pun sempat muncul.

## Langkah eksekusi

### Langkah 1 — DCS: tambah confirm() di `doAnalisis()`

File: `src/app/(auth)/dcs/aksi-instrumen.tsx`. Baca ulang baris 70–85 dulu (nomor baris di atas
adalah hasil observasi 2026-07-14, bisa bergeser bila file lain di repo berubah lebih dulu).

Tambahkan HANYA baris guard berikut sebagai baris pertama badan fungsi — jangan ubah apa pun lagi
di fungsi ini:

```tsx
async function doAnalisis() {
  if (
    !confirm(
      "Jalankan analisis DCS? Setelah analisis berhasil, instrumen TIDAK DAPAT dibuka ulang lagi.",
    )
  )
    return;
  setLoading(true);
  setError(null);
  try {
    const client = withServerAuth(accessToken);
    const { error: apiError, response } = await client.POST("/api/v1/dcs/analisis", {});
    const reqId = response.headers.get("x-request-id");
    if (apiError) throw toApiError(apiError, reqId);
    notifySukses("Analisis selesai.");
    router.push("/dcs/hasil");
  } catch (err) {
    setError(pesanGagal(err));
    notifyGagal(err);
    setLoading(false);
  }
}
```

### Langkah 2 — WCP: perubahan identik

File: `src/app/(auth)/wcp/aksi-instrumen.tsx`, fungsi `doAnalisis()` — sama persis, teks pesan
memakai kalimat WCP yang sudah dikunci di atas (`"Jalankan analisis WCP? Setelah analisis berhasil,
instrumen TIDAK DAPAT dibuka ulang lagi."`), endpoint & `router.push` tetap `/api/v1/wcp/analisis`
dan `/wcp/hasil` (tidak berubah dari sebelumnya).

### Langkah 3 — Buat 2 file test baru (belum ada sama sekali)

Buat `src/test/dcs-aksi-instrumen.test.tsx` dan `src/test/wcp-aksi-instrumen.test.tsx`, memakai
scaffold mocking yang SAMA PERSIS dengan pola existing di repo ini — jangan improvisasi pola
mocking baru:

- Mock router dari `src/test/transisi-sesi.test.tsx` baris 5–9 (menyediakan `refresh` DAN `push`,
  karena `doAnalisis` DCS/WCP memanggil `router.push`, `doTutup`/`doBukaUlang` memanggil
  `router.refresh`):
  ```tsx
  const refresh = vi.fn();
  const push = vi.fn();
  vi.mock("next/navigation", () => ({
    useRouter: () => ({ refresh, push }),
  }));
  ```
- Mock `client.POST` dari pola `src/test/dcs-assign-responden.test.tsx` baris 10–13:
  ```tsx
  const post = vi.fn();
  vi.mock("@/lib/api/client", () => ({
    withServerAuth: () => ({ POST: post }),
  }));
  ```
- Import komponen SETELAH kedua `vi.mock` di atas (urutan penting untuk hoisting Vitest — ikuti
  urutan di `dcs-assign-responden.test.tsx` baris 1–15):
  ```tsx
  import { AksiInstrumen } from "@/app/(auth)/dcs/aksi-instrumen"; // atau wcp untuk file WCP
  ```
- `window.confirm` di-spy dengan pola `src/test/transisi-sesi.test.tsx` baris 34 + 30–35
  (`beforeEach` reset `refresh`/`post`/`push`, `post.mockResolvedValue({ error: null, response: {
  headers: { get: () => "req-1" } } })`, `vi.spyOn(window, "confirm")`), lalu per-test
  `vi.mocked(window.confirm).mockReturnValue(false)` (Cancel) atau `.mockReturnValue(true)` (OK).
  `sonner` **tidak perlu** di-mock lagi di file test — sudah di-mock global di `vitest.setup.ts`;
  import `toast` dari `"sonner"` lalu `vi.mocked(toast.success)`/`vi.mocked(toast.error)` untuk
  assert, seperti `src/test/reset-katalog-panel.test.tsx` baris 1–19.
- Props `AksiInstrumen`: `{ instrumen: DcsInstrumenRead, jumlahSubmit: number, accessToken:
  string | undefined }` (tipe di `src/lib/api/schema.ts`, cari deklarasi `DcsInstrumenRead`/
  `WcpInstrumenRead` — field minimal untuk test: `id`, `status: "CLOSED"`, `min_responden`,
  `catatan`). Contoh instrumen test:
  ```tsx
  const instrumenClosed: DcsInstrumenRead = {
    id: "dcs",
    status: "CLOSED",
    min_responden: 3,
    catatan: null,
  } as unknown as DcsInstrumenRead;
  ```

Test case wajib per file (pola persis `transisi-sesi.test.tsx` baris 37–65, adaptasi ke tombol
"Jalankan Analisis"):

1. **Cancel tidak memanggil apa pun**: `window.confirm` return `false` → klik "Jalankan Analisis"
   → `expect(post).not.toHaveBeenCalled()` dan `expect(push).not.toHaveBeenCalled()`.
2. **OK melanjutkan alur seperti semula**: `window.confirm` return `true` → klik "Jalankan
   Analisis" → `await waitFor(() => expect(post).toHaveBeenCalledWith("/api/v1/dcs/analisis", {}))`
   (atau `/api/v1/wcp/analisis` untuk file WCP) → `expect(push).toHaveBeenCalledWith("/dcs/hasil")`
   (atau `/wcp/hasil`).
3. **`doTutup`/`doBukaUlang` tidak berubah perilaku** — opsional, boleh diskip bila menambah
   kompleksitas berlebih; fokus utama test baru adalah `doAnalisis`.

## Kriteria penerimaan

- [ ] Klik "Jalankan Analisis" pada instrumen DCS/WCP status CLOSED memunculkan `confirm()` dengan
      teks yang sudah dikunci di atas.
- [ ] Menekan **Cancel** pada dialog TIDAK memanggil `POST .../analisis` sama sekali — tidak ada
      side effect.
- [ ] Menekan **OK** melanjutkan alur seperti semula (POST → `notifySukses` → redirect ke halaman
      hasil).
- [ ] `doTutup()`/`doBukaUlang()` tidak berubah baris kodenya sama sekali.
- [ ] Dua file test baru (`dcs-aksi-instrumen.test.tsx`, `wcp-aksi-instrumen.test.tsx`) lulus,
      masing-masing minimal test #1 dan #2 di atas.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-web-app`
- [ ] `npm run build` sukses
- [ ] `CLAUDE.md` (`anjab-abk-web-app`) diperbarui dengan entri revisi desain singkat
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- Perubahan kode produksi murni satu blok `if` tambahan per file (2 file) — risiko regresi sangat
  kecil. Risiko utama ada di test baru: pastikan mock `useRouter` menyediakan `push` (bukan cuma
  `refresh` seperti pola lama `dcs-assign-responden.test.tsx`), atau `doAnalisis` akan gagal
  memanggil `router.push` di test dan melempar error "push is not a function".
- Ditemukan lewat testing manual di **instance produksi YPII** (`anjab-abk.cantum-ypii.com`), bukan
  di lingkungan E2E terisolasi — 3 responden uji coba (A. Widjianto, Agustina Megawati Siahaan,
  Agustinus Purnomo) sempat menjadi responden DCS sungguhan dengan jawaban acak; instrumen DCS
  sempat diubah `min_responden` 6→3 lalu dikembalikan ke 6 setelah pengujian, dan sempat berstatus
  **Teranalisis** (ireversibel) dengan data uji — perlu diperhatikan bila ada analisis DCS asli
  yang direncanakan setelah ini (hasil analisis DCS sudah terisi dengan data test, bukan data
  DCS asli — belum ada mekanisme "reset ke OPEN dari ANALYZED" di aplikasi; lihat item **022**
  untuk konteks backend terkait).
- **Konfirmasi empiris untuk WCP (2026-07-14, sesi terpisah)**: simulasi SOP Persiapan+Pelaksanaan
  WCP end-to-end (3 responden uji coba yang sama, 72 item jawaban acak) mereproduksi persis gejala
  yang sama di `src/app/(auth)/wcp/aksi-instrumen.tsx` — klik "Jalankan Analisis" pada instrumen
  CLOSED langsung redirect ke `/wcp/hasil` tanpa dialog `confirm()` apa pun, identik dengan DCS.
  Ini menguatkan (bukan mengubah) cakupan "DCS dan WCP" yang sudah dikunci di atas — tidak ada
  perubahan pada langkah eksekusi. Efek samping: instrumen WCP produksi sempat `min_responden`
  6→3 (dikembalikan ke 6 setelah pengujian) dan kini berstatus **Teranalisis** dengan data uji
  coba dari 3 partisipan yang sama (baris `wrsp_7c0ff89d`/`wrsp_f5fad014`/`wrsp_ab6c6a0f`).
