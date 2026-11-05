---
title: "OD-11 Kebijakan Pemakaian AI, Versi 1"
description: "Keputusan OD-11 tentang provider, model, jalur data, retensi, izin pemrosesan, dan jalur manual untuk lapisan pemanggil AI aplikasi ANJAB/ABK."
published: true
date: 2026-11-04T00:00:00.000Z
tags: kebijakan, ai, privasi
editor: markdown
dateCreated: 2026-11-04T00:00:00.000Z
doc_id: "KBJ-2ebb120b"
category: "kebijakan"
owner: "Sponsor, data steward, security"
status: "aktif"
version: "1.1"
effective_date: "2026-11-04"
last_reviewed: "2026-11-05"
related_docs: ["KBJ-f18de0a3"]
---

# OD-11 Kebijakan Pemakaian AI, Versi 1

**Dokumen ini tidak menyalakan AI.** Versi 1.1 (5 November 2026) mencatat bahwa penyedia dipilih admin lewat UI di antara dua jalur, `API_ANTHROPIC` dan `LANGGANAN_CLAUDE`; memilih penyedia tidak menyalakan AI. Ia mencatat keputusan OD-11, yaitu kebijakan provider/model, jalur data, privasi, retensi, izin pemrosesan, dan jalur manual yang disyaratkan sebelum AI atas data riil dipakai (OD:28: "Fitur AI atas data riil nonaktif; operasi manual berizin boleh berlanjut"). Menyalakan AI dan menyatakan izin atas data pribadi sudah ada adalah keputusan terpisah (AKTIF-F1), di luar dokumen ini.

## Latar Belakang

Aplikasi ANJAB/ABK direncanakan memiliki lapisan pemanggil AI untuk membantu Tim menyusun draf narasi. Keputusan K-1 sampai K-16 diputuskan oleh user pada 4 November 2026 ("Oke, setuju semua") atas rekomendasi di berkas rencana sesi (`Rencana-Pemanggil-AI.md` versi 4 November 2026, §3). Pada 5 November 2026 pemilik proyek memutuskan penyedia dipilih admin lewat UI (Anthropic API atau paket langganan Anthropic), dan bahwa aturan ZDR sebelum data pribadi (K-6) dikesampingkan khusus untuk mode langganan; backlog kodenya ada di `cakrawala-tumbuh/anjab-abk-backend#109` sampai `#112` dan `cakrawala-tumbuh/anjab-abk-web-app#104`. Sebelum dokumen ini, keputusan K-1 sampai K-16 hanya ada di berkas rencana tersebut, sehingga syarat "OD-11 tertulis" untuk AKTIF-F1 belum terpenuhi. Rujukan pelacakan: `cakrawala-tumbuh/ypii-support#442`.

## Tujuan

Menetapkan secara tertulis dan bertanggal apa yang sudah diputuskan, apa yang menunggu pengesahan, dan apa yang belum diverifikasi, tanpa menyatakan hal yang tidak ada di sumber.

## Ruang Lingkup

Berlaku untuk lapisan pemanggil AI aplikasi ANJAB/ABK. Tidak mencakup: menyalakan AI, pernyataan bahwa izin data sudah ada atau bahwa persetujuan pemilik data sudah diperoleh, pemberitahuan kepada Tim (K-17), dan perubahan kode atau konfigurasi.

## Definisi dan Singkatan

| Istilah | Arti |
|:--|:--|
| T0 | Data sintetis. |
| T1 | Dokumen resmi tanpa data pribadi (SOP, mandat, struktur). |
| T2 | Cerita dan keterangan orang (data pribadi). |
| ZDR | Zero Data Retention. |
| AKTIF-F1 | Keputusan terpisah untuk menyalakan AI pada F1 dokumen resmi. |
| OD, RM, KD4, 06/01, SPEC, PG, PRD, PRM, SOP, KAI, KN, SQL | Kode rujukan ke Edisi Terpadu R1.1, sebagaimana dipakai di berkas rencana sumber. |

