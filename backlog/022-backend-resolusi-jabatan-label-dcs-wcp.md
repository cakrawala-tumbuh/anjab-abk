# Backlog 022 — Backend: resolusi `jabatan_label` DCS & WCP (bukan salinan ID mentah)

> **Repo:** `anjab-abk-backend`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `backend-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Ditemukan saat menjalankan SOP Persiapan+Pelaksanaan DCS end-to-end via Playwright (3 responden
uji coba di `https://anjab-abk.cantum-ypii.com`, 2026-07-14): kolom **"Jabatan"** di tabel Daftar
Responden halaman admin `/dcs` (dan `/wcp`), serta subtext header halaman
`/dcs/hasil-responden/{id}`, menampilkan **ID internal mentah** (mis. `jbt_4c034eef`) alih-alih
nama jabatan yang bisa dibaca (mis. "Guru Mapel SMP").

Ini sudah diketahui & sengaja ditunda sejak revisi `[2026-07-12]` `CLAUDE.md` (entri "DCS & WCP:
hapus entitas sesi..."): *"`jabatan_label` tetap kolom teks bebas (bukan FK) — nilainya sekadar
disalin dari `jabatan_utama_id`, bukan diresolusi ke nama jabatan (di luar lingkup revisi ini)."*
Item ini mengeksekusi penyelesaian yang saat itu sengaja ditunda.

## Keputusan yang sudah dikunci

- **Skema TIDAK berubah** — `jabatan_label` di `DcsRespondenModel`/`WcpRespondenModel`
  (`String(200)`, `nullable=False`) dan `DcsRespondenRead`/`WcpRespondenRead` TETAP kolom teks
  bebas (bukan FK), TIDAK ada migrasi Alembic. Hanya NILAI yang diisi saat create yang berubah.
- **Resolusi dilakukan sekali, saat responden dibuat di `create_banyak()`** — HANYA titik ini yang
  disentuh. Method `create()` (single-assign) di kedua file **TIDAK disentuh sama sekali** — sudah
  diverifikasi ia tidak dipanggil oleh endpoint apa pun untuk DCS/WCP (lihat "Kondisi sekarang" di
  bawah): satu-satunya endpoint POST (`POST /api/v1/dcs/responden` & `.../wcp/responden`) hanya
  memanggil `create_banyak()`. `create()` adalah kode Protocol yang tidak terpakai (peninggalan
  desain sebelum refactor `[2026-07-12]`) — **jangan dihapus** (di luar lingkup item ini), tapi
  juga jangan diberi resolusi jabatan karena tidak ada jalur yang mengujinya.
- **Keputusan arsitektur (WAJIB dibaca, ini bukan pilihan bebas eksekutor):** ada DUA pola berbeda
  yang sudah eksis di codebase untuk kasus serupa, dan keduanya **saling bertentangan**:
  - OPM (`opm/services/responden_sql.py`, method `assign_banyak`) melakukan query ORM cross-domain
    LANGSUNG: `self._s.get(JabatanModel, jabatan_id)`, fallback ke `""` bila `None` — TANPA lewat
    `JabatanService`, TANPA `NotFoundError` — ini melanggar aturan tertulis di `CLAUDE.md` repo ini
    sendiri: *"Akses data ke domain lain hanya via seam service `core` — tidak query lintas domain
    langsung."*
  - **Item ini memilih pola KEDUA (bukan meniru OPM)**: suntik `JabatanService` (Protocol yang
    sudah ada, `anjab/services/jabatan.py`, DI provider `get_jabatan_service()` sudah ada di
    `dependencies.py`) ke `SqlDcsRespondenService`/`SqlWcpRespondenService`, persis seperti
    `PartisipanService` yang SUDAH disuntik ke kelas yang sama. **Alasan:** kelas ini sudah
    memakai pola Protocol+DI untuk `PartisipanService` — menambah `JabatanService` dengan cara yang
    sama adalah nol perubahan pola baru, dapat `NotFoundError` terstruktur secara gratis untuk
    fallback, dan konsisten dengan konvensi seam Service yang dipakai di SELURUH domain lain
    (`anjab`, `abk`, `core`). Query mentah ala OPM adalah tech debt yang kebetulan sudah lolos
    merge, BUKAN preseden yang harus diikuti — **jangan tiru pola OPM di item ini.**
- **Fallback bila `JabatanService.get()` melempar `NotFoundError`**: `jabatan_label` diisi dengan
  `partisipan.jabatan_utama_id` mentah (ID) + `logger.warning(...)`. TIDAK boleh membuat
  `create_banyak()` gagal (bulk sudah idempoten/skip-on-conflict untuk hal lain — jangan tambah
  jalur gagal baru untuk kasus ini). Nilai fallback (ID, `String(40)`) selalu muat di kolom
  `String(200)`.
- **Data existing TIDAK dimigrasi otomatis** di item ini — baris `dcs_responden`/`wcp_responden`
  yang sudah ada (termasuk 3 baris uji coba dari sesi testing 2026-07-14 di produksi YPII) tetap
  apa adanya. Backfill butuh keputusan terpisah, TANYA user sebelum eksekusi UPDATE massal di DB
  produksi.

## Kondisi sekarang (verified 2026-07-14 — baca ulang file sebelum edit, baris bisa bergeser)

- ✓ `src/anjab_abk_backend/dcs/services/responden_sql.py`:
  - Import baris 15–31 — `NotFoundError` **sudah** di-import (baris 25, dipakai `_get_model`),
    tidak perlu ditambah. `JabatanService` **belum** di-import di file ini.
  - `__init__` baris 55–57:
    ```python
    def __init__(self, session: Session, partisipan_service: PartisipanService) -> None:
        self._s = session
        self._par = partisipan_service
    ```
  - `create_banyak()` baris 126–181, baris bug **persis di baris 165**:
    ```python
    partisipan = self._par.get(partisipan_id)
    rec = DcsRespondenModel(
        id=f"drsp_{uuid.uuid4().hex[:8]}",
        nama=partisipan.nama,
        jabatan_label=partisipan.jabatan_utama_id,
        partisipan_id=partisipan_id,
        sudah_submit=False,
    )
    self._s.add(rec)
    recs.append(rec)
    ```
  - `create()` baris 118–124 — menerima `jabatan_label: str` sudah jadi dari caller. **Terverifikasi
    TIDAK ADA caller sama sekali** untuk DCS/WCP (`api/v1/dcs_responden.py` hanya punya satu POST
    endpoint, memanggil `create_banyak()`; `DcsRespondenCreate` payload hanya berisi
    `partisipan_ids: list[str]`, tidak ada field `nama`/`jabatan_label` untuk dikirim manual). Jangan
    disentuh.
- ✓ `src/anjab_abk_backend/wcp/services/responden_sql.py` — STRUKTUR IDENTIK baris-per-baris
  dengan file DCS (`__init__` baris 55–57, `create_banyak()` baris 126–181, bug di baris 165 persis
  sama), hanya beda nama kelas/model (`WcpRespondenModel`, `WcpRespondenRead`) dan prefix ID
  (`wrsp_`).
- ✓ `src/anjab_abk_backend/dependencies.py`:
  - `get_dcs_responden_service()` baris 184–189:
    ```python
    def get_dcs_responden_service(
        session: SessionDep,
        partisipan_service: Annotated[PartisipanService, Depends(get_partisipan_service)],
    ) -> DcsRespondenService:
        """SEAM: implementasi `DcsRespondenService` berbasis PostgreSQL."""
        return SqlDcsRespondenService(session, partisipan_service)
    ```
  - `get_wcp_responden_service()` baris 158–163 (nama fungsi terverifikasi, struktur identik pola
    di atas — `SqlWcpRespondenService(session, partisipan_service)`).
  - `get_jabatan_service()` baris 135–137 (SUDAH ADA, tidak perlu dibuat):
    ```python
    def get_jabatan_service(session: SessionDep) -> JabatanService:
        """SEAM: implementasi `JabatanService` berbasis PostgreSQL."""
        return SqlJabatanService(session)
    ```
  - Import `JabatanService`/`SqlJabatanService` baris 22–23 (sudah ada, tidak perlu ditambah).
- ✓ `JabatanService.get(jabatan_id: str) -> JabatanRead` (`anjab/services/jabatan_sql.py`, method
  `_get_model` baris 73–77 dipakai `get()`) melempar `anjab_abk_backend.errors.NotFoundError`
  (import `from ...errors import ConflictError, NotFoundError`, baris 24) bila jabatan tidak
  ditemukan — persis exception yang sudah ter-import di `dcs/services/responden_sql.py` &
  `wcp/services/responden_sql.py`. `JabatanRead.nama: str` adalah field yang dipakai
  (`anjab/schemas/jabatan.py` baris 67).
- ✓ `DcsRespondenModel.jabatan_label`/`WcpRespondenModel.jabatan_label` (`models.py` baris 255 &
  321): `Mapped[str] = mapped_column(String(200), nullable=False)`.
- ✓ **Fakta penting untuk test**: fixture `partisipan_factory` (`tests/conftest.py` baris 148–175)
  secara default mengisi `jabatan_utama_id` dengan **ID ACAK yang tidak pernah ada di DB**
  (`f"jbt_{uuid.uuid4().hex[:8]}"`, baris 168) — dipakai oleh SELURUH test DCS/WCP responden yang
  ada saat ini (`par_a`/`par_b` di `test_dcs_responden.py` baris 43–50, dst.). Artinya jalur
  fallback (`NotFoundError`) adalah jalur DEFAULT yang dilewati hampir semua test existing, bukan
  edge case langka.
- ✓ Test existing yang menyentuh `jabatan_label`,
  `test_create_responden_derives_nama_dan_jabatan_label` (`test_dcs_responden.py` baris 73–78),
  HANYA mengecek truthy (`assert created["jabatan_label"]`), TIDAK membandingkan dengan
  `jabatan_utama_id` — **test ini TIDAK akan rusak oleh perubahan ini**, tidak perlu diubah.
  `test_wcp_responden.py` tidak punya assertion `jabatan_label` sama sekali (grep nihil).
- ✓ Fixture `jabatan_id_tk` (`tests/conftest.py` baris 178–189) tersedia untuk membuat partisipan
  dengan jabatan NYATA (bukan ID acak). **Koreksi presisi (verified 2026-07-14 via Explore agent):**
  fixture ini dipakai `test_opm_responden.py`, TAPI BUKAN lewat `partisipan_factory` — file itu
  memakai helper terpisah `_buat_partisipan()` di `tests/_opm_common.py` yang langsung
  `POST /api/v1/partisipan` dengan `jabatan_utama_id=jabatan_id` di payload. `partisipan_factory`
  TIDAK dipanggil sama sekali di `test_opm_responden.py` — jangan mencarinya di sana. Untuk test
  baru "resolusi benar" di Skenario uji di bawah, gunakan `jabatan_id_tk` bersama
  `partisipan_factory(subject, jabatan_utama_id=jabatan_id_tk)` langsung (pola fixture DCS/WCP
  yang sudah ada di `tests/conftest.py`, BUKAN meniru `_opm_common.py`).

## Langkah eksekusi

### Langkah 1 — DCS: suntik `JabatanService`, resolusi di `create_banyak()`

File: `src/anjab_abk_backend/dcs/services/responden_sql.py`. Baca ulang baris 15–31, 55–57,
126–181 dulu (nomor baris bisa bergeser).

1. Tambah import (di antara import lain, sebelum `from ..schemas.responden import ...`):
   ```python
   import logging

   from ...anjab.services.jabatan import JabatanService
   ```
   (`NotFoundError` SUDAH di-import baris 25 — tidak perlu ditambah lagi.)
2. Tambah `logger = logging.getLogger(__name__)` di level modul (setelah import, sebelum
   `def _to_read`).
3. Ubah `__init__` (baris 55–57) jadi:
   ```python
   def __init__(
       self,
       session: Session,
       partisipan_service: PartisipanService,
       jabatan_service: JabatanService,
   ) -> None:
       self._s = session
       self._par = partisipan_service
       self._jab = jabatan_service
   ```
4. Ubah baris 165 di `create_banyak()` — ganti:
   ```python
   jabatan_label=partisipan.jabatan_utama_id,
   ```
   menjadi (pola resolusi + fallback, ditempatkan SEBELUM konstruksi `DcsRespondenModel(...)`,
   di dalam loop `for partisipan_id in candidates:`, setelah `partisipan = self._par.get(partisipan_id)`):
   ```python
   try:
       jabatan_label = self._jab.get(partisipan.jabatan_utama_id).nama
   except NotFoundError:
       jabatan_label = partisipan.jabatan_utama_id
       logger.warning(
           "Jabatan '%s' tidak ditemukan untuk partisipan '%s' — jabatan_label DCS"
           " fallback ke ID mentah.",
           partisipan.jabatan_utama_id,
           partisipan_id,
       )
   rec = DcsRespondenModel(
       id=f"drsp_{uuid.uuid4().hex[:8]}",
       nama=partisipan.nama,
       jabatan_label=jabatan_label,
       partisipan_id=partisipan_id,
       sudah_submit=False,
   )
   ```

### Langkah 2 — WCP: perubahan identik

File: `src/anjab_abk_backend/wcp/services/responden_sql.py` — langkah 1–4 di atas diulang persis
(ganti `DcsRespondenModel`→`WcpRespondenModel`, pesan log menyebut "WCP"). Baca ulang file WCP
sebelum edit — meski terverifikasi identik strukturnya, nomor baris final bisa sedikit berbeda
setelah Langkah 1 selesai duluan (edit dua file independen, tidak saling bergantung urutan).

### Langkah 3 — Dependency injection

File: `src/anjab_abk_backend/dependencies.py`.

1. `get_dcs_responden_service()` (baris ~184–189): tambah parameter, teruskan ke constructor:
   ```python
   def get_dcs_responden_service(
       session: SessionDep,
       partisipan_service: Annotated[PartisipanService, Depends(get_partisipan_service)],
       jabatan_service: Annotated[JabatanService, Depends(get_jabatan_service)],
   ) -> DcsRespondenService:
       """SEAM: implementasi `DcsRespondenService` berbasis PostgreSQL."""
       return SqlDcsRespondenService(session, partisipan_service, jabatan_service)
   ```
2. `get_wcp_responden_service()` (baris ~158–163) — perubahan identik, teruskan ke
   `SqlWcpRespondenService(session, partisipan_service, jabatan_service)`.
   (Import `JabatanService`/`get_jabatan_service` SUDAH ada di file ini, baris 22–23 — tidak perlu
   ditambah.)

## Kriteria penerimaan

- [ ] `POST /api/v1/dcs/responden` (bulk) mengisi `jabatan_label` dengan nama jabatan hasil
      resolusi (`JabatanRead.nama`) bila `jabatan_utama_id` partisipan valid.
- [ ] Idem untuk `POST /api/v1/wcp/responden`.
- [ ] Partisipan dengan `jabatan_utama_id` yang tidak valid TIDAK menggagalkan assign — fallback ke
      ID mentah + warning log, endpoint tetap 201 seperti sebelumnya.
- [ ] `method create()` (single-assign) di kedua file TIDAK berubah sama sekali — tidak disentuh.
- [ ] Test existing (`test_create_responden_derives_nama_dan_jabatan_label`, dan seluruh test DCS/
      WCP responden lain) tetap lulus tanpa modifikasi.
- [ ] `openapi.json` **tidak berubah bentuk skema** (murni perubahan nilai runtime + DI internal,
      bukan kontrak HTTP) — regenerasi tetap dijalankan untuk memastikan tidak ada drift tak
      sengaja (seharusnya diff kosong).

## Skenario uji

Tambahkan ke `tests/test_dcs_responden.py` (dan `tests/test_wcp_responden.py`, pola identik):

1. **Test resolusi benar** — partisipan dengan jabatan NYATA:
   ```python
   def test_create_responden_resolve_jabatan_label_dari_jabatan_nyata(
       client: TestClient, partisipan_factory, jabatan_id_tk: str
   ) -> None:
       par_id = partisipan_factory("dcs-rsp-jabatan-nyata", jabatan_utama_id=jabatan_id_tk)
       created = _assign(client, [par_id])[0]

       jab = client.get(f"/api/v1/jabatan/{jabatan_id_tk}").json()
       assert created["jabatan_label"] == jab["nama"]
       assert created["jabatan_label"] != jabatan_id_tk
   ```
   (Path `GET /api/v1/jabatan/{jabatan_id}` terverifikasi — router `jabatan` di-mount dengan
   `prefix="/jabatan"` di `api/router.py` baris 68–70, operation_id `jabatan_get`.)
2. **Test fallback** — partisipan dengan `jabatan_utama_id` acak (perilaku default
   `partisipan_factory`, TIDAK perlu override apa pun):
   ```python
   def test_create_responden_fallback_jabatan_label_saat_jabatan_tidak_ada(
       client: TestClient, par_a: str
   ) -> None:
       created = _assign(client, [par_a])[0]
       # par_a dari partisipan_factory: jabatan_utama_id acak, tidak ada di DB.
       assert created["jabatan_label"]  # tidak error, tetap terisi (fallback ke ID)
   ```
   (Test ini pada dasarnya memformalkan perilaku `test_create_responden_derives_nama_dan_jabatan_label`
   yang sudah ada — boleh digabung/dilewati bila dianggap duplikat, TAPI test #1 di atas WAJIB ada
   karena tidak ada test lain yang memverifikasi resolusi nama sungguhan.)

## Definition of done

- [ ] `make test` hijau di `anjab-abk-backend`
- [ ] `openapi.json` diregenerasi (`make export-openapi` atau setara) — commit hanya bila memang
      berubah (seharusnya tidak berubah, lihat Kriteria penerimaan)
- [ ] `CLAUDE.md` (`anjab-abk-backend`) diperbarui dengan entri revisi desain singkat, termasuk
      mencabut/melengkapi catatan "di luar lingkup" di entri `[2026-07-12]`
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Data existing tidak dibackfill oleh item ini.** Baris `dcs_responden`/`wcp_responden` yang
  sudah ada (termasuk 3 baris uji coba dari sesi testing 2026-07-14:
  `drsp_55d09d5e`/`drsp_b63ac0a9`/`drsp_885b62b4` di instance produksi YPII, semuanya berstatus
  submitted & instrumen DCS sudah **Teranalisis** dengan data test) tetap menampilkan ID mentah
  sampai ada keputusan eksplisit soal backfill. Backfill TIDAK termasuk lingkup item ini — tanyakan
  ke user sebelum mengeksekusi UPDATE massal di database produksi.
- **`method create()` sengaja dibiarkan tidak konsisten** (masih menerima `jabatan_label` mentah
  dari parameter, tanpa resolusi) karena memang tidak ada jalur HTTP yang memanggilnya untuk
  DCS/WCP saat ini. Bila di masa depan ada endpoint baru yang menghidupkan kembali jalur
  single-assign, resolusi jabatan perlu ditambahkan di titik itu juga — di luar lingkup item ini.
- Ditemukan lewat testing manual di **instance produksi YPII** — lihat catatan risiko yang sama
  di item **021** soal 3 responden uji coba & status ANALYZED instrumen DCS.
- **Konfirmasi empiris untuk WCP (2026-07-14, sesi terpisah)**: simulasi SOP Persiapan+Pelaksanaan
  WCP end-to-end mereproduksi gejala yang sama — kolom Jabatan di Daftar Responden `/wcp` dan
  subtext header `/wcp/hasil-responden/{id}` menampilkan ID mentah (`jbt_4c034eef`, dst.), bukan
  nama jabatan. Menguatkan cakupan "DCS dan WCP" yang sudah dikunci di atas, termasuk baris
  `wrsp_7c0ff89d`/`wrsp_f5fad014`/`wrsp_ab6c6a0f` yang kini ikut perlu backfill (di luar lingkup
  item ini, sama seperti 3 baris DCS).
