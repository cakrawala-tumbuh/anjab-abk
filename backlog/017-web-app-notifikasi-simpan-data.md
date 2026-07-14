# Backlog 017 — Web app: notifikasi sukses/gagal di setiap penyimpanan data

> **Repo:** `anjab-abk-web-app`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Setiap operasi penyimpanan data (POST/PATCH/PUT/DELETE ke backend) harus memberi tahu user apakah
operasinya **berhasil** atau **gagal**. Saat ini web app tidak punya sistem notifikasi sama sekali:
tak ada library toast, tak ada `<Toaster>`. Tiap komponen menangani notifikasinya sendiri, dengan
hasil yang tidak konsisten dan berlubang.

Audit atas 49 berkas / ~55 call site mutasi (2026-07-13) menemukan:

- **Kegagalan** hampir selalu diberitahukan, tapi lewat **4 mekanisme berbeda** — `form-server-error`,
  `bg-red-50`, `<p className="text-red-600">`, dan `alert()` browser — plus **1 tempat yang menelan
  error bulat-bulat**.
- **Keberhasilan** adalah lubang besarnya: dari ~55 call site, **hanya 6** yang memberi konfirmasi
  sukses eksplisit. Sisanya mengandalkan efek samping (`router.push` / `router.refresh()`) yang, bila
  tidak mengubah apa pun yang terlihat, membuat user tidak bisa membedakan **simpan-berhasil** dari
  **tidak-terjadi-apa-apa**.

Kasus terburuk ada di `review-form.tsx` (Tahap 2): koordinator menyimpan keputusan untuk seluruh
daftar task, dan bila sukses yang terjadi hanya `router.refresh()` — halaman kembali menampilkan
pilihan yang sama persis, tanpa pesan apa pun.

## Keputusan yang sudah dikunci

1. **Library: `sonner`.** Dipasang sebagai dependency baru + `<Toaster />` di `src/app/providers.tsx`.
   Tidak membangun sistem toast sendiri.
2. **Helper terpusat di `src/lib/notify.ts`** — `notifySukses(pesan)` dan `notifyGagal(err)`. Semua
   call site memanggil helper ini; dilarang memanggil `toast.*` langsung dari komponen.
3. **`notifyGagal` menampilkan `requestId`** (dari header `X-Request-ID`) sebagai deskripsi toast bila
   ada, supaya user bisa menyebutkannya saat lapor masalah. `ApiError` sudah membawa field ini
   (`src/lib/api/errors.ts`).
4. **Error inline TETAP dipertahankan** di form panjang (tahap1/2/3, dcs/wcp/opm isi, semua form
   master-data). Toast bersifat **tambahan**, bukan pengganti — pesan error tidak boleh hilang setelah
   4 detik pada form yang panjang. Pola: `setServerError(...)` **dan** `notifyGagal(err)`.
5. **`alert()` browser dihapus total** dari seluruh kode. Diganti `notifyGagal(err)`.
6. **Bug "notifikasi bohong" ikut diperbaiki di item ini** (bug 1–5 di bawah) — semuanya adalah kasus
   notifikasi yang salah/hilang, jadi masih satu lingkup. Bug "skip tersembunyi" DCS/WCP **TIDAK** —
   itu butuh perubahan backend, dipecah ke item **018** (backend) + **019** (web-app).
7. Teks notifikasi **Bahasa Indonesia**, kalimat lengkap, menyebut objeknya
   (mis. `"Sekolah berhasil ditambahkan."`, bukan `"Berhasil"`).

## Kondisi sekarang (verified)

✓ = sudah dibaca langsung dari kode pada 2026-07-13. Baris bisa bergeser — **baca ulang sebelum edit**.

### Infrastruktur

