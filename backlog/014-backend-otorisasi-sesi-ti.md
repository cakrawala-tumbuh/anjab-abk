# Backlog 014 — Backend: tutup lubang otorisasi endpoint sesi/hasil/tahap2 Task Inventory

> **Repo:** `anjab-abk-backend`
> **Status:** Menunggu (blocked by 013)
> **Blocked by:** 013
> **Skill yang dipakai:** `backend-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Seluruh otorisasi Task Inventory di level **sesi** saat ini dikerjakan di frontend, dan backend tidak
menegakkan apa pun. Pemeriksaannya kosmetik: halaman Next.js menampilkan 404 yang rapi
(`anjab-abk-web-app/src/app/(auth)/task-inventory/tahap2/[sesi_id]/page.tsx:64`), sementara panggilan
langsung ke backend mengembalikan datanya.

Dua kelas lubang:

**(a) Tanpa autentikasi sama sekali.** Tidak ada middleware auth global — `main.py` dan
`api/router.py` tidak punya `dependencies=` maupun `add_middleware` untuk auth (✓ diverifikasi).
Endpoint yang tidak menyebut `get_current_principal` secara eksplisit benar-benar terbuka tanpa token:
daftar sesi, detail sesi, review Tahap 2, task-terpilih, dan hasil analisis bisa ditarik siapa pun yang
bisa menjangkau backend.

**(b) Token saja, tanpa cek peran.** `_WRITE_GUARDS = [get_current_principal, rate_limit]`
(`taskinv_sesi.py:39`) hanya memastikan pemanggil punya JWT sah — partisipan mana pun lolos. Akibatnya
**partisipan biasa bisa menjalankan state machine sesi milik siapa pun**: memulai Tahap 2, membekukan
himpunan task di Tahap 3 (`freeze_task_terpilih` — **tidak bisa dibatalkan**), menutup sesi, menjalankan
analisis, membuat sesi, dan mem-`PATCH` sesi. Ini bukan sekadar kebocoran baca, tapi perusakan data
yang sah secara teknis. Hanya `DELETE /sesi/{id}` yang benar-benar `require_admin`.

## Keputusan yang sudah dikunci

1. **Dua lapis guard, bukan satu.** Menjadikan semuanya `require_admin` akan **mematikan alur pengisian
   partisipan** — halaman Tahap 1/2/3 memang memanggil endpoint sesi-level (lihat tabel di bawah).
2. **Lapis 1 — admin murni** (`dependencies=[Depends(require_admin)]`, pola persis
   `taskinv_responden.py:46`):
   `GET /sesi`, `POST /sesi/search`, `POST /sesi` (create), `PATCH /sesi/{id}`,
   `POST /sesi/{id}/mulai-tahap1`, `mulai-tahap2`, `mulai-tahap3`, `POST /sesi/{id}/tutup`,
   `POST /sesi/{id}/analisis`, `GET /sesi/{id}/hasil`.
3. **Lapis 2 — admin ATAU peserta sesi itu**, lewat **helper guard baru**
   `authorize_sesi_access()` di `dependencies.py`, sejajar `authorize_responden_access()` (`:343`):
   `GET /sesi/{id}`, `GET /sesi/{id}/tahap2`, `GET /sesi/{id}/task-terpilih`.
   Lolos bila: principal admin, **atau** partisipannya `== sesi.koordinator_id`, **atau** ia punya baris
   `TiRespondenModel` di sesi itu.
4. **`POST /sesi/{id}/tahap2` tidak disentuh** — sudah benar (cek koordinator di
   `taskinv_tahap2.py:94-100`). Hanya `GET`-nya yang bocor.
5. **Semua penolakan memakai `ForbiddenError`** (403) dari `errors.py`, bukan 404. Jangan `raise
   HTTPException` mentah (konvensi repo).
6. **Tidak ada perubahan skema/model/migrasi.** Murni pemasangan guard.
7. **Web app tidak perlu berubah** untuk alur yang sah — gating UI yang ada sudah sejalan dengan guard
   baru. Satu pengecualian yang harus ditangani: lihat Langkah 3.

## Kondisi sekarang (verified)

Guard aktual per endpoint TI:

| Endpoint | Lokasi | Guard sekarang | Target |
|---|---|---|---|
| `GET /task-inventory/sesi` | `api/v1/taskinv_sesi.py:46` | **tidak ada sama sekali** | admin |
| `POST /sesi/search` | `taskinv_sesi.py:112` | **tidak ada sama sekali** | admin |
| `GET /sesi/{id}` | `taskinv_sesi.py:129` | **tidak ada sama sekali** | admin / peserta sesi |
| `GET /sesi/{id}/tahap2` | `api/v1/taskinv_tahap2.py:38` | **tidak ada sama sekali** | admin / peserta sesi |
| `GET /sesi/{id}/task-terpilih` | `api/v1/taskinv_hasil.py:47` | **tidak ada sama sekali** | admin / peserta sesi |
| `GET /sesi/{id}/hasil` | `taskinv_hasil.py:106` | **tidak ada sama sekali** | admin |
| `POST /sesi` (create) | `taskinv_sesi.py:60` | token saja (`_WRITE_GUARDS`) | admin |
| `PATCH /sesi/{id}` | `taskinv_sesi.py:143` | token saja | admin |
| `POST /sesi/{id}/mulai-tahap1` | `taskinv_sesi.py:198` | token saja | admin |
| `POST /sesi/{id}/mulai-tahap2` | `taskinv_sesi.py:213` | token saja | admin |
| `POST /sesi/{id}/mulai-tahap3` | `taskinv_sesi.py:255` | token saja | admin |
| `POST /sesi/{id}/tutup` | `taskinv_sesi.py:311` | token saja | admin |
| `POST /sesi/{id}/analisis` | `taskinv_hasil.py:70` | token saja | admin |
| `DELETE /sesi/{id}` | `taskinv_sesi.py:159` (`require_admin` di `:179`) | **sudah benar** | — |
| `POST /sesi/{id}/tahap2` | `taskinv_tahap2.py:68` (cek koordinator `:94-100`) | **sudah benar** | — |
| `GET /sesi/{id}/responden` | `api/v1/taskinv_responden.py:46` | `require_admin` | lihat Langkah 3 |

Fakta pendukung:

| Fakta | Lokasi | ✓ |
|---|---|---|
| Tidak ada middleware auth global / `dependencies=` di router | `main.py`, `api/router.py` (grep bersih) | ✓ |
| `_WRITE_GUARDS = [Depends(get_current_principal), Depends(rate_limit)]` — token saja, tanpa peran | `taskinv_sesi.py:39` | ✓ |
| `require_admin` — guard yang sudah ada | `dependencies.py:334` | ✓ |
| `authorize_responden_access` — pola helper object-level yang harus ditiru | `dependencies.py:343` | ✓ |
| Endpoint responden-level (seleksi/detail/get responden) **sudah benar** — semua memanggil `authorize_responden_access` | `taskinv_seleksi.py:68,112,141`, `taskinv_detail.py:66,110,139`, `taskinv_responden.py:182` | ✓ |
| `mulai-tahap3` memanggil `freeze_task_terpilih()` — **tidak reversibel** | `taskinv_sesi.py:308` | ✓ |

Halaman web app yang memanggil endpoint sesi-level **sebagai partisipan** (inilah alasan lapis 2 ada):

| Halaman | Pemanggilan | Aktor |
|---|---|---|
| `task-inventory/tahap1/[responden_id]/page.tsx:24` | `GET /sesi/{sesi_id}` | anggota panel | 
| `task-inventory/tahap3/[responden_id]/page.tsx:29` | `GET /sesi/{sesi_id}` | anggota panel |
| `task-inventory/tahap3/[responden_id]/page.tsx:37` | `GET /sesi/{sesi_id}/task-terpilih` | anggota panel |
| `task-inventory/tahap2/[sesi_id]/page.tsx:22,30` | `GET /sesi/{sesi_id}`, `GET /sesi/{sesi_id}/tahap2` | koordinator **& anggota** (`:64` mengizinkan `isAnggota`) |
| `task-inventory/tahap2/[sesi_id]/page.tsx:37` | `GET /sesi/{sesi_id}/responden` | koordinator — **lihat Langkah 3** |

Halaman yang memanggil endpoint sesi-level sebagai **admin** (aman dijadikan admin-only):
`task-inventory/page.tsx:13` (list), `task-inventory/[sesi_id]/page.tsx:64,88,94,103` (detail, task-terpilih,
hasil, review), `task-inventory/buat/ti-sesi-form.tsx:73` (create), `[sesi_id]/transisi-sesi.tsx` (semua
transisi), `opm/buat/page.tsx:16` (meminjam `GET /task-inventory/sesi`).
`POST /sesi/search` **tidak dipanggil web app sama sekali** (✓ grep).

Agen pelaksana **wajib membaca ulang** file-file di atas sebelum mengedit — nomor baris bisa bergeser.

## Langkah eksekusi

### Langkah 1 — Helper guard baru `authorize_sesi_access()`

`src/anjab_abk_backend/dependencies.py`, tepat di bawah `authorize_responden_access` (`:343`).
Ikuti gaya dan docstring helper itu.

```python
def authorize_sesi_access(
    principal: Principal,
    sesi: TiSesiRead,
    par_service: PartisipanService,
    rsp_service: TiRespondenService,
) -> None:
    """Guard otorisasi object-level sesi TI: admin ATAU peserta sesi ini.

    Peserta = koordinator sesi, atau partisipan yang terdaftar sebagai responden di sesi
    ini. Dipakai di endpoint baca sesi/tahap2/task-terpilih agar partisipan tidak dapat
    membaca sesi jabatan lain lewat penebakan ID (BOLA/IDOR).
    """
    if "admin" in principal.groups:
        return
    par = par_service.get_by_subject(principal.subject)
    if par is None:
        raise ForbiddenError("Akses ditolak: Anda bukan peserta sesi ini.")
    if par.id == sesi.koordinator_id:
        return
    if any(r.sesi_id == sesi.id for r in rsp_service.list_by_partisipan(par.id)):
        return
    raise ForbiddenError("Akses ditolak: Anda bukan peserta sesi ini.")
