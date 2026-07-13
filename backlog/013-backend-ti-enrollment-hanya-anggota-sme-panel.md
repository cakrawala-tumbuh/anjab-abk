# Backlog 013 — Backend: enrollment TI hanya anggota SME panel (hapus auto-enroll universal)

> **Repo:** `anjab-abk-backend`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `backend-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Partisipan saat ini bisa melihat — dan otomatis terdaftar ke — **semua** sesi Task Inventory yang
aktif, termasuk sesi jabatan yang sama sekali bukan urusannya. Ini bukan kebocoran lewat tebak-ID,
melainkan perilaku yang memang ditulis di `GET /task-inventory/kuesioner/saya`: endpoint itu mencari
seluruh sesi berstatus TAHAP1/TAHAP2/TAHAP3 tanpa filter partisipan, lalu memanggil
`ensure_for_partisipan()` yang **meng-INSERT baris `TiRespondenModel`** untuk setiap sesi tersebut.

Ini sisa desain lama yang tidak ikut dimigrasikan. Revisi `[2026-06-21]` di `CLAUDE.md` backend
sudah menyatakan *"Task Inventory tetap menggunakan flow yang sama (assignment manual via
tambah-responden)"* — klaim itu **tidak pernah benar di kode**. DCS/WCP/OPM sudah assignment-based
(`list_by_partisipan`), TI tertinggal.

Sejak item 008, sesi TI **sudah** otomatis mendaftarkan seluruh anggota SME panel jabatannya sebagai
responden saat `create()`. Jalur enrollment yang benar sudah ada dan sudah bekerja; auto-enroll
universal di `/kuesioner/saya` justru **membatalkan** penyaringan SME panel itu. Yang perlu dilakukan
adalah membuang auto-enroll universal, bukan membangun mekanisme baru.

## Keputusan yang sudah dikunci

1. **Enrollment TI = anggota SME panel jabatan sesi itu, ditetapkan saat sesi dibuat.** Tidak ada
   enrollment di waktu baca. `/kuesioner/saya` menjadi **murni pembacaan** — tidak boleh lagi menulis
   ke DB.
2. **`ensure_for_partisipan()` dihapus total** dari `TiRespondenService` (Protocol + impl SQL + impl
   in-memory). Ia hanya dipanggil dari satu tempat (`taskinv_kuesioner.py:62`) — tidak ada pemakai lain.
   Jangan disisakan sebagai dead code.
3. **`/kuesioner/saya` memakai `list_by_partisipan(par.id)`**, meniru persis pola OPM
   (`opm_kuesioner.py:52-57`): iterasi responden milik partisipan → ambil sesinya → saring status.
4. **Filter status tetap `TAHAP1 | TAHAP2 | TAHAP3`** (`_ACTIVE_STATUSES`, `taskinv_kuesioner.py:28`).
   Sesi DRAFT/CLOSED/ANALYZED tetap tidak muncul di daftar kuesioner partisipan. Tidak ada perubahan
   perilaku di sini.
5. **Kontrak `TiKuesionerItemRead` tidak berubah** — semua field tetap, termasuk `is_koordinator`.
   Tidak ada perubahan `openapi.json` selain hilangnya efek samping (MCP & web app tidak perlu ikut
   berubah; **tidak ada item turunan** untuk repo lain).
6. **Tidak ada migrasi Alembic.** `models.py` tidak disentuh.
7. **Pembersihan baris auto-enroll lama TIDAK masuk item ini** — lihat "Risiko & catatan". Perubahan
   ini menghentikan pendarahan; data lama ditangani terpisah setelah dikonfirmasi ke user.

## Kondisi sekarang (verified)

| Fakta | Lokasi | ✓ |
|---|---|---|
| `/kuesioner/saya` TI mencari **semua** sesi aktif tanpa filter partisipan, lalu `ensure_for_partisipan()` per sesi | `src/anjab_abk_backend/api/v1/taskinv_kuesioner.py:53-66` | ✓ |
| Docstring endpoint mengakui perilakunya: *"Task Inventory bersifat universal — tiap partisipan mengisi SEMUA sesi aktif"* | `taskinv_kuesioner.py:45-48` | ✓ |
| `_ACTIVE_STATUSES = ["TAHAP1", "TAHAP2", "TAHAP3"]` | `taskinv_kuesioner.py:28` | ✓ |
| `ensure_for_partisipan` dipanggil **hanya** dari `taskinv_kuesioner.py:62` (tidak ada pemakai lain di `src/` maupun `tests/`) | grep repo-wide | ✓ |
| `ensure_for_partisipan` — Protocol | `src/anjab_abk_backend/taskinv/services/responden.py:40` | ✓ |
| `ensure_for_partisipan` — impl in-memory | `taskinv/services/responden.py:112` | ✓ |
| `ensure_for_partisipan` — impl SQL (yang meng-INSERT) | `taskinv/services/responden_sql.py:191` | ✓ |
| `list_by_partisipan` **sudah ada** di TI tapi tidak pernah dipanggil | Protocol `responden.py:33`, in-memory `responden.py:70`, SQL `responden_sql.py:139` | ✓ |
| Pola target — OPM: `for rsp in rsp_service.list_by_partisipan(par.id)` lalu saring `sesi.status` | `src/anjab_abk_backend/api/v1/opm_kuesioner.py:52-57` | ✓ |
| Pola target — DCS, docstring eksplisit *"Tidak ada enrollment otomatis"* | `src/anjab_abk_backend/api/v1/dcs_kuesioner.py:40-45` | ✓ |
| Sesi TI **sudah** auto-assign anggota SME panel sebagai responden saat create (item 005/008) | `taskinv/services/sesi_sql.py` (`create()` → `assign_ti_responden_banyak()`) | ✓ |
| Koordinator **wajib anggota panel** → auto-assign anggota otomatis mencakup koordinator | `anjab/schemas/sme_panel.py:32`, `:50` | ✓ |
| Melepas anggota panel otomatis mengosongkan `koordinator_id` → koordinator tak pernah jadi non-anggota | `anjab/services/sme_panel_sql.py:155-156` | ✓ |
| `TiKuesionerItemRead` — field yang harus tetap terisi, termasuk `is_koordinator` | `taskinv/schemas/kuesioner.py:10-38` | ✓ |

Agen pelaksana **wajib membaca ulang** file-file di atas sebelum mengedit — nomor baris bisa bergeser.

## Langkah eksekusi

### Langkah 1 — Tulis ulang `/kuesioner/saya` menjadi read-only

`src/anjab_abk_backend/api/v1/taskinv_kuesioner.py`.

Ganti blok `sesi_service.search(...)` + loop `ensure_for_partisipan()` (baris 53-66) dengan iterasi atas
responden milik partisipan. Bentuk akhir yang diharapkan (sesuaikan dengan kode aktual):

```python
def kuesioner_saya(...) -> list[TiKuesionerItemRead]:
    """Kembalikan sesi TI yang partisipannya sudah terdaftar sebagai responden, bila sesi aktif.

    Partisipan hanya melihat sesi tempat ia terdaftar sebagai responden — pendaftaran terjadi
    saat sesi dibuat, dari anggota SME panel jabatan tersebut. Tidak ada enrollment otomatis.
    """
    par = par_service.get_by_subject(principal.subject)
    if par is None:
        return []

    result = []
    for rsp in rsp_service.list_by_partisipan(par.id):
        sesi = sesi_service.get(rsp.sesi_id)
        if sesi.status not in _ACTIVE_STATUSES:
            continue
        try:
            jabatan_nama = jabatan_service.get(sesi.jabatan_id).nama
        except Exception:
            jabatan_nama = None
        result.append(TiKuesionerItemRead(... seperti sekarang ...))
    return result