| Fakta | Bukti |
|---|---|
| Tidak ada library toast terpasang | ✓ `grep -E "sonner\|toast\|react-hot" package.json` → nol hasil |
| Tidak ada `<Toaster>` di mana pun | ✓ `grep -rn "Toaster" src` → nol hasil |
| `src/components/ui/` **tidak ada** (shadcn belum dipakai) | ✓ `ls src/components/` → `calhr.ts`, `pwa-register.tsx`, `shell/`, `theme-provider.tsx`, `theme-toggle.tsx` |
| `Providers` sudah ada, membungkus `QueryClientProvider` + `ThemeProvider` | ✓ `src/app/providers.tsx` |
| `ApiError` sudah membawa `code`, `message`, `details`, `requestId` | ✓ `src/lib/api/errors.ts` |
| `openapi-fetch` **tidak melempar** pada HTTP 4xx/5xx — mengembalikan `{ data, error, response }` | ✓ pola `if (error) throw toApiError(error, requestId)` dipakai di ~54 dari ~55 call site |

### Bug yang harus diperbaiki (bagian dari item ini)

| # | Berkas : baris | Masalah |
|---|---|---|
| **1** | ✓ `src/app/(auth)/master-data/sme-panel/[id]/anggota-form.tsx:167` | **Error ditelan bulat-bulat.** `await client.PATCH("/api/v1/sme-panel/{panel_id}", {...})` — hasil `{ error }` tidak pernah dibaca, tidak ada `catch` (hanya `try { … } finally { setLoading(false) }`), tidak ada state error, tidak ada yang dirender. `router.refresh()` tetap jalan walau 403/409/500. Satu-satunya mutasi di seluruh app yang begini. |
| **2** | ✓ `src/app/(auth)/task-inventory/tahap2/[sesi_id]/review-form.tsx:62` | **Sukses tanpa notifikasi apa pun.** Setelah POST `/sesi/{id}/tahap2` sukses, satu-satunya aksi adalah `router.refresh()`. Tak ada pesan, tak ada navigasi. User tidak bisa membedakan simpan-berhasil dari no-op. |
| **3** | ✓ `src/app/(auth)/task-inventory/[sesi_id]/atur-koordinator.tsx:95` | **Pesan sukses tidak pernah muncul.** Banner `✓ Koordinator diperbarui` digate `sukses && !berubah`; `berubah` dihitung dari prop Server Component (`koordinatorId`) yang masih basi sesaat setelah PATCH → banner tersembunyi tepat saat seharusnya tampil. |
| **4** | ✓ `src/app/(auth)/opm/isi/[responden_id]/opm-form.tsx:92-122` | **Notifikasi berbohong.** `buildJawabanPayload()` memfilter task yang belum lengkap 3 dimensi (`isTaskLengkap`), lalu user tetap diberi `setSaveMessage("Draft tersimpan.")` (L122). Karena endpoint `PUT` = replace penuh, task yang tadinya lengkap-dan-tersimpan bisa **terhapus di server** saat di-edit jadi parsial. DCS/WCP tidak punya masalah ini (mengirim seluruh `skor`). |
| **5** | ✓ `src/app/(auth)/master-data/task-inventory/utilitas/reset-katalog-panel.tsx:60` | **Stale closure.** Pesan pemulihan `"Katalog sudah dikosongkan tapi reseed gagal…"` digate `emptied`, tapi di dalam `catch` nilai `emptied` masih `false` (tertangkap saat render; `setEmptied(true)` di L47 tidak mengubah binding pada invocation yang sama). Justru pada skenario paling berbahaya — katalog **sudah terhapus**, reseed gagal — user tidak diberi tahu. |
| **6** | ✓ 6 berkas (lihat tabel di bawah) | **`alert()` browser** dipakai untuk melaporkan kegagalan hapus. Bisa diblokir browser, tak punya `role="alert"`, tidak konsisten. |

Berkas ber-`alert()` (bug 6):

