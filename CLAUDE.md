# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**anjab-abk** adalah aplikasi untuk **Analisis Jabatan (ANJAB)** dan **Analisis Beban Kerja (ABK)** — dua instrumen manajemen SDM untuk memetakan posisi jabatan dan mengukur beban kerja pegawai.

**Target pengguna**: yayasan pendidikan yang mengelola **satu atau lebih sekolah** di berbagai jenjang (PAUD, SD, SMP, SMA, SMK, dll.). Satu yayasan bisa punya beberapa satuan pendidikan; tiap satuan pendidikan diperlakukan sebagai unit kerja tersendiri.

## Repository Structure

Repo ini adalah **repo induk** yang mengelola tiga sub-repo sebagai **git submodule**:

| Sub-repo | Path | Deskripsi |
|---|---|---|
| anjab-abk-mcp | `./anjab-abk-mcp/` | MCP server — bridge antara Claude dan data ANJAB/ABK |
| anjab-abk-backend | `./anjab-abk-backend/` | REST API backend (FastAPI) |
| anjab-abk-web-app | `./anjab-abk-web-app/` | Web application (frontend) |

## Git Submodule Commands

```bash
# Clone repo induk beserta semua submodule
git clone --recurse-submodules <url>

# Update semua submodule ke commit terbaru di branch masing-masing
git submodule update --remote --merge

# Inisialisasi submodule setelah clone biasa
git submodule update --init --recursive

# Tambah submodule baru
git submodule add <url> <path>
```

## Domain Knowledge

- **ANJAB (Analisis Jabatan)**: proses pengumpulan, pencatatan, pengolahan, dan penyusunan data jabatan menjadi informasi jabatan — mencakup uraian jabatan, syarat jabatan, dan peta jabatan.
- **ABK (Analisis Beban Kerja)**: teknik manajemen untuk mengetahui tingkat efektivitas dan efisiensi kerja suatu jabatan/unit organisasi berdasarkan volume pekerjaan dan norma waktu.

### Konteks Yayasan Pendidikan

- **Yayasan** adalah entitas pemilik yang menaungi satu atau lebih **satuan pendidikan** (sekolah).
- **Satuan pendidikan** diperlakukan sebagai unit kerja utama; jenjang yang mungkin: PAUD, TK, SD, SMP, SMA, SMK, dan kombinasinya.
- Satu yayasan bisa punya sekolah di beberapa jenjang dan/atau beberapa lokasi — tiap satuan pendidikan dianalisis ANJAB/ABK secara terpisah.
- Jabatan di lingkungan yayasan pendidikan mencakup: pengurus yayasan, kepala sekolah, wakil kepala sekolah, guru (per mata pelajaran/kelas), staf tata usaha, tenaga kependidikan (pustakawan, laboran, dll.), dan tenaga pendukung (satpam, kebersihan, dll.).
- **UnitKerja** dalam konteks ini bisa berupa: yayasan (pusat), satuan pendidikan, atau sub-unit dalam sekolah (mis. divisi kurikulum, kesiswaan).

## Task Inventory — Alur 3 Tahap

Pengisian Task Inventory dibagi menjadi **3 tahap** dengan status sesi: `DRAFT → TAHAP1 → TAHAP2 → TAHAP3 → CLOSED → ANALYZED`.

| Tahap | Aktor | Deskripsi |
|---|---|---|
| **Tahap 1** | Anggota SME panel | Pilih task yang relevan untuk jabatan. Partisipan di >1 panel harus isi per panel. |
| **Tahap 2** | Koordinator SME panel | Review task yang tidak dipilih unanimously di Tahap 1; tentukan setuju/tidak. |
| **Tahap 3** | Anggota SME panel | Isi detail CalHR (5 komponen) per task. Task yang masuk = unanimous ∪ koordinator-disetujui. |

### Aturan teknis Task Inventory

- **`koordinator_id`** disimpan di `TiSesi`; koordinator akses review via `GET/POST /sesi/{id}/tahap2`.
- **Freeze task** terjadi di transisi TAHAP2→TAHAP3 (`mulai-tahap3`): `final = unanimous ∪ coordinator_approved`.
- Task **unanimous** (semua anggota pilih) otomatis masuk tanpa review koordinator.
- Task **partial** (sebagian pilih) ditampilkan di halaman review koordinator (`/task-inventory/tahap2/{sesi_id}`).
- Partisipan mengisi detail di `/task-inventory/tahap3/{responden_id}`.

## Backlog

Pekerjaan yang **sudah direncanakan tapi belum dieksekusi** dicatat sebagai berkas Markdown di repo
induk ini — bukan di sub-repo — karena banyak pekerjaan menyentuh dua atau tiga sub-repo sekaligus.

- **[`BACKLOG.md`](BACKLOG.md)** — indeks: satu baris per item (ID, judul, repo, status, blocked-by).
  Ini satu-satunya tempat melihat urutan & ketergantungan antar item.
- **`backlog/<id>-<slug>.md`** — satu berkas per item, berisi rencana **detail dan siap dieksekusi**.
- **[`backlog/TEMPLATE.md`](backlog/TEMPLATE.md)** — struktur wajib item baru.

Aturan:

1. Item backlog ditulis cukup lengkap sehingga agen pelaksana (mis. Sonnet) bisa mengeksekusinya
   **tanpa menginterpretasi ulang** — sertakan keputusan yang sudah dikunci, fakta kode aktual
   (`path:baris`, ditandai ✓), langkah konkret, kriteria penerimaan, skenario uji, dan definition of done.
2. **Satu item = satu repo.** Pekerjaan lintas repo dipecah per repo dan diurutkan lewat kolom
   *blocked by* (mis. backend dulu → MCP & web app menyusul setelah `openapi.json` berubah).
3. Item yang sudah dieksekusi dipindahkan ke tabel "Selesai" di `BACKLOG.md`, berkasnya tetap
   disimpan sebagai jejak keputusan.
4. Saat berada di **plan mode** untuk pekerjaan anjab-abk, materialisasikan rencananya jadi item
   backlog — jangan biarkan hanya jadi rencana sesaat di dalam percakapan.

Berkas `rencana-*.md` / `plan-*.md` di akar repo adalah format **lama** (sebelum mekanisme ini ada).
Jangan tambah yang baru; tulis item backlog.

## Development Guidelines

- Commit message ditulis dalam **Bahasa Indonesia**.
- Branch utama di setiap repo bernama **master**.
- Setiap sub-repo memiliki `CLAUDE.md` sendiri dengan panduan teknis spesifik.
- Gunakan skill `git-workflow-skill` untuk commit/push/PR dan `github-cli-skill` untuk interaksi GitHub.