```

Catatan: `list_by_partisipan` sudah ada (`taskinv/services/responden_sql.py:139`) dan setelah item 013
menjadi predikat yang bermakna. Bila mau lebih hemat query, boleh tambahkan method
`is_responden(sesi_id, partisipan_id) -> bool` ke `TiRespondenService` — **opsional**, jangan
memperluas item ini kalau tidak perlu.

### Langkah 2 — Pasang guard

**Lapis 1 (admin murni)** — tambahkan `Depends(require_admin)` ke `dependencies=` tiap endpoint.
Untuk yang sudah memakai `_WRITE_GUARDS`, ganti menjadi konstanta baru di `taskinv_sesi.py`:

```python
_ADMIN_GUARDS = [Depends(require_admin), Depends(rate_limit)]
```

(pola ini sudah ada persis di `taskinv_responden.py:31`). Terapkan ke: `taskinv_sesi.py` — list (`:46`),
search (`:112`), create (`:60`), patch (`:143`), mulai-tahap1 (`:198`), mulai-tahap2 (`:213`),
mulai-tahap3 (`:255`), tutup (`:311`); `taskinv_hasil.py` — analisis (`:70`), hasil (`:106`).
Tambahkan `403` ke dict `responses` tiap endpoint (`_FORBIDDEN` sudah didefinisikan di
`taskinv_sesi.py:43`).

**Lapis 2 (admin / peserta)** — di `GET /sesi/{id}` (`taskinv_sesi.py:129`), `GET /sesi/{id}/tahap2`
(`taskinv_tahap2.py:38`), dan `GET /sesi/{id}/task-terpilih` (`taskinv_hasil.py:47`): tambahkan
parameter `principal: Annotated[Principal, Depends(get_current_principal)]` + dependency
`par_service`/`rsp_service`, lalu panggil `authorize_sesi_access(principal, sesi, par_service,
rsp_service)` **segera setelah** `sesi = sesi_service.get(sesi_id)` dan **sebelum** kerja apa pun
(`taskinv_tahap2.py` dan `taskinv_hasil.py` sudah punya `rsp_service` di tangan). Tambahkan `401` &
`403` ke `responses`.

### Langkah 3 — Rekonsiliasi `GET /sesi/{id}/responden` (inkonsistensi existing)

`taskinv_responden.py:46` memakai `require_admin`, tetapi halaman koordinator
`tahap2/[sesi_id]/page.tsx:37` memanggilnya. Artinya **koordinator non-admin sudah kena 403 di sana
hari ini** — halaman itu kemungkinan degradasi diam-diam dan belum dilaporkan siapa pun.

Sebelum mengubah apa pun: **baca halaman itu**, pastikan bagaimana ia menangani error (apakah
`notFound()`, apakah jumlah responden jadi 0, atau apakah ada guard `admin` yang membuatnya tidak
pernah dipanggil oleh koordinator). Lalu pilih:

- **(a)** Relaksasi `list_responden` menjadi `authorize_sesi_access` (admin/peserta) — konsisten dengan
  lapis 2, dan halaman koordinator jadi benar. **Ini pilihan yang disarankan** bila terbukti halaman itu
  memang butuh datanya.
- **(b)** Biarkan `require_admin` dan ubah halaman agar tidak memanggilnya (butuh item turunan di
  `anjab-abk-web-app`).

**Laporkan temuan & pilihan ke user sebelum eksekusi** — ini satu-satunya titik di item ini yang belum
terkunci keputusannya.

### Langkah 4 — Test

`tests/test_taskinv.py`. Repo sudah punya pola test 401/403 (lihat test seputar
`authorize_responden_access`). Tambahkan, minimal:

1. `test_sesi_list_tanpa_token_401` + `test_sesi_list_partisipan_403` — dan ulangi untuk search, create,
   patch, tutup, analisis, hasil (boleh `pytest.mark.parametrize` atas (method, path)).
2. `test_mulai_tahap3_partisipan_403` — **paling penting**: partisipan biasa tidak boleh bisa membekukan
   task. Verifikasi juga sesi **tidak** berpindah status setelah panggilan ditolak.
3. `test_get_sesi_peserta_boleh` / `test_get_sesi_bukan_peserta_403` — anggota panel jabatan X boleh baca
   sesi X, tidak boleh baca sesi Y.
4. `test_get_tahap2_koordinator_boleh` — koordinator (non-admin) boleh `GET` review.
5. `test_get_tahap2_bukan_peserta_403` + `test_get_tahap2_tanpa_token_401`.
6. `test_get_task_terpilih_peserta_boleh` — anggota panel yang mengisi Tahap 3 tidak boleh ikut terblokir
   (regresi paling mungkin dari item ini).
7. `test_admin_semua_endpoint_boleh` — admin tetap lolos di seluruh endpoint di atas.

## Kriteria penerimaan

- [ ] Tidak ada satu pun endpoint TI yang dapat diakses **tanpa token** (verifikasi dengan menyapu
      seluruh route TI di `openapi.json` dan memastikan tiap operasi punya guard).
- [ ] Partisipan non-admin menerima **403** pada: create/patch/delete sesi, keempat transisi
      (`mulai-tahap1|2|3`, `tutup`), `analisis`, `hasil`, `list`, `search`.
- [ ] Partisipan non-admin **tetap bisa** menyelesaikan alur pengisian: Tahap 1 (baca sesi + seleksi),
      Tahap 3 (baca sesi + task-terpilih + detail), dan koordinator tetap bisa `GET`+`POST` review Tahap 2.
- [ ] Partisipan tidak bisa membaca sesi/tahap2/task-terpilih milik jabatan yang panelnya bukan miliknya
      (403, bukan 200).
- [ ] Admin tidak terhalang di endpoint mana pun.
- [ ] Semua penolakan lewat `ForbiddenError`/`UnauthorizedError` (envelope `errors.py`), bukan
      `HTTPException` mentah.
- [ ] Tidak ada berkas migrasi baru; `models.py` tidak berubah.

## Skenario uji

Test di `tests/test_taskinv.py` (lihat Langkah 4). Gate lengkap:

```bash
cd anjab-abk-backend && make test
```

Setelah hijau, jalankan `make export-openapi` — `openapi.json` **akan** berubah (blok `security` +
respons 401/403 baru per operasi). Ini diharapkan; commit hasil generate-nya, jangan edit tangan.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-backend`
- [ ] `openapi.json` di-regenerate lewat `make export-openapi`
- [ ] `CHANGELOG.md` diperbarui
- [ ] `CLAUDE.md` repo diperbarui — entri Revisi Desain berisi matriks guard TI (siapa boleh apa)
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Blocked by 013 — jangan dikerjakan lebih dulu.** Selama `/kuesioner/saya` masih meng-auto-enroll
  semua partisipan ke semua sesi aktif, "punya baris responden di sesi ini" bernilai benar untuk semua
  orang, sehingga guard lapis 2 **tidak menyaring apa pun** dan test-nya akan lolos secara palsu.