| Berkas : baris |
|---|
| ✓ `src/app/(auth)/master-data/sme-panel/[id]/anggota-form.tsx:127` |
| ✓ `src/app/(auth)/task-inventory/[sesi_id]/hapus-responden.tsx:31` |
| ✓ `src/app/(auth)/dcs/hapus-responden.tsx:30` |
| ✓ `src/app/(auth)/wcp/hapus-responden.tsx:30` |
| ✓ `src/app/(auth)/opm/[sesi_id]/hapus-responden.tsx:30` |
| ✓ `src/app/(auth)/time-study/[penugasan_id]/hapus-penugasan.tsx:39` |

### Inventaris call site (~55, di 49 berkas)

Kolom **Sukses sekarang**: `—` = tidak ada notifikasi apa pun; `push` = hanya `router.push`;
`refresh` = hanya `router.refresh()`; `✓` = sudah ada pesan sukses eksplisit.

**Master data** (semua `serverError` inline pada gagal)

| Berkas | Mutasi | Sukses sekarang |
|---|---|---|
| `master-data/sekolah/tambah/sekolah-form.tsx:49` | POST sekolah | push |
| `master-data/jabatan/tambah/jabatan-form.tsx:53` | POST jabatan | push |
| `master-data/jenjang-pendidikan/tambah/jenjang-form.tsx:41` | POST jenjang | push |
| `master-data/mata-pelajaran/tambah/mata-pelajaran-form.tsx:55` | POST mapel | push |
| `master-data/sme-panel/tambah/sme-panel-form.tsx:42` | POST panel | push |
| `master-data/tugas-pokok/tambah/tugas-pokok-form.tsx:68,78` | PATCH / POST | push |
| `master-data/uraian-tugas/tambah/uraian-tugas-form.tsx:121,131` | PATCH / POST | push |
| `master-data/detil-tugas/tambah/detil-tugas-form.tsx:80,94` | PATCH / POST | push |
| `master-data/tugas-pokok/[id]/hapus-button.tsx:25` | DELETE | push |
| `master-data/uraian-tugas/[id]/hapus-button.tsx:25` | DELETE | push |
| `master-data/detil-tugas/[id]/hapus-button.tsx:25` | DELETE | push |
| `master-data/sme-panel/[id]/anggota-form.tsx:39` | POST anggota | refresh |
| `master-data/sme-panel/[id]/anggota-form.tsx:118` | DELETE anggota | refresh (**alert** on fail) |
| `master-data/sme-panel/[id]/anggota-form.tsx:167` | PATCH koordinator | refresh (**BUG 1: error ditelan**) |
| `master-data/dcs/[kode]/dcs-item-editor.tsx:108` | PATCH item | refresh |
| `master-data/wcp/[kode]/wcp-item-editor.tsx:109` | PATCH item | refresh |
| `master-data/task-inventory/utilitas/reset-katalog-panel.tsx:44,49` | POST purge / reseed | ✓ (**BUG 5**) |

**Task Inventory**

| Berkas | Mutasi | Sukses sekarang |
|---|---|---|
| `task-inventory/buat/ti-sesi-form.tsx:73` | POST sesi | push |
| `task-inventory/[sesi_id]/tambah-responden.tsx:51` | POST responden | — |
| `task-inventory/[sesi_id]/assign-responden-banyak.tsx:64` | POST bulk | ✓ (created + skipped) |
| `task-inventory/[sesi_id]/hapus-responden.tsx:23` | DELETE responden | refresh (**alert** on fail) |
| `task-inventory/[sesi_id]/atur-koordinator.tsx:49` | PATCH koordinator | ✓ tapi **BUG 3** |
| `task-inventory/[sesi_id]/transisi-sesi.tsx:49,50` | POST transisi (5 endpoint) | refresh |
| `task-inventory/[sesi_id]/transisi-sesi.tsx:93` | DELETE sesi | push |
| `task-inventory/tahap1/[responden_id]/seleksi-form.tsx:150` | PUT draft | ✓ "Draft tersimpan." |
| `task-inventory/tahap1/[responden_id]/seleksi-form.tsx:177,187` | PUT + POST submit | push |
| `task-inventory/tahap2/[sesi_id]/review-form.tsx:56` | POST tahap2 | — (**BUG 2**) |
| `task-inventory/tahap3/[responden_id]/detail-form.tsx:172` | PUT draft | ✓ "Draft tersimpan." |
| `task-inventory/tahap3/[responden_id]/detail-form.tsx:198,205` | PUT + POST submit | push |