## Pernyataan Kebijakan

### 1. Keputusan lingkup

1. **K-1.** Draf AI boleh dipakai di ruang kerja Tim sebelum aturan kartu untuk responden (OD-12) selesai, hanya untuk F1 dokumen resmi. Alasan di sumber: OD:29 merinci bahwa yang tertahan hanya layar responden, dan jalur ini tidak menampilkan apa pun ke sekolah. Risiko yang dicatat: BL:14 dan RM:40 bisa dibaca lebih luas dan Tim bisa berpendapat lain; karena itu Tim sebaiknya diberi tahu.
1. **K-2.** Kebijakan ini diputuskan secara teknis oleh pihak pelaksana, sedangkan bagian data pribadi (T2) berstatus **menunggu pengesahan Yayasan/pemilik data**. Pemilik OD-11 yang diusulkan paket adalah "Sponsor, data steward, security" (OD:28), dan data steward/etik ditugaskan memastikan dasar pemrosesan AI (06/01:37). Kewenangan atas data YPII belum dikonfirmasi lewat bahan yang ada; konfirmasinya diminta dari user.
1. **K-3.** Tahap data: mulai dari T0, naik ke T1 lewat keputusan eksplisit, dan T2 hanya setelah butir 9 dan 12 daftar konfirmasi terjawab serta K-6 selesai. Untuk `LANGGANAN_CLAUDE`, syarat K-6 dikesampingkan (lihat K-6 dan bagian 4); syarat lain, termasuk K-2, tidak berubah. Alasan: setiap kenaikan menambah risiko tanpa bisa ditarik setelah data terkirim.

### 2. Isi OD-11 (Kelompok B)

| Pokok | Keputusan | Status fakta |
|:--|:----|:---|
| Provider | Anthropic, lewat salah satu dari dua jalur yang dipilih admin di UI (bawaan `MATI`; memilih penyedia tidak menyalakan AI): `API_ANTHROPIC` (SDK resmi) atau `LANGGANAN_CLAUDE` (paket langganan Anthropic seperti Pro atau Max, lewat binary Claude Code, bukan Anthropic API) | Kontrak dari isi issue, kodenya belum ada: cakrawala-tumbuh/anjab-abk-backend#89 (`API_ANTHROPIC`); cakrawala-tumbuh/anjab-abk-backend#109 s.d. #112 dan cakrawala-tumbuh/anjab-abk-web-app#104 (pilihan lewat UI, `LANGGANAN_CLAUDE`) |
| Model | `claude-opus-5-5` dan effort `high` sebagai bawaan, dapat diubah admin lewat UI dengan alasan dan jejak event; ditinjau setelah EVAL. Jangan Fable/Mythos (K-4) | Skill `claude-api`; dokumen retensi |
| Jalur data | `API_ANTHROPIC`: backend/worker YPII → `api.anthropic.com`, satu pesan tanpa alat, tanpa Files API, Batch, Managed Agents, MCP connector. `LANGGANAN_CLAUDE`: backend/worker YPII → binary Claude Code (`claude -p`, tanpa alat) → Anthropic, bukan Anthropic API | cakrawala-tumbuh/anjab-abk-backend#89; dokumen retensi: Batch dan Files "stateful"; cakrawala-tumbuh/anjab-abk-backend#112 |
| Lokasi | `API_ANTHROPIC`: `inference_geo=us`, dikunci `allowed_inference_geos: ["us"]` di workspace (K-5). `LANGGANAN_CLAUDE`: `inference_geo`, ZDR, dan batas biaya workspace tidak berlaku; paket konsumen dapat memakai data untuk pelatihan bila pengaturan akun aktif, dengan retensi 5 tahun, atau 30 hari bila tidak aktif | Dokumen Data Residency; https://code.claude.com/docs/en/data-usage.md; cakrawala-tumbuh/anjab-abk-backend#112 |
| Retensi pihak Anthropic | Lihat K-6. Dua dokumen perlu dijelaskan | Lihat K-6 |
| Retensi kita | `AI_SIMPAN_MASUKAN=false`; hash dan keluaran disimpan selama kajian (K-7) | cakrawala-tumbuh/anjab-abk-backend#85; SPEC:248 |
| Boleh keluar | T0, lalu T1. T2 menunggu izin | K-3 |
| Tidak pernah keluar | WCP/DCS, konseling, murid, kredensial | PRM:6; SPEC:50, 233; PRD:56; cakrawala-tumbuh/anjab-abk-backend#86 |
| Izin pemrosesan | Dicatat per jenis sumber dalam `narasi_sumber` | OD:28; PRD:10 |
| Jalur manual | Tersedia sebelum AI dinyalakan, status sama | SOP:95; PG:12; SPEC:269 |
| Pemisahan lingkungan | Workspace dan kunci khusus produksi, pengembang tidak memegangnya | PG:14; PRD:56 |
| Pengaktif | K-8. Admin memilih penyedia lewat UI, tetapi itu bukan pengaktifan | cakrawala-tumbuh/anjab-abk-backend#110 |
| Insiden | PG:27: hentikan rilis, isolasi, simpan raw. Saklar cakrawala-tumbuh/anjab-abk-backend#88 | PG:27 |