- **Risiko regresi utama: memblokir partisipan yang sah.** Titik paling rawan adalah
  `GET /sesi/{id}/task-terpilih` (dipakai halaman Tahap 3 partisipan, `tahap3/[responden_id]/page.tsx:37`)
  dan `GET /sesi/{id}` (dipakai Tahap 1 & 3). Kriteria penerimaan sudah memuat test khusus untuk ini —
  jangan hapus.
- **`openapi.json` berubah** → MCP (`anjab-abk-mcp`) dan web app membaca skema ini. Perubahan hanya
  berupa penambahan respons 401/403, **bukan** perubahan bentuk request/response, jadi seharusnya tidak
  ada item turunan. Verifikasi dengan membaca diff `openapi.json`; bila ternyata ada perubahan bentuk,
  hentikan dan buat item turunan.
- **Deployment YPII sedang berjalan dengan lubang ini terbuka.** Perlakukan sebagai perbaikan
  keamanan — setelah rilis, sebaiknya user melakukan redeploy, bukan menunggu siklus rilis berikutnya.
- **OPM belum diaudit.** `opm/buat/page.tsx:16` bahkan meminjam `GET /api/v1/task-inventory/sesi` yang
  terbuka itu — setelah item ini, halaman itu **hanya akan bekerja untuk admin** (dan memang semestinya
  begitu, karena membuat sesi OPM adalah pekerjaan admin — tapi konfirmasi saat eksekusi). Enrollment OPM
  sendiri sudah aman (`opm_kuesioner.py:52` memakai `list_by_partisipan`), tetapi guard sesi/hasil-nya
  **belum diperiksa sama sekali**. Buat item terpisah untuk OPM; jangan melebarkan item ini.