> `task-inventory/[sesi_id]/page.tsx:75` adalah **POST-shaped read** (`/api/v1/sme-panel/search`) —
> bukan mutasi. **Jangan disentuh.**

**DCS / WCP** (struktur identik, baris sama)

| Berkas | Mutasi | Sukses sekarang |
|---|---|---|
| `dcs/aksi-instrumen.tsx:35,51,70` & `wcp/…` | POST tutup / buka-ulang / analisis | refresh, refresh, push |
| `dcs/assign-responden.tsx:51` & `wcp/…` | POST responden (bulk) | — |
| `dcs/edit-instrumen.tsx:46` & `wcp/…` | PATCH instrumen | refresh |
| `dcs/hapus-responden.tsx:23` & `wcp/…` | DELETE responden | refresh (**alert** on fail) |
| `dcs/isi/[responden_id]/dcs-form.tsx:50` & `wcp/…` | PUT draft | ✓ "Draft tersimpan." |
| `dcs/isi/[responden_id]/dcs-form.tsx:78,88` & `wcp/…` | PUT + POST submit | ✓ panel hijau |

**OPM**

| Berkas | Mutasi | Sukses sekarang |
|---|---|---|
| `opm/buat/opm-sesi-form.tsx:72` | POST sesi | push |
| `opm/[sesi_id]/tambah-responden.tsx:45` | POST responden | — |
| `opm/[sesi_id]/assign-responden-banyak.tsx:63` | POST bulk | ✓ (created + skipped) |
| `opm/[sesi_id]/hapus-responden.tsx:23` | DELETE responden | refresh (**alert** on fail) |
| `opm/[sesi_id]/transisi-sesi.tsx:26,44,67` | POST buka/tutup, POST analisis, DELETE | refresh, push, push |
| `opm/isi/[responden_id]/opm-form.tsx:113` | PUT draft | ✓ tapi **BUG 4** |
| `opm/isi/[responden_id]/opm-form.tsx:141,151` | PUT + POST submit | ✓ panel hijau |

**Time Study / Partisipan**

| Berkas | Mutasi | Sukses sekarang |
|---|---|---|
| `time-study/buat/ts-penugasan-form.tsx:47` | POST penugasan | push |
| `time-study/tugaskan-banyak/ts-penugasan-bulk-form.tsx:64` | POST bulk | ✓ (created + skipped) |
| `time-study/isi/[penugasan_id]/tambah/ts-log-form.tsx:86` | POST log | push |
| `time-study/isi/…/[log_id]/edit/ts-log-edit-form.tsx:90` | PATCH log | push |
| `time-study/[penugasan_id]/toggle-aktif.tsx:26` | PATCH aktif | refresh |
| `time-study/[penugasan_id]/hapus-penugasan.tsx:28` | DELETE | push (**alert** on fail) |
| `partisipan/tambah/partisipan-form.tsx:75` | POST partisipan | push |
| `partisipan/[id]/edit-partisipan-form.tsx:87` | PATCH partisipan | ✓ "Data berhasil disimpan." |

## Langkah eksekusi

### Langkah 1 — Pasang `sonner` + `<Toaster />`

```bash
npm install sonner
```

Di `src/app/providers.tsx`, tambahkan `<Toaster />` **di dalam** `ThemeProvider` (supaya toast ikut
tema light/dark) tapi **di luar** `{children}`:

```tsx
import { Toaster } from "sonner";
// …
<ThemeProvider>
  {children}
  <Toaster position="top-right" richColors closeButton />
</ThemeProvider>
```