Kolom "Boleh keluar" hanya menyebut tahap T0 dan T1. Baris atau bagian apa pun yang menyangkut T2 **menunggu pengesahan Yayasan/pemilik data** dan tidak boleh dibaca sebagai izin mengirim data pribadi.

### 3. Keputusan rinci

1. **K-4, model.** Opus 5.5 ($4/$20 per juta token), bawaan cakrawala-tumbuh/anjab-abk-backend#89 dan `claude-opus-5-5` dengan effort `high` sebagai nilai bawaan di cakrawala-tumbuh/anjab-abk-backend#109. Admin dapat mengubah model dan effort lewat UI dengan alasan, dan tiap perubahan tercatat sebagai event; nama model berawalan `claude-fable` atau `claude-mythos` ditolak. Hasil EVAL hanya berlaku untuk model yang diuji. Alternatif yang dipertimbangkan: Sonnet 5.5 ($2/$10), Haiku 5.5 ($0,10/$0,50), Fable 5.1 ($10/$50). Kesetiaan parafrasa adalah risiko utama (KAI:34), dan turun model baru masuk akal setelah EVAL mengukurnya. Fable 5.1 tidak dipilih: ia Covered Model yang mewajibkan retensi 30 hari. Ilustrasi biaya, bukan pengukuran: 5.000 token masuk + 2.000 token keluar pada Opus 5.5 kira-kira $0,06 per draf, belum termasuk thinking. Harga dan daftar model berasal dari skill `claude-api` (cache 6 Oktober 2026) dan **belum diverifikasi** ke sumber resmi.
1. **K-5, lokasi.** `us` (hanya AS, harga 1,1×), sehingga lokasi jadi satu dan dapat dinyatakan. Tidak ada opsi Indonesia atau Asia: dokumen menyatakan "Only `us` and `global` are available" untuk inference dan workspace geo hanya `us`. Pada opsi apa pun, data keluar dari Indonesia. Bagian ini perlu tinjauan hukum atas UU 27/2022, yang dijadikan dasar normatif oleh KD4:12. Pasal transfer lintas negara UU 27/2022 beserta dampak hukum K-5 **belum diverifikasi**.
1. **K-6, retensi pihak Anthropic.** Ketentuan standar cukup untuk T0 dan T1; permintaan ZDR lewat tim sales wajib dicoba sebelum T2. Syarat ini berlaku untuk `API_ANTHROPIC`. Untuk `LANGGANAN_CLAUDE`, K-6 **dikesampingkan** atas keputusan pemilik proyek, 5 November 2026; dicatat apa adanya, dan pengesampingan ini bukan persetujuan pemilik data (K-2). Yang terverifikasi di sumber untuk `API_ANTHROPIC`:
   - Pusat Privasi Anthropic (diperbarui 1 Juli 2026): input dan output dihapus otomatis "within 30 days of receipt or generation".
   - Dokumen "API and data retention": "Conversation content ... is not retained by default", kecuali Covered Models.
   - Konten yang ditandai sistem keamanan otomatis dapat disimpan hingga 2 tahun, bahkan dengan ZDR.
   - "Retained data is never used for model training without your express permission."
