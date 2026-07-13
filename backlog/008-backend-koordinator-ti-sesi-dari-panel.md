# Backlog 008 — Backend: koordinator sesi TI otomatis diwarisi dari SME panel

> **Repo:** `anjab-abk-backend`
> **Status:** Siap dieksekusi
> **Blocked by:** —
> **Skill yang dipakai:** `backend-skill`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

Saat sesi Task Inventory dibuat untuk sebuah jabatan, backend sudah otomatis mendaftarkan seluruh
anggota SME panel jabatan itu sebagai responden (item 005). Tapi `koordinator_id` sesi **tidak**
ikut diwarisi dari `SmePanel.koordinator_id` — admin harus menetapkannya lagi lewat PATCH sesi.

Temuan dari simulasi end-to-end TI di deployment YPII (2026-07-13): koordinator sudah ditetapkan di
Master Data → SME Panel, tapi sesi yang baru dibuat tetap menampilkan "Koordinator: Belum ditentukan".
Bila admin melewatkan langkah manual ini, **Tahap 2 tidak punya siapa pun yang bisa mereview** — task
partial tidak akan pernah diputuskan, dan saat masuk Tahap 3 semuanya diabaikan tanpa peringatan.

Panel sudah ada di tangan pada saat auto-assign responden dijalankan, jadi perbaikannya murni logika
service — tidak ada perubahan schema maupun migrasi.

## Keputusan yang sudah dikunci

1. **Payload menang atas panel.** `koordinator_id` diisi dari `panel.koordinator_id` **hanya bila**
   `data.koordinator_id is None`. Bila pemanggil mengirim `koordinator_id` eksplisit (termasuk sebagai
   bagian dari `TiSesiCreate`), nilai itu dipakai apa adanya.
2. **Best-effort, bukan validasi.** Panel tidak ada / panel tanpa koordinator → sesi tetap dibuat dengan
   `koordinator_id = None`. Jangan melempar error. Ini mengikuti pola auto-assign responden yang sudah ada
   (`sesi_sql.py:127-137`: "Panel tidak ada/kosong → sesi tetap dibuat kosong (tidak error)").
3. **Tidak ada migrasi Alembic.** Kolom `ti_sesi.koordinator_id` sudah ada sejak initial schema.
   `models.py` tidak disentuh sama sekali.
4. **Tidak ada perubahan schema Pydantic.** `koordinator_id` sudah ada di `TiSesiCreate`.
5. **Perilaku PATCH tidak berubah.** Admin tetap bisa mengganti koordinator kapan pun (PATCH sesi
   non-DRAFT sudah mengizinkan `koordinator_id` sebagai satu-satunya field yang boleh berubah).

## Kondisi sekarang (verified)

| Fakta | Lokasi | ✓ |
|---|---|---|
| Endpoint create sesi TI (`taskinv_sesi_create`) memanggil `service.create(payload)` | `src/anjab_abk_backend/api/v1/taskinv_sesi.py:60-109` (panggilan di :106) | ✓ |
| Service produksi `SqlTiSesiService.create()` | `src/anjab_abk_backend/taskinv/services/sesi_sql.py:95` | ✓ |
| Record dibuat dengan `koordinator_id=data.koordinator_id` — **tanpa fallback ke panel** | `sesi_sql.py:108-117` | ✓ |
| Auto-assign responden dari panel; objek `panel` sudah di tangan tapi `panel.koordinator_id` tak pernah dibaca | `sesi_sql.py:127-137` | ✓ |
| Seam kedua `InMemoryTiSesiService.create` — **tidak punya auto-populate panel sama sekali** | `src/anjab_abk_backend/taskinv/services/sesi.py:99-123` | ✓ |
| `TiSesiModel.koordinator_id: Mapped[str \| None]`, `String(40)`, nullable, tanpa FK | `src/anjab_abk_backend/models.py:429` | ✓ |
| `SMEPanelModel.koordinator_id` idem; panel **unik per jabatan** (`jabatan_id ... unique=True`) → lookup deterministik | `models.py:184`, `models.py:183` | ✓ |
| `koordinator_id` sudah ada di `TiSesiCreate` (default `None`) / `TiSesiUpdate` / `TiSesiRead` | `src/anjab_abk_backend/taskinv/schemas/sesi.py:36-40`, `:52`, `:70-72` | ✓ |
| Kolom sudah ada di initial schema → **tidak butuh migrasi** | `migrations/versions/20260623_b2bbd3afbe65_initial_schema.py:262` (`ti_sesi`), `:179` (`sme_panel`) | ✓ |
| Test auto-assign responden yang sudah ada (jadi contoh pola) | `tests/test_taskinv.py:1065`, `:1078`, `:1085` | ✓ |
| Test koordinator yang ada hanya menguji `koordinator_id` **eksplisit di payload** | `tests/test_taskinv.py:206` (`test_sesi_koordinator_id`) | ✓ |
| Helper test: `_create_sesi` (`test_taskinv.py:51`), `_setup_panel` (`test_taskinv.py:1040`) | `tests/test_taskinv.py` | ✓ |

Agen pelaksana **wajib membaca ulang** file-file di atas sebelum mengedit — nomor baris bisa bergeser.

## Langkah eksekusi

### Langkah 1 — Warisi koordinator di `SqlTiSesiService.create()`

`src/anjab_abk_backend/taskinv/services/sesi_sql.py`.