`richColors` memberi warna hijau/merah bawaan sonner; `closeButton` supaya toast error bisa ditutup
manual (penting karena toast error kita set `duration: Infinity`, lihat Langkah 2).

### Langkah 2 — Buat `src/lib/notify.ts`

```ts
/**
 * Notifikasi toast untuk hasil operasi penyimpanan data.
 *
 * Dipakai berdampingan dengan error inline pada form panjang — toast bersifat
 * tambahan, bukan pengganti. Jangan memanggil `toast.*` langsung dari komponen.
 */
import { toast } from "sonner";
import { ApiError } from "@/lib/api/errors";

export function notifySukses(pesan: string): void {
  toast.success(pesan);
}

export function pesanGagal(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return "Terjadi kesalahan.";
}

export function notifyGagal(err: unknown): void {
  const requestId = err instanceof ApiError ? err.requestId : null;
  toast.error(pesanGagal(err), {
    description: requestId ? `ID permintaan: ${requestId}` : undefined,
    duration: Infinity,
  });
}
```

`duration: Infinity` — toast **error** tidak boleh hilang sendiri; user harus menutupnya. Toast sukses
memakai durasi bawaan sonner (4 detik).

`pesanGagal` diekspor supaya call site yang juga punya error inline tidak perlu menduplikasi logika
`err instanceof Error ? err.message : "…"`:

```ts
} catch (err) {
  setServerError(pesanGagal(err));
  notifyGagal(err);
}
```

### Langkah 3 — Perbaiki bug 1 (error ditelan) di `sme-panel/[id]/anggota-form.tsx`

Fungsi set/unset koordinator (sekitar L160-175) harus mengikuti pola yang sama dengan mutasi lain:

```ts
try {
  const client = withServerAuth(accessToken);
  const { error, response } = await client.PATCH("/api/v1/sme-panel/{panel_id}", {
    params: { path: { panel_id: panelId } },
    body: { koordinator_id: newKoordinatorId },
  });
  const requestId = response.headers.get("x-request-id");
  if (error) throw toApiError(error, requestId);
  notifySukses(
    newKoordinatorId ? "Koordinator panel diperbarui." : "Koordinator panel dikosongkan.",
  );
  router.refresh();
} catch (err) {
  notifyGagal(err);
} finally {
  setLoading(false);
}
```

Komponen ini tidak punya tempat natural untuk error inline (tombol di dalam baris tabel) — **toast saja
sudah cukup** di sini.

### Langkah 4 — Perbaiki bug 2 (Tahap 2 sukses senyap) di `tahap2/[sesi_id]/review-form.tsx`

Setelah POST sukses (L62), tambahkan notifikasi yang **menyebut jumlah keputusan tersimpan**, karena
form ini membuang task yang belum diputuskan dari payload (L52-54):

```ts
const dikirim = payload.keputusan.length;
const dilewati = pending.length;
notifySukses(
  dilewati > 0
    ? `${dikirim} keputusan tersimpan. ${dilewati} task belum diputuskan dan tidak disertakan.`
    : `${dikirim} keputusan tersimpan.`,
);
router.refresh();
```

Nama variabel menyesuaikan kode aktual — **baca ulang** L40-62 sebelum edit.

### Langkah 5 — Perbaiki bug 3 (banner tak pernah muncul) di `[sesi_id]/atur-koordinator.tsx`

Buang gate `!berubah` pada banner sukses. Ganti seluruh mekanisme `sukses` dengan `notifySukses(...)`
setelah PATCH sukses, dan hapus state `sukses` beserta banner inline-nya (L95-99) — toast sudah
menggantikannya, dan tidak ada lagi ketergantungan pada prop basi.

Error inline (`<p role="alert">`, L90-94) **tetap dipertahankan**, tambahkan `notifyGagal(err)`.

### Langkah 6 — Perbaiki bug 4 (notifikasi bohong) di `opm/isi/[responden_id]/opm-form.tsx`

