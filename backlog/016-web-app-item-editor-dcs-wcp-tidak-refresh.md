# Backlog 016 — Web app: editor item DCS & WCP tidak mereload data setelah simpan

> **Repo:** `anjab-abk-web-app`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `frontend-development-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Tombol **"Simpan"** di editor item kuesioner DCS (`/master-data/dcs/{kode}`) dan WCP
(`/master-data/wcp/{kode}`) berhasil mem-`PATCH` item ke backend, tapi **tidak pernah mereload data
server**. Keduanya hanya menambal salinan lokal di `useState` — satu-satunya komponen mutasi di
seluruh web app yang tidak memanggil `router.refresh()`.

Akibatnya perubahan **`urutan` tidak pernah terlihat**: backend mengurutkan item berdasarkan kolom
itu, tapi tabel di layar tidak di-render ulang, sehingga baris menampilkan nomor urut yang baru
**di posisi lamanya**. Tabel tampak tidak terurut sampai user menekan F5 manual.

Gejala ini menipu karena `pernyataan` dan `arah`/`reverse_type` *terlihat* ter-update — respons
server dimasukkan ke state lokal — jadi sekilas tombolnya seolah bekerja.

## Keputusan yang sudah dikunci

1. **Buang cermin state lokal (`rows`), jangan tambal.** Perbaikannya BUKAN sekadar menambahkan
   `router.refresh()` di samping `setRows(...)`. State `rows` yang di-seed dari props sekali saja
   adalah sumber masalahnya (bisa terus melenceng dari server). Tabel harus dirender **langsung dari
   prop `items`**, dan `router.refresh()` yang memasok datanya. Ini menyamakan komponen ini dengan
   46 tempat lain di repo yang sudah memakai pola Server Component + `router.refresh()`.
2. **Jangan sort di klien.** Urutan tabel tetap milik backend (`.order_by(...urutan)`). Jangan
   menambahkan `sorted()`/`.sort()` di komponen sebagai jalan pintas — itu hanya menyembunyikan
   fakta bahwa data tidak di-reload.
3. **DCS dan WCP diperlakukan identik.** Kedua berkas adalah komponen kembar; perubahannya harus
   simetris. Perbedaan hanya pada nama tipe (`DcsItemRead`/`WcpItemRead`), field enum
   (`arah: DcsArahItem` vs `reverse_type: WcpReverseType`), dan path endpoint.
4. **Jangan bergantung pada `staleTimes`.** `next.config.ts` menyetel
   `staleTimes: { dynamic: 0, static: 0 }` (Router Cache mati). Itu yang membuat tombol lain yang
   hanya `router.push()` tetap dapat data segar. Perbaikan di sini harus eksplisit lewat
   `router.refresh()`, tidak menyandarkan kebenaran pada setelan itu.

## Kondisi sekarang (verified)

| Fakta | Lokasi | ✓ |
|---|---|---|
| `rows` di-seed dari prop `items` sekali, lalu jadi sumber render tabel | `src/app/(auth)/master-data/dcs/[kode]/dcs-item-editor.tsx:19` | ✓ |
| `applyUpdate()` hanya `setRows(...)` + `setEditingId(null)` — tanpa `router.refresh()` | `dcs-item-editor.tsx:22-25` | ✓ |
| `PATCH /api/v1/dcs/sub-skala/items/{item_id}` body `{pernyataan, arah, urutan}` | `dcs-item-editor.tsx:107-110` | ✓ |
| Tombol "Simpan" memanggil `save()` | `dcs-item-editor.tsx:169` | ✓ |
| Komponen kembar WCP: `rows` state di baris 21, `applyUpdate` 25, `PATCH /api/v1/wcp/dimensi/items/{item_id}` body `{pernyataan, reverse_type, urutan}` di 108-110 | `src/app/(auth)/master-data/wcp/[kode]/wcp-item-editor.tsx` | ✓ |
| Tidak ada `useRouter`/`router.refresh` sama sekali di kedua berkas | `grep` kedua file | ✓ |
| Induk merender `<DcsItemEditor items={subSkala.items} accessToken={...} />` (Server Component) | `src/app/(auth)/master-data/dcs/[kode]/page.tsx:53` | ✓ |
| Backend mengurutkan item by `urutan` | `anjab-abk-backend/src/anjab_abk_backend/wcp/services/dimensi_sql.py:68` (+ padanan DCS) | ✓ |
| Router Cache dimatikan → `router.refresh()` benar-benar re-fetch RSC | `next.config.ts` (`staleTimes: {dynamic: 0, static: 0}`) | ✓ |
| Belum ada test untuk kedua editor | `src/test/` — tidak ada `*item-editor*` | ✓ |
| Tidak ada Server Action & tidak ada `fetch()` mentah di client component — satu-satunya gaya mutasi adalah klien `openapi-fetch` | sweep `grep "use server"` / `fetch(` | ✓ |

**Agen pelaksana WAJIB membaca ulang berkasnya sebelum mengedit — nomor baris bisa bergeser.**

## Langkah eksekusi

### Langkah 1 — `dcs-item-editor.tsx`: hapus state `rows`, render dari prop, refresh setelah simpan

Di komponen induk `DcsItemEditor`:

- Hapus `const [rows, setRows] = useState<DcsItemRead[]>(items);`
- Tambahkan `const router = useRouter();` (impor `useRouter` dari `next/navigation`).
- Ganti body `applyUpdate` — tidak lagi menerima `updated`, cukup tutup baris edit lalu reload:

```tsx
function handleSaved() {
  setEditingId(null);
  router.refresh();
}
```

- Ganti `rows.map(...)` menjadi `items.map(...)` di JSX.
- Prop `onSaved` di `RowProps` berubah tipe dari `(updated: DcsItemRead) => void` menjadi
  `() => void`; di `DcsItemEditRow.save()`, panggilan `onSaved(data)` menjadi `onSaved()`.
- `data` dari respons PATCH tidak lagi dipakai untuk merender, tapi **guard `if (apiError || !data)
  throw toApiError(...)` tetap dipertahankan** — itu yang mendeteksi kegagalan. Kalau `tsc` mengeluh
  `data` unused, biarkan tetap didestructure (dipakai di guard), bukan dihapus.
- `setSaving(false)` saat sukses tetap tidak perlu (komponen baris di-unmount oleh `setEditingId(null)`),
  konsisten dengan kode sekarang.

### Langkah 2 — `wcp-item-editor.tsx`: perubahan simetris

Terapkan persis Langkah 1 pada komponen WCP. Bedanya hanya `WcpItemRead`, field
`reverse_type`, dan endpoint `/api/v1/wcp/dimensi/items/{item_id}`. Jangan menyimpang dari bentuk
DCS — keduanya harus tetap kembar agar mudah dirawat.

### Langkah 3 — `hapus-penugasan.tsx`: seragamkan (opsional, kosmetik)

`src/app/(auth)/time-study/[penugasan_id]/hapus-penugasan.tsx:36` melakukan `DELETE` lalu
`router.push("/time-study")` **tanpa** `router.refresh()`. Ini **bukan bug** — Router Cache mati
(`staleTimes: 0`), jadi `push()` tetap mengambil data segar. Tapi tiga tombol hapus lain di Master
Data (`tugas-pokok`, `uraian-tugas`, `detil-tugas`) memakai `push()` + `refresh()`.

Tambahkan `router.refresh();` setelah `router.push("/time-study");` agar seragam dan tidak
menyandarkan kebenaran pada setelan `staleTimes` secara diam-diam (lihat Keputusan #4).

### Langkah 4 — test

Buat `src/test/dcs-item-editor.test.tsx` dan `src/test/wcp-item-editor.test.tsx`. Ikuti pola mock
yang sudah dipakai `src/test/atur-koordinator.test.tsx`:

```tsx
const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh }) }));