Masalah urutan: `panel` saat ini di-query **setelah** `rec` dibuat & di-flush (baris 127-137), padahal
`koordinator_id` dibutuhkan **saat** membuat `rec` (baris 108-117). Pindahkan lookup panel ke **sebelum**
pembuatan record, lalu pakai satu objek `panel` yang sama untuk dua keperluan (koordinator + responden) —
jangan query dua kali.

Bentuk akhir yang diharapkan (sesuaikan dengan kode aktual saat mengedit):

```python
# Panel unik per jabatan (SMEPanelModel.jabatan_id unique) → satu lookup, dua keperluan:
# mewarisi koordinator + auto-assign anggota sebagai responden.
panel = self._s.scalar(
    select(SMEPanelModel).where(SMEPanelModel.jabatan_id == data.jabatan_id)
)

# Payload menang atas panel; panel hanya dipakai bila pemanggil tidak menentukan koordinator.
koordinator_id = data.koordinator_id
if koordinator_id is None and panel is not None:
    koordinator_id = panel.koordinator_id

rec = TiSesiModel(
    ...
    koordinator_id=koordinator_id,
    ...
)
...
if panel is not None and panel.anggota:
    assign_ti_responden_banyak(
        self._s, rec.id, panel.partisipan_ids, max_responden=data.max_responden
    )
```

### Langkah 2 — Samakan perilaku seam in-memory

`src/anjab_abk_backend/taskinv/services/sesi.py:99-123` (`InMemoryTiSesiService.create`) saat ini tidak
punya auto-populate panel **sama sekali** — jadi seam ini sudah divergen dari seam SQL bahkan sebelum
perubahan ini.

Ruang lingkup item ini **hanya koordinator**: bila seam in-memory punya akses ke data panel, terapkan
aturan pewarisan yang sama. Bila tidak (tidak ada store panel di seam ini), **jangan** memaksakan —
cukup tambahkan komentar singkat di `create()` yang menyatakan bahwa pewarisan koordinator & auto-assign
responden dari panel adalah perilaku seam SQL, dan seam in-memory sengaja tidak mengikutinya. Jangan
melebarkan item ini menjadi refactor dua seam.

### Langkah 3 — Test

`tests/test_taskinv.py`. Ikuti pola `test_create_sesi_auto_populate_dari_panel` (:1065) dan helper
`_setup_panel` (:1040). Tambahkan:

1. `test_create_sesi_mewarisi_koordinator_dari_panel` — panel punya `koordinator_id`; sesi dibuat **tanpa**
   `koordinator_id` di payload → respons `TiSesiRead.koordinator_id` == koordinator panel.
2. `test_create_sesi_koordinator_payload_menang_atas_panel` — panel punya koordinator A; payload mengirim
   koordinator B → hasil B.
3. `test_create_sesi_panel_tanpa_koordinator_tetap_none` — panel ada tapi `koordinator_id` null → sesi
   `koordinator_id is None`, dan **sesi tetap terbuat** (tidak error).
4. `test_create_sesi_tanpa_panel_koordinator_none` — jabatan tanpa panel → `koordinator_id is None`, sesi
   tetap terbuat.

## Kriteria penerimaan

- [ ] `POST /api/v1/task-inventory/sesi` untuk jabatan yang panelnya punya koordinator, tanpa
      `koordinator_id` di payload → respons memuat `koordinator_id` milik panel.
- [ ] `koordinator_id` eksplisit di payload tidak pernah ditimpa nilai panel.
- [ ] Jabatan tanpa panel / panel tanpa koordinator → sesi tetap terbuat, `koordinator_id` null, tanpa error.
- [ ] Panel di-query **satu kali** di `create()` (tidak ada query ganda untuk koordinator dan responden).
- [ ] Tidak ada berkas migrasi baru; `models.py` tidak berubah.

## Skenario uji

Empat test baru di `tests/test_taskinv.py` (lihat Langkah 3). Jalankan gate lengkap:

```bash
cd anjab-abk-backend && make test
```

`tests/test_migrations.py::test_schema_matches_models` harus tetap hijau — bila gagal, berarti `models.py`
ikut tersentuh, dan itu di luar ruang lingkup item ini.

## Definition of done

- [ ] `make test` hijau di `anjab-abk-backend`
- [ ] `CHANGELOG.md` diperbarui
- [ ] `CLAUDE.md` repo diperbarui bila ada perubahan model/alur (di sini: kemungkinan besar **tidak** —
      hanya catatan perilaku di bagian Task Inventory bila dirasa perlu)
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

- **Sesi TI yang sudah terlanjur dibuat tanpa koordinator tidak ikut diperbaiki** oleh perubahan ini
  (ini logika create, bukan backfill). Sesi lama harus di-PATCH manual lewat UI. Tidak ada rencana
  migrasi data — konfirmasikan ke user bila ia mengharapkan sesi lama ikut terisi.
- Panel bisa berganti koordinator **setelah** sesi dibuat; sesi tidak ikut berubah. Ini disengaja —
  `ti_sesi.koordinator_id` adalah snapshot saat pembuatan, bukan referensi hidup ke panel. Web app
  tetap menyediakan form ganti koordinator di halaman sesi.
- Tidak ada FK dari `ti_sesi.koordinator_id` ke `partisipan`, jadi tidak ada jaminan integritas di level
  DB. Item ini **tidak** menambahkannya (akan butuh migrasi + keputusan soal data lama).