`buildJawabanPayload()` (L92-105) membuang task yang belum lengkap 3 dimensi. User harus **diberi tahu**
berapa yang benar-benar tersimpan, bukan sekadar "Draft tersimpan.":

```ts
const total = sortedTask.length;
const tersimpan = payload.jawaban.length;   // sesuaikan nama field aktual
const pesan =
  tersimpan === total
    ? "Draft tersimpan."
    : `Draft tersimpan — ${tersimpan} dari ${total} task. ` +
      `Task yang penilaiannya belum lengkap (3 dimensi) tidak ikut tersimpan.`;
setSaveMessage(pesan);
notifySukses(pesan);
```

Pesan inline (`setSaveMessage`) **tetap** — respondent perlu bisa membacanya ulang.

> **Catatan:** ini hanya memperbaiki *notifikasinya* — perilaku `PUT` yang menghapus task parsial dari
> server **tidak** diubah di item ini. Bila user ingin perilakunya berubah (mis. task parsial tetap
> disimpan sebagian), itu perubahan backend + kontrak API → item backlog terpisah.

### Langkah 7 — Perbaiki bug 5 (stale closure) di `utilitas/reset-katalog-panel.tsx`

Ganti pembacaan state `emptied` di dalam `catch` dengan **variabel lokal** yang hidup di dalam scope
`resetKatalog`:

```ts
async function resetKatalog() {
  let sudahDikosongkan = false;          // ← lokal, bukan state
  try {
    // … POST purge …
    if (errPurge) throw toApiError(errPurge, reqIdPurge);
    sudahDikosongkan = true;
    setEmptied(true);
    // … POST reseed …
  } catch (err) {
    const pesan = sudahDikosongkan
      ? "Katalog sudah dikosongkan tapi reseed gagal — klik ulang untuk mengisi ulang."
      : pesanGagal(err);
    setError(pesan);
    notifyGagal(sudahDikosongkan ? new Error(pesan) : err);
  }
}
```

State `emptied` saat ini tidak pernah dibaca di JSX (dead state) — **hapus** bila memang tidak dipakai
setelah perubahan ini.

Tambahkan juga `notifySukses("Katalog berhasil di-reset.")` pada jalur sukses; panel `ringkasan` yang
sudah ada (L80-93) tetap dipertahankan karena memuat hitungan deleted/created.

### Langkah 8 — Hapus semua `alert()` (bug 6)

Di 6 berkas pada tabel "Berkas ber-`alert()`" di atas, ganti:

```ts
alert(err instanceof Error ? err.message : "Gagal menghapus responden.");
```

dengan:

```ts
notifyGagal(err);
```

dan tambahkan `notifySukses("Responden berhasil dihapus.")` (sesuaikan objeknya) sebelum
`router.refresh()` / `router.push(...)` pada jalur sukses.

### Langkah 9 — Tambahkan `notifySukses(...)` ke SELURUH call site sisanya

Untuk tiap baris di "Inventaris call site" yang kolom **Sukses sekarang**-nya `—`, `push`, atau
`refresh`, tambahkan `notifySukses(<pesan>)` **sebelum** `router.push(...)` / `router.refresh()`.
Toast bertahan lintas navigasi App Router, jadi memanggilnya sebelum `push` aman.

Untuk tiap `catch`, tambahkan `notifyGagal(err)` **berdampingan** dengan `setServerError(...)` yang
sudah ada (jangan hapus yang inline).

Teks yang dipakai (kunci — jangan diubah-ubah sendiri):

