# Backlog 015 — Backend: tutup lubang otorisasi endpoint sesi/hasil OPM

> **Repo:** `anjab-abk-backend`
> **Status:** Siap dieksekusi (disarankan menyusul 014)
> **Blocked by:** —
> **Skill yang dipakai:** `backend-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Audit OPM (2026-07-13, lanjutan audit TI yang melahirkan item 013–014) menemukan **lubang otorisasi
sesi-level yang sama persis dengan TI**: endpoint sesi OPM tidak dijaga, dan otorisasinya cuma ada di
frontend.

Kabar baiknya, OPM **jauh lebih sehat dari TI di dua sisi** — dan keduanya sudah diverifikasi, sehingga
item ini lebih sempit dari 014:

1. **Enrollment OPM sudah aman.** `GET /opm/kuesioner/saya` memakai `list_by_partisipan()`
   (`opm_kuesioner.py:52`) — tidak ada auto-enroll universal seperti bug TI di item 013. **Tidak ada
   padanan item 013 untuk OPM.**
2. **Lapisan responden OPM sudah dijaga benar**, bahkan lebih ketat dari TI: `list`/`create`/`bulk`/
   `delete` responden semuanya `require_admin`/`_ADMIN_GUARDS`, dan `get`/`jawaban` memakai
   `authorize_responden_access`.

Yang bocor **hanya level sesi & hasil**. Sama seperti TI, ada dua kelas: sebagian endpoint terbuka
**tanpa token sama sekali** (tidak ada middleware auth global — ✓ diverifikasi di item 014), sebagian
lagi bertoken tanpa cek peran sehingga **partisipan biasa bisa membuka/menutup sesi OPM milik siapa pun
dan menjalankan analisisnya**.

## Keputusan yang sudah dikunci

1. **Dua lapis guard**, sama seperti 014 — tapi lapis 2 di OPM **hanya menyentuh satu endpoint**
   (`GET /sesi/{id}/task`), karena hanya itu endpoint sesi-level yang dipanggil halaman partisipan.
2. **Lapis 1 — admin murni** (`_ADMIN_GUARDS = [Depends(require_admin), Depends(rate_limit)]`; pola
   sudah ada persis di `opm_responden.py:32`):
   `GET /opm/sesi`, `POST /opm/sesi/search`, `GET /opm/sesi/{id}`, `POST /opm/sesi` (create),
   `PATCH /opm/sesi/{id}`, `POST /sesi/{id}/buka`, `POST /sesi/{id}/tutup`,
   `POST /sesi/{id}/analisis`, `GET /sesi/{id}/hasil`.
3. **Lapis 2 — admin ATAU responden sesi ini**: `GET /sesi/{id}/task` saja.
4. **Guard OPM lebih sederhana dari TI: tidak ada koordinator.** `OpmSesiModel` tidak punya kolom
   `koordinator_id` (✓ `models.py:591-602`), dan tidak ada satu pun kemunculan kata "koordinator" di
   `src/anjab_abk_backend/opm/` (✓ grep bersih). Jadi predikatnya cukup: **admin, atau punya baris
   `OpmRespondenModel` di sesi itu.** Jangan menyalin cabang koordinator dari helper TI.
5. **Endpoint responden OPM tidak disentuh sama sekali** — semuanya sudah benar.
6. **`/opm/kuesioner/saya` tidak disentuh** — sudah assignment-based.
7. **Tidak ada perubahan skema/model/migrasi.** Murni pemasangan guard.
8. **Web app tidak perlu berubah.** Seluruh halaman admin OPM sudah memanggil
   `if (!isAdmin(session)) notFound()`, dan satu-satunya halaman partisipan hanya memakai endpoint yang
   tetap boleh diaksesnya (lihat tabel).

## Kondisi sekarang (verified)

Guard aktual per endpoint OPM:

| Endpoint | Lokasi | Guard sekarang | Target |
|---|---|---|---|
| `GET /opm/sesi` | `api/v1/opm_sesi.py:38` | **tidak ada sama sekali** | admin |
| `POST /opm/sesi/search` | `opm_sesi.py:108` | **tidak ada sama sekali** | admin |
| `GET /opm/sesi/{id}` | `opm_sesi.py:125` | **tidak ada sama sekali** | admin |
| `GET /opm/sesi/{id}/task` | `opm_sesi.py:224` | **tidak ada sama sekali** | admin / responden sesi |
| `GET /opm/sesi/{id}/hasil` | `api/v1/opm_hasil.py:79` | **tidak ada sama sekali** | admin |
| `POST /opm/sesi` (create) | `opm_sesi.py:52` | token saja (`_WRITE_GUARDS`) | admin |
| `PATCH /opm/sesi/{id}` | `opm_sesi.py:139` | token saja | admin |
| `POST /sesi/{id}/buka` | `opm_sesi.py:194` | token saja | admin |
| `POST /sesi/{id}/tutup` | `opm_sesi.py:209` | token saja | admin |
| `POST /sesi/{id}/analisis` | `opm_hasil.py:32` | token saja | admin |
| `DELETE /opm/sesi/{id}` | `opm_sesi.py:155` (`require_admin` di `:175`) | **sudah benar** | — |
| `GET /sesi/{id}/responden` | `opm_responden.py:42` (`require_admin` `:47`) | **sudah benar** | — |
| `POST /sesi/{id}/responden` | `opm_responden.py:59` (`_ADMIN_GUARDS` `:65`) | **sudah benar** | — |
| `POST /sesi/{id}/responden/bulk` | `opm_responden.py:95` (`_ADMIN_GUARDS` `:101`) | **sudah benar** | — |
| `DELETE /responden/{id}` | `opm_responden.py:150` (`_ADMIN_GUARDS` `:155`) | **sudah benar** | — |
| `GET /responden/{id}` | `opm_responden.py:132` (`authorize_responden_access` `:146`) | **sudah benar** | — |
| `PUT/POST/GET /responden/{id}/jawaban*` | `opm_responden.py:193`, `:234`, `:263` | **sudah benar** | — |
| `GET /opm/kuesioner/saya` | `api/v1/opm_kuesioner.py:52` (`list_by_partisipan`) | **sudah benar** | — |

Fakta pendukung:

| Fakta | Lokasi | ✓ |
|---|---|---|
| `_WRITE_GUARDS = [Depends(get_current_principal), Depends(rate_limit)]` — token saja, tanpa peran | `opm_sesi.py:31`, `opm_hasil.py:26` | ✓ |
| `_ADMIN_GUARDS` — pola target yang **sudah ada di modul OPM sendiri** | `opm_responden.py:32` | ✓ |
| `OpmSesiModel` **tidak punya** `koordinator_id` | `models.py:591-602` | ✓ |
| Tidak ada konsep koordinator di seluruh modul OPM | grep `koordinator` di `src/anjab_abk_backend/opm/` → kosong | ✓ |
| Enrollment OPM assignment-based (tidak ada `ensure_for_partisipan`) | `opm_kuesioner.py:52` | ✓ |
| `list_by_partisipan` OPM — dipakai helper guard lapis 2 | `opm/services/responden_sql.py:61`, Protocol `opm/services/responden.py:32` | ✓ |

Halaman web app (`anjab-abk-web-app`):

| Halaman | Pemanggilan sesi-level | Aktor | ✓ |
|---|---|---|---|
| `opm/isi/[responden_id]/page.tsx:25` | `GET /opm/sesi/{sesi_id}/task` | **partisipan** (`:40` `if (!isPartisipan(session)) notFound()`) | ✓ |
| `opm/page.tsx:19` | `GET /opm/sesi` | admin (`:29`) | ✓ |
| `opm/[sesi_id]/page.tsx:50,51,52` | `GET /sesi/{id}`, `/task`, `/responden` | admin (`:79`) | ✓ |
| `opm/[sesi_id]/hasil/page.tsx:17,18` | `GET /sesi/{id}`, `/hasil` | admin (`:44`) | ✓ |
| `opm/buat/opm-sesi-form.tsx:72` | `POST /opm/sesi` | admin (`buat/page.tsx:36`) | ✓ |
| `opm/[sesi_id]/transisi-sesi.tsx:25,45,67` | `buka`/`tutup`, `analisis`, `DELETE` | admin (`[sesi_id]/page.tsx:79`) | ✓ |

Catatan penting: halaman partisipan `opm/isi/[responden_id]` **tidak** memanggil `GET /opm/sesi/{id}` —
ia hanya butuh `/task` (+ endpoint responden yang sudah dijaga). Karena itu `GET /opm/sesi/{id}` **aman
dijadikan admin-only**, berbeda dari TI (yang halaman Tahap 1/3-nya memang memanggilnya).
`POST /opm/sesi/search` **tidak dipanggil web app sama sekali** (✓ grep).

Agen pelaksana **wajib membaca ulang** file-file di atas sebelum mengedit — nomor baris bisa bergeser.

## Langkah eksekusi

### Langkah 1 — Helper guard `authorize_opm_sesi_access()`

`src/anjab_abk_backend/dependencies.py`, di dekat `authorize_responden_access` (`:343`) dan
`authorize_sesi_access` (dibuat di item 014).

```python
def authorize_opm_sesi_access(
    principal: Principal,
    sesi_id: str,
    par_service: PartisipanService,
    rsp_service: OpmRespondenService,
) -> None:
    """Guard otorisasi object-level sesi OPM: admin ATAU responden sesi ini.

    OPM tidak punya koordinator (beda dari Task Inventory), jadi peserta = partisipan
    yang terdaftar sebagai responden di sesi ini.
    """
    if "admin" in principal.groups:
        return
    par = par_service.get_by_subject(principal.subject)
    if par is None or not any(r.sesi_id == sesi_id for r in rsp_service.list_by_partisipan(par.id)):
        raise ForbiddenError("Akses ditolak: Anda bukan peserta sesi OPM ini.")