```

Catatan: `sesi_service` dan `jabatan_service` **tetap** dibutuhkan sebagai dependency (untuk status &
nama jabatan); yang hilang hanya `search()` dan `ensure_for_partisipan()`. Pertahankan `try/except`
pada lookup jabatan — perilaku existing, jangan diubah di item ini.

### Langkah 2 — Hapus `ensure_for_partisipan` dari service TI

Hapus di tiga tempat: Protocol `taskinv/services/responden.py:40`, impl in-memory
`responden.py:112`, impl SQL `responden_sql.py:191`. Setelah Langkah 1 tidak ada pemanggil tersisa —
pastikan dengan grep sebelum menghapus.

Jangan sentuh `list_by_sesi`, `assign_banyak`, `create`, maupun fungsi level-modul
`assign_ti_responden_banyak()` — semuanya masih dipakai jalur enrollment yang sah.

### Langkah 3 — Test

`tests/test_taskinv.py`. Buang/sesuaikan test lama yang mengasumsikan auto-enroll universal (cari test
yang memanggil `/kuesioner/saya` lalu mengharapkan sesi muncul tanpa responden dibuat lebih dulu —
test semacam ini **akan** gagal, dan itu memang benar). Tambahkan:

1. `test_kuesioner_saya_hanya_sesi_yang_terdaftar` — partisipan A anggota panel jabatan X; sesi dibuat
   untuk jabatan X **dan** jabatan Y (panel berbeda, A bukan anggota) → `/kuesioner/saya` milik A
   hanya memuat sesi X.
2. `test_kuesioner_saya_tidak_membuat_responden` — partisipan yang bukan anggota panel mana pun
   memanggil `/kuesioner/saya` → respons `[]` **dan** jumlah baris `TiRespondenModel` di DB tidak
   bertambah (ini inti bug-nya; assert count sebelum/sesudah).
3. `test_kuesioner_saya_saring_status_nonaktif` — sesi tempat partisipan terdaftar berstatus DRAFT /
   CLOSED / ANALYZED → tidak muncul.
4. `test_kuesioner_saya_is_koordinator` — koordinator panel melihat sesinya dengan
   `is_koordinator = true` (memastikan koordinator tidak kehilangan akses setelah pengetatan).

## Kriteria penerimaan

- [ ] `GET /task-inventory/kuesioner/saya` hanya mengembalikan sesi tempat pemanggil sudah terdaftar
      sebagai responden.
- [ ] Endpoint tersebut **tidak menulis apa pun ke DB** — jumlah baris `ti_responden` tidak berubah
      berapa kali pun ia dipanggil.
- [ ] `ensure_for_partisipan` tidak lagi ada di `src/` (grep bersih, termasuk Protocol).
- [ ] Koordinator SME panel tetap melihat sesinya dengan `is_koordinator = true`.
- [ ] `TiKuesionerItemRead` tidak berubah; `make export-openapi` tidak menghasilkan diff pada skema
      (hanya deskripsi endpoint yang boleh berubah).
- [ ] Tidak ada berkas migrasi baru; `models.py` tidak berubah.

## Skenario uji

Empat test di `tests/test_taskinv.py` (lihat Langkah 3). Gate lengkap:

```bash
cd anjab-abk-backend && make test
```

`tests/test_migrations.py::test_schema_matches_models` harus tetap hijau.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-backend`
- [ ] `CHANGELOG.md` diperbarui
- [ ] `CLAUDE.md` repo diperbarui — **wajib**: tambahkan entri Revisi Desain yang menyatakan TI kini
      assignment-based, **dan koreksi klaim keliru di revisi `[2026-06-21]`** yang menyebut TI sudah
      assignment-based padahal tidak pernah begitu di kode
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Data lama di deployment YPII kemungkinan besar sudah tercemar.** Setiap partisipan yang pernah
  membuka halaman kuesioner sejak sesi TI pertama dibuat punya baris `ti_responden` di **semua** sesi
  aktif saat itu. Perubahan ini menghentikan pendarahan tapi **tidak** membersihkan baris lama —
  partisipan yang terlanjur ter-enroll akan tetap melihat sesi yang bukan haknya.

  Kandidat baris untuk dibersihkan: `ti_responden` yang `tahap1_submit = false` **dan** `tahap3_submit
  = false` **dan** `partisipan_id`-nya bukan anggota `sme_panel` jabatan sesi tersebut. Baris yang
  sudah ter-submit **jangan disentuh** — itu data jawaban nyata, dan menghapusnya akan mengubah hasil
  agregasi (`count_tahap1_submitted` adalah penyebut unanimity di Tahap 2).

  **Konfirmasikan ke user** sebelum mengeksekusi pembersihan apa pun. Kalau disetujui, ini item
  terpisah (script satu kali, bukan migrasi Alembic — ini pembersihan data, bukan perubahan skema).
  Jangan lakukan sebagai bagian dari item ini.
- Partisipan yang **ditambahkan ke SME panel setelah sesi dibuat** tidak otomatis jadi responden —
  enrollment adalah snapshot saat `create()`. Admin harus menambahkannya lewat
  `POST /sesi/{id}/responden` (single) atau `/responden/bulk`. Ini perilaku yang sudah ada sejak item
  005/008 dan **tidak** diubah di sini; sebutkan ke user bila ia mengharapkan panel jadi referensi hidup.
- Item **014 bergantung pada item ini**. Guard "admin ATAU responden sesi ini" di item 014 tidak
  menyaring apa pun selama auto-enroll universal masih hidup (semua orang adalah responden semua sesi).
  Kerjakan 013 lebih dulu.