| Call site | Pesan sukses |
|---|---|
| POST sekolah | `Sekolah berhasil ditambahkan.` |
| POST jabatan | `Jabatan berhasil ditambahkan.` |
| POST jenjang | `Jenjang pendidikan berhasil ditambahkan.` |
| POST mapel | `Mata pelajaran berhasil ditambahkan.` |
| POST panel | `SME panel berhasil ditambahkan.` |
| POST/PATCH tugas pokok | `Tugas pokok berhasil ditambahkan.` / `…berhasil diperbarui.` |
| POST/PATCH uraian tugas | `Uraian tugas berhasil ditambahkan.` / `…berhasil diperbarui.` |
| POST/PATCH detil tugas | `Detil tugas berhasil ditambahkan.` / `…berhasil diperbarui.` |
| DELETE tugas pokok / uraian / detil | `Tugas pokok berhasil dihapus.` (dst.) |
| POST anggota panel | `Anggota berhasil ditambahkan ke panel.` |
| DELETE anggota panel | `Anggota berhasil dikeluarkan dari panel.` |
| PATCH item DCS/WCP | `Item berhasil disimpan.` |
| POST sesi TI / OPM | `Analisis jabatan berhasil dibuat.` |
| POST responden (single) TI/OPM | `Responden berhasil ditambahkan.` |
| POST responden (bulk) — semua | *(panel ringkasan sudah ada; tambahkan toast)* `{n} responden berhasil ditambahkan.` |
| DELETE responden TI/DCS/WCP/OPM | `Responden berhasil dihapus.` |
| POST transisi sesi TI | `Sesi dilanjutkan ke {tahap}.` / `Sesi ditutup.` / `Analisis selesai.` |
| DELETE sesi TI/OPM | `Analisis jabatan berhasil dihapus.` |
| POST tutup/buka-ulang instrumen DCS/WCP | `Instrumen ditutup.` / `Instrumen dibuka ulang.` |
| PATCH instrumen DCS/WCP | `Instrumen berhasil disimpan.` |
| POST analisis DCS/WCP/OPM | `Analisis selesai.` |
| POST submit kuesioner (tahap1/3, dcs/wcp/opm) | `Jawaban berhasil dikirim.` |
| POST/PATCH penugasan TS | `Penugasan berhasil dibuat.` / `…diperbarui.` |
| PATCH toggle aktif TS | `Penugasan diaktifkan.` / `Penugasan dinonaktifkan.` |
| DELETE penugasan TS | `Penugasan berhasil dihapus.` |
| POST/PATCH log TS | `Log berhasil disimpan.` |
| POST/PATCH partisipan | `Partisipan berhasil ditambahkan.` / `…berhasil diperbarui.` |

> Panel sukses yang **sudah ada** (`assign-responden-banyak`, `ts-penugasan-bulk-form`, panel hijau
> submit kuesioner, `edit-partisipan-form`, `reset-katalog-panel`) **tetap dipertahankan** — toast
> ditambahkan berdampingan, tidak menggantikan. Panel-panel itu memuat detail (daftar `skipped`,
> hitungan) yang tidak muat di toast.

### Langkah 10 — Test

Lihat "Skenario uji".

## Kriteria penerimaan

- [ ] `sonner` terpasang; `<Toaster />` ada di `src/app/providers.tsx` di dalam `ThemeProvider`.
- [ ] `src/lib/notify.ts` mengekspor `notifySukses`, `notifyGagal`, `pesanGagal`.
- [ ] `grep -rn "alert(" src/app` → **nol hasil** (kecuali `role="alert"` dan `confirm(`).
- [ ] `grep -rn "toast" src/app` → **nol hasil** (komponen hanya memanggil helper `notify*`).
- [ ] Setiap call site mutasi memanggil `notifySukses(...)` pada jalur sukses **dan** `notifyGagal(err)`
      pada jalur gagal. Verifikasi: tiap berkas di "Inventaris call site" punya `notifySukses` dan
      `notifyGagal`.