```

Bila item 014 sudah menambahkan method `is_responden(sesi_id, partisipan_id)` ke service TI, pakai pola
yang sama untuk OPM demi konsistensi. Bila tidak, `list_by_partisipan` sudah cukup — jangan melebarkan
lingkup.

### Langkah 2 — Pasang guard

**Lapis 1 (admin murni).** Di `opm_sesi.py`, `_ADMIN_GUARDS` belum ada — tambahkan (salin dari
`opm_responden.py:32`), lalu terapkan ke: list (`:38`), search (`:108`), get (`:125`), create (`:52`),
patch (`:139`), buka (`:194`), tutup (`:209`). Di `opm_hasil.py`: analisis (`:32`), hasil (`:79`).
Ganti `_WRITE_GUARDS` menjadi `_ADMIN_GUARDS` pada endpoint yang sudah memakainya; tambahkan
`dependencies=` pada endpoint yang tadinya kosong. Tambahkan respons `401` & `403` ke dict `responses`
tiap endpoint.

**Lapis 2.** Di `GET /sesi/{id}/task` (`opm_sesi.py:224`): tambahkan `principal`, `par_service`, dan
`rsp_service` sebagai dependency, lalu panggil `authorize_opm_sesi_access(...)` **sebelum** kerja apa
pun. Tambahkan `401` & `403` ke `responses`.

### Langkah 3 — Test

`tests/test_opm.py` (bila belum ada, ikuti struktur `tests/test_taskinv.py`). Minimal:

1. Parametrized `test_opm_sesi_*_tanpa_token_401` dan `*_partisipan_403` untuk: list, search, get,
   create, patch, buka, tutup, analisis, hasil.
2. `test_opm_buka_sesi_partisipan_403` — verifikasi sesi **tidak** berpindah status setelah ditolak.
3. `test_opm_task_responden_boleh` — responden sesi X bisa `GET /sesi/X/task` (**regresi paling
   mungkin**: ini satu-satunya endpoint sesi-level yang dipakai halaman pengisian partisipan).
4. `test_opm_task_bukan_responden_403` — partisipan yang bukan responden sesi X ditolak.
5. `test_opm_admin_semua_endpoint_boleh`.

## Kriteria penerimaan

- [ ] Tidak ada endpoint OPM yang dapat diakses **tanpa token**.
- [ ] Partisipan non-admin menerima **403** pada: list, search, get sesi, create, patch, buka, tutup,
      analisis, hasil.
- [ ] Partisipan yang **terdaftar sebagai responden** tetap bisa menyelesaikan pengisian OPM:
      `GET /sesi/{id}/task` + seluruh endpoint responden/jawaban.
- [ ] Partisipan tidak bisa membaca `/task` sesi yang bukan miliknya (403).
- [ ] Endpoint responden OPM dan `/opm/kuesioner/saya` **tidak berubah sama sekali**.
- [ ] Admin tidak terhalang di endpoint mana pun.
- [ ] Semua penolakan lewat envelope `errors.py` (`ForbiddenError`/`UnauthorizedError`).
- [ ] Tidak ada berkas migrasi baru; `models.py` tidak berubah.

## Skenario uji

```bash
cd anjab-abk-backend && make test
```

Lalu `make export-openapi` — `openapi.json` **akan** berubah (respons 401/403 baru per operasi).
Commit hasil generate-nya, jangan edit tangan.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-backend`
- [ ] `openapi.json` di-regenerate lewat `make export-openapi`
- [ ] `CHANGELOG.md` diperbarui
- [ ] `CLAUDE.md` repo diperbarui — lengkapi matriks guard dari item 014 dengan baris OPM
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Tidak diblokir oleh 013/014, tapi sebaiknya menyusul 014.** Berbeda dari TI, guard OPM tidak
  bergantung pada perbaikan enrollment (enrollment OPM sudah benar), jadi secara teknis item ini bisa
  jalan sendiri. Tetap disarankan menyusul 014 agar helper guard & konstanta `_ADMIN_GUARDS`-nya konsisten
  dan `openapi.json` cukup di-regenerate sekali.
- **Interaksi dengan item 014 — `opm/buat/page.tsx:16` meminjam `GET /api/v1/task-inventory/sesi`**
  (endpoint TI, bukan OPM) untuk memilih sesi TI sumber. Setelah item 014 menjadikan endpoint itu
  admin-only, halaman itu **tetap bekerja** karena sudah admin-gated (`buat/page.tsx:36`). Tidak ada
  tindakan yang diperlukan — dicatat di sini supaya tidak salah didiagnosis sebagai regresi.
- **Risiko regresi utama:** `GET /sesi/{id}/task`. Ini satu-satunya endpoint sesi-level di jalur
  pengisian partisipan; kalau salah dijadikan admin-only, halaman `opm/isi/[responden_id]` mati total.
  Kriteria penerimaan sudah memuat test khusus — jangan hapus.
- **Deployment YPII sedang berjalan dengan lubang ini terbuka**, sama seperti TI. Perlakukan sebagai
  perbaikan keamanan.