1. **Retensi pihak Anthropic: belum diverifikasi.** Bunyi kedua dokumen di atas tidak identik, dan tidak disimpulkan mana yang mengikat akun kita. Penegasan tertulis perlu diminta.
1. **Kontrak: belum diverifikasi.** Status organisasi, kontrak, dan perjanjian pemrosesan data YPII atau pelaksana: belum diverifikasi.
1. **ZDR: belum diverifikasi.** Kelayakan ZDR untuk akun kita belum diverifikasi.
1. **K-7, retensi di aplikasi.** Hasil AI disimpan sampai kajian ditutup, lalu dihapus atas keputusan pemilik data. `REPRODUCIBLE` (KN:41) butuh keluaran tersimpan, dan masa tetap yang dikarang pengembang dilarang SPEC:248. Masukan tetap tidak disimpan.
1. **K-8, pengaktif.** Satu keputusan tertulis user, dijalankan operator. Menyalakan butuh empat hal sekaligus: flag, daftar jenis sumber, `AI_FUNGSI_AKTIF` (ketiganya di deployment), dan penyedia siap lewat UI (`API_ANTHROPIC` dengan kunci, atau `LANGGANAN_CLAUDE` dengan CLI sudah masuk). Kunci induk enkripsi `AI_KREDENSIAL_KUNCI_INDUK` adalah satu-satunya rahasia baru di deployment. Mematikannya boleh admin kapan saja lewat saklar cakrawala-tumbuh/anjab-abk-backend#88.
1. **K-9, akun dan anggaran.** Untuk `API_ANTHROPIC`: workspace khusus dengan batas biaya, kunci produksi dipasang lewat UI dan tersimpan terenkripsi, dan kunci evaluasi tetap dari env proses di luar basis data. Jalur `LANGGANAN_CLAUDE` tidak memakai workspace. PG:14 meminta biaya per kasus, dan token sudah tercatat di `ai_run`. Tanpa kunci, EVAL tidak dapat dijalankan.
1. **K-10, pengalihan otomatis.** Mati saat memproses data riil, langsung ke jalur manual: `AI_REFUSAL_FALLBACK=false`. Dokumen menyatakan rute pengalihan "is not published for each model", dan halaman itu tidak menyebut retensi maupun geo (hitungan 0). Model mana yang menerima data tak bisa dinyatakan di muka. Ada pula catatan content-hash sekitar 1 jam untuk organisasi non-ZDR. Tidak mengubah cakrawala-tumbuh/anjab-abk-backend#89, hanya env. Tujuan pengalihan `fallbacks="default"` untuk Opus 5.5, dan apakah model tujuannya berkewajiban retensi: **belum diverifikasi**.
1. **K-12, nama orang dalam sumber.** `BLOKIR`, sumber ditolak utuh, untuk tahap T1 (sesuai bawaan cakrawala-tumbuh/anjab-abk-backend#86). Pakai KERING dulu untuk mengukur berapa dokumen tertolak. `SAMARKAN` butuh desain pembuka penanda dan baru relevan di T2. Tingkat salah-blok gerbang PII atas dokumen nyata belum diverifikasi (BE-5).
1. **K-13, penyimpanan teks sumber.** Tabel baru `narasi_sumber`, hanya teks tempelan (permukaan terkecil, hash stabil). Untuk T2 perlu dinilai ulang: KD4:5 meminta "vault berizin dan terenkripsi" untuk sumber lama. Enkripsi basis data produksi: **belum diverifikasi**.
1. **K-14, akun layanan.** Tidak ada grup Authentik baru; identitas proses `system:ai-worker`, tanpa token, batas ditegakkan struktural. Worker tak punya akses HTTP dan model tak punya alat (cakrawala-tumbuh/anjab-abk-backend#89). TEST-159 diuji dengan pendengar `before_flush` (cakrawala-tumbuh/anjab-abk-backend#90), ditambah uji bahwa penyerap hanya membuat versi, tidak pernah `narasi_event` tinjauan. Bila kelak worker perlu memanggil HTTP, dibuat grup deny-by-default. Catatan: "403" TEST-159 tidak bisa dipicu tanpa token, jadi kriterianya dibaca sebagai "tidak ada jalur", dan ini tafsir pelaksana.
1. **K-16, akses Claude lewat MCP.** Hanya metadata (status, hitungan). Membaca isi membuka jalur data kedua di luar gerbang PII, dan meninjau draf melanggar `NO_SELF_AUTH`.

### 4. Mode langganan

1. **Definisi.** `LANGGANAN_CLAUDE` memakai paket langganan Anthropic (Pro, Max, dan sejenisnya) lewat binary Claude Code. Ini bukan Anthropic API.
1. **Kredensial.** Aplikasi tidak menerima, menyimpan, membaca, atau mengantarai token langganan. Operator masuk lewat alur Anthropic sendiri (`claude auth login`) di dalam kontainer (cakrawala-tumbuh/anjab-abk-backend#112).
1. **Tanggung jawab.** Tanggung jawab atas pemakaian ada pada pemilik akun yang masuk.
1. **Audit.** `ai_run.penyedia` mencatat penyedia tiap run.
1. **Gerbang data.** Sama dengan `API_ANTHROPIC`, tanpa aturan per penyedia. Bawaan `SINTETIS` tetap; membukanya adalah keputusan terpisah (K-8).
1. **Isi dokumen Anthropic.** https://code.claude.com/docs/en/legal-and-compliance.md menyatakan: "Anthropic does not permit third-party developers to offer Claude.ai login into their own applications, or to route requests through Free, Pro, Max, or Ultra plan credentials on behalf of their users." Dokumen yang sama menyatakan pengembang produk "should use API key authentication", dan bahwa batas pemakaian paket "assume ordinary, individual usage". Ia juga menyatakan bahwa ketentuan itu tidak mencegah "an end user from signing in to the unmodified Claude Code binary with their own Claude subscription". Pemilik proyek memutuskan membangun jalur ini pada 5 November 2026 setelah mengetahui isi dokumen itu.
1. **Data.** https://code.claude.com/docs/en/data-usage.md menyatakan data akun Free, Pro, Max, dan Ultra dipakai melatih model bila pengaturan akun aktif, dengan retensi 5 tahun bila pengaturan itu aktif dan 30 hari bila tidak. K-6 dikesampingkan untuk mode ini (lihat K-6).
1. **Persetujuan pemilik data tetap terbuka.** K-2 berlaku untuk kedua mode. Pengesampingan K-6 tidak dibaca sebagai persetujuan pemilik data.
1. **Status.** Apakah pemakaian mode ini sesuai ketentuan Anthropic belum diverifikasi, dan dokumen ini tidak memutuskannya. Dokumen legal itu mengarahkan pertanyaan tentang metode autentikasi yang dibolehkan ke tim sales Anthropic.

### 5. Pagar yang tidak berubah oleh keputusan apa pun

AI tidak mengisi rating, WCP/DCS, persetujuan, izin, atau keputusan (RM:22; MX baris I15-I17; KAI:18). Jenis berawalan `WCP`, `DCS`, `KONSELING`, `MURID` selalu ditolak (cakrawala-tumbuh/anjab-abk-backend#86).

### 6. Syarat sebelum AKTIF-F1

| Syarat | Rujukan | Pemilik | Status |
|:--|:--|:--|:---|
| Baseline runtime | OD-05/14; RM:40 | Pelaksana | Backend #84, mcp #23 terbuka |
| OD-11 tertulis | OD:28 | Pelaksana | Dokumen ini; Kelompok B dicatat di atas |
| Izin atas dokumen yang dikirim | OD-01; PRD:66 | Pemilik data | Belum; K-2 |
| Jalur manual dan antrean hidup | SOP:95; PG:12 | Pelaksana | Belum dibangun |
| UAT relevan PASS: R11-003, 005, 009, 011, 013, 015, 016, TEST-080, TEST-159 | PU:26; RM:40 | Pelaksana + QA/sponsor | Semua `NOT_TESTED` |
| Pilot OD-13 | RM:40; PRD:66 Gate C | Metodolog | Bentrok: RM:40 menyebutnya gate, sementara OD:30 hanya melarang klaim. Usulan di sumber: untuk F1 internal tanpa klaim efisiensi cukup sampling negatif R11-016; pilot penuh sebelum F2 |

## Yang belum diverifikasi

Dicatat apa adanya dari §6 sumber; jangan dianggap fakta:

- Apakah pemakaian mode `LANGGANAN_CLAUDE` diizinkan Anthropic: belum diverifikasi, dan penerapan kalimat "unmodified Claude Code binary" pada arsitektur ini belum dinilai.
- Retensi pihak Anthropic untuk `API_ANTHROPIC`: dua dokumen berbunyi berbeda, belum diverifikasi mana yang mengikat.
- Kontrak, perjanjian pemrosesan data, dan status organisasi: belum diverifikasi.
- Kelayakan ZDR untuk akun kita: belum diverifikasi.
- Pasal transfer lintas negara UU 27/2022 dan dampak hukum K-5 dan K-6: belum diverifikasi.
- Tujuan pengalihan `fallbacks="default"`: belum diverifikasi.
- Enkripsi basis data produksi: belum diverifikasi.
- Perilaku nyata cakrawala-tumbuh/anjab-abk-backend#85 sampai #90 dan #109 sampai #112, serta cakrawala-tumbuh/anjab-abk-web-app#104, karena kodenya belum ada, serta dukungan `if/then` di structured output dan batas kompleksitas skema (diuji pada BE-6).

## Tanggung Jawab Pelaksanaan

Pemilik dokumen: Sponsor, data steward, dan security (OD:28). Pengaktifan AI mengikuti K-8. Pengesahan bagian data pribadi: Yayasan/pemilik data (K-2). Nama orang penanggung jawab tidak ditulis; hanya peran.

## Referensi

- Sumber tambahan versi 1.1: cakrawala-tumbuh/anjab-abk-backend#109, #110, #111, #112; cakrawala-tumbuh/anjab-abk-web-app#104; https://code.claude.com/docs/en/legal-and-compliance.md dan https://code.claude.com/docs/en/data-usage.md (dibaca 5 November 2026); keputusan pemilik proyek 5 November 2026.
- Sumber: `Rencana-Pemanggil-AI.md` versi 4 November 2026 (§3 Kelompok B, K-1 s.d. K-16, syarat AKTIF-F1, §6), disetujui user 4 November 2026; paket R1.1 `08_KENDALI_RILIS/01_OPEN_DECISIONS.md:28`.
- Pelacakan: `cakrawala-tumbuh/ypii-support#442`.
- Dokumen Terkait: [Keputusan Versi Status dan Lingkup Narasi](/docs/kebijakan/keputusan-versi-status-lingkup-narasi.md) (`KBJ-f18de0a3`).