- [ ] `anggota-form.tsx` PATCH koordinator memeriksa `error` dan melempar `toApiError` (bug 1 tutup).
- [ ] `review-form.tsx` memberi toast berisi jumlah keputusan tersimpan + jumlah yang dilewati (bug 2).
- [ ] `atur-koordinator.tsx` tidak lagi punya state `sukses`/gate `!berubah` untuk pesan sukses (bug 3).
- [ ] `opm-form.tsx` menyebut `{tersimpan} dari {total} task` bila ada task parsial yang dibuang (bug 4).
- [ ] `reset-katalog-panel.tsx` memakai variabel lokal, bukan state `emptied`, di dalam `catch` (bug 5).
- [ ] Error inline lama (`form-server-error` dkk.) **tidak dihapus** dari form panjang.

## Skenario uji

Vitest + Testing Library. Sonner perlu di-mock di test — tambahkan di `vitest.setup.ts`:

```ts
vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
  Toaster: () => null,
}));
```

Test baru — `src/test/notify.test.tsx`:

- `notifyGagal(new ApiError({code, message}, "req-123"))` → `toast.error` dipanggil dengan `message`
  dan `description` berisi `req-123`.
- `notifyGagal(new Error("boom"))` → `toast.error("boom")`, tanpa `description`.
- `notifyGagal("bukan error")` → `toast.error("Terjadi kesalahan.")`.
- Toast error memakai `duration: Infinity`.

Test regresi per bug (WAJIB — ini yang membuktikan bug tertutup):

| Berkas test | Skenario |
|---|---|
| `src/test/sme-panel-anggota-form.test.tsx` | PATCH koordinator merespons 403 → `toast.error` dipanggil; `router.refresh` **tidak** dipanggil. *(Sebelum perbaikan: refresh dipanggil, error senyap.)* |
| `src/test/review-form.test.tsx` (sudah ada, tambah case) | POST sukses dengan 2 task pending → `toast.success` dipanggil dengan teks yang memuat jumlah dikirim **dan** jumlah dilewati. |
| `src/test/atur-koordinator.test.tsx` | PATCH sukses sementara prop `koordinatorId` **belum** berubah → `toast.success` tetap dipanggil. *(Sebelum perbaikan: banner tersembunyi.)* |
| `src/test/opm-form.test.tsx` | Draft save dengan 1 dari 3 task terisi lengkap → pesan sukses memuat `1 dari 3`. |
| `src/test/reset-katalog-panel.test.tsx` | purge sukses + reseed gagal → pesan error memuat `"sudah dikosongkan"`. *(Sebelum perbaikan: pesan generik.)* |

Perintah: `make test` (lint + unit, di Docker) dan `npm run build`.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-web-app`
- [ ] `npm run build` sukses
- [ ] `CHANGELOG.md` diperbarui
- [ ] `CLAUDE.md` repo diperbarui — tambahkan bagian "Revisi Desain" untuk konvensi notifikasi
      (`src/lib/notify.ts` sebagai satu-satunya pintu toast; `alert()` dilarang)
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Volume perubahan besar** (49 berkas). Risiko utama bukan kerusakan logika — perubahannya aditif
  (menambah panggilan `notify*`) — melainkan **terlewat**: satu call site tanpa `notifySukses` akan
  lolos tanpa test menangkapnya. Kriteria penerimaan sengaja memakai `grep` sebagai jaring pengaman.
- **Bug 4 hanya diperbaiki notifikasinya, bukan perilakunya.** `PUT` OPM tetap menghapus task parsial
  di server. Ini keputusan sadar — mengubah perilakunya menyentuh kontrak backend.
- **Toast bertahan lintas navigasi App Router** — `notifySukses` sebelum `router.push` aman dan sudah
  jadi pola yang diasumsikan Langkah 9. Bila ternyata tidak (misal karena remount `Providers`),
  pindahkan pemanggilannya ke halaman tujuan lewat query param — **konfirmasi ke user dulu** bila
  sampai perlu.
- Bug "skip tersembunyi" pada `dcs/assign-responden.tsx` & `wcp/assign-responden.tsx` **bukan** bagian
  item ini — lihat item **018** (backend) dan **019** (web-app).