const patch = vi.fn();
vi.mock("@/lib/api/client", () => ({ withServerAuth: () => ({ PATCH: patch }) }));
```

`patch` harus mengembalikan bentuk yang dipakai komponen:
`{ data: <item>, error: undefined, response: { headers: { get: () => "req_1" } } }`.

### Langkah 5 — dokumentasi

- `CHANGELOG.md` web-app: entri `Fixed`.
- `CLAUDE.md` web-app: tambahkan entri di bagian **Revisi Desain** bertanggal, isinya keputusan
  "editor item DCS/WCP: cermin `useState` dibuang, data dipasok Server Component + `router.refresh()`" —
  supaya pola cermin-state ini tidak diperkenalkan lagi di komponen baru.
- `docs-usage/`: **tidak perlu diubah** — tidak ada perubahan alur/layar yang terlihat pengguna,
  hanya perilaku refresh yang jadi benar.

## Kriteria penerimaan

- [ ] Tidak ada lagi `useState` yang mencerminkan `items` di kedua editor; tabel dirender langsung dari prop `items`.
- [ ] Klik "Simpan" pada item DCS/WCP memanggil `router.refresh()` tepat sekali setelah PATCH sukses.
- [ ] Klik "Simpan" yang **gagal** (API error) **tidak** memanggil `router.refresh()`, baris edit tetap terbuka, dan pesan error tampil (`role="alert"`).
- [ ] Mengubah `urutan` sebuah item lalu menyimpan membuat baris berpindah posisi sesuai urutan baru tanpa reload manual (verifikasi di app; lihat "Skenario uji").
- [ ] `hapus-penugasan.tsx` memanggil `router.refresh()` setelah `router.push()` (Langkah 3).
- [ ] Tidak ada komponen mutasi tersisa di `src/app/` yang memanggil `POST`/`PATCH`/`DELETE` tanpa `router.refresh()` atau `router.push()`.

## Skenario uji

`src/test/dcs-item-editor.test.tsx` dan `src/test/wcp-item-editor.test.tsx` (masing-masing):

1. **Simpan sukses → refresh dipanggil.** Render dengan 2 item, klik "Ubah" pada item kedua, ubah
   `pernyataan`, klik "Simpan" → `patch` dipanggil sekali dengan `params.path.item_id` yang benar dan
   body berisi field yang diedit; `refresh` dipanggil **tepat 1×**; baris edit tertutup (textarea hilang).
2. **Simpan gagal → refresh TIDAK dipanggil.** `patch` mengembalikan `{ data: undefined, error: {...} }`
   → `refresh` **tidak** dipanggil, textarea masih tampak, pesan error muncul (`role="alert"`).
3. **Tabel mengikuti prop, bukan state lokal.** Render dengan `items` awal, lalu `rerender` dengan
   `items` yang urutannya sudah berubah (simulasi hasil `router.refresh()`) → urutan baris di DOM
   ikut berubah. Test inilah yang mengunci regresi: dengan kode lama (cermin `useState`) test ini gagal.
4. **Batal tidak memanggil apa pun.** Klik "Ubah" lalu "Batal" → `patch` dan `refresh` tidak dipanggil.

Perintah: `make test` (lint + typecheck + unit, di Docker) dari `anjab-abk-web-app/`.

Verifikasi manual (tidak wajib, tapi ini gejala aslinya): di `/master-data/dcs/{kode}`, ubah `urutan`
item nomor 5 menjadi 1 → baris harus langsung pindah ke atas tanpa F5.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-web-app`
- [ ] `npm run build` sukses
- [ ] `CHANGELOG.md` diperbarui
- [ ] `CLAUDE.md` web-app diperbarui (entri Revisi Desain — larangan pola cermin-state)
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Rendah.** Perubahan terbatas pada 3 berkas komponen + 2 berkas test baru. Tidak menyentuh
  backend, `schema.ts`, maupun kontrak API — `openapi.json` tidak berubah.
- **`urutan` duplikat tidak ditangani di item ini.** Backend (sejauh yang dicek) hanya menyetel nilai
  `urutan` yang dikirim, tidak menggeser item lain. Jadi dua item bisa berakhir dengan `urutan` sama,
  dan setelah perbaikan ini urutannya jadi tak-deterministik antar-refresh. Itu **cacat backend yang
  terpisah**, di luar cakupan item ini — sebelumnya tersembunyi justru karena UI tidak pernah reload.
  Kalau saat pengujian gejala ini muncul, **jangan tambal di frontend**; catat sebagai item backlog
  backend baru dan konfirmasi ke user.
- Setelah `rows` dibuang, `useState` di komponen induk tinggal `editingId` — pastikan impor `useState`
  masih terpakai (jangan sampai lint `no-unused-vars` menyala).
