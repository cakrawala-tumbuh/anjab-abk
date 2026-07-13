# Backlog <ID> — <Judul singkat>

> **Repo:** `<anjab-abk-backend | anjab-abk-mcp | anjab-abk-web-app>`
> **Status:** Siap dieksekusi | Menunggu (blocked by <ID>) | Sedang dikerjakan | Selesai
> **Blocked by:** <ID lain, atau —>
> **Skill yang dipakai:** `<backend-skill | frontend-development-skill | mcp-development-skill>`, `automated-test-skill`
> **Jangan commit tanpa instruksi eksplisit user.**

## Tujuan

<Satu-dua paragraf: apa yang berubah dan kenapa. Rujuk keputusan produk bila ada.>

## Keputusan yang sudah dikunci

<Daftar keputusan desain yang TIDAK boleh ditawar ulang oleh agen pelaksana. Ini yang membedakan
backlog dari sekadar catatan: agen tidak perlu menginterpretasi ulang.>

## Kondisi sekarang (verified)

<Tabel/daftar fakta kode aktual + path:baris. Tandai ✓ untuk yang sudah dicek. Agen pelaksana WAJIB
membaca ulang file-nya sebelum mengedit — baris bisa bergeser.>

## Langkah eksekusi

### Langkah 1 — <nama>

<Instruksi konkret: file yang disentuh, isi perubahan, potongan kode bila perlu.>

### Langkah 2 — ...

## Kriteria penerimaan

- [ ] <hasil yang bisa diverifikasi, bukan "sudah dikerjakan">

## Skenario uji

<Test yang harus ada/lulus. Sebutkan file test dan perintah `make test`.>

## Definition of done

- [ ] `make test` hijau di repo terkait
- [ ] `CHANGELOG.md` diperbarui
- [ ] `CLAUDE.md` repo diperbarui bila ada perubahan model/alur
- [ ] Item dipindah ke tabel "Selesai" di `BACKLOG.md`

## Risiko & catatan

<Hal yang bisa meledak, data yang bisa hilang, hal yang perlu dikonfirmasi ke user.>
