---
title: "Keputusan Versi: Nama Status dan Kunci Lingkup Narasi"
description: "Catatan keputusan versi terkendali untuk nama status narasi, jenis sumber, dan kunci lingkup kasus narasi (K-15)."
published: true
date: 2026-11-04T00:00:00.000Z
tags: kebijakan, narasi
editor: markdown
dateCreated: 2026-11-04T00:00:00.000Z
doc_id: "KBJ-f18de0a3"
category: "kebijakan"
owner: "Sponsor, data steward, security"
status: "aktif"
version: "1.0"
effective_date: "2026-11-04"
last_reviewed: "2026-11-04"
related_docs: ["KBJ-2ebb120b"]
---

# Keputusan Versi: Nama Status dan Kunci Lingkup Narasi

Dokumen ini mencatat keputusan K-15 yang disetujui user pada 4 November 2026. RM:8 mewajibkan keputusan versi terkendali untuk nama status; dokumen ini adalah catatannya. Dokumen ini tidak menyalakan AI.

## Latar Belakang

Dua dokumen rujukan memakai nama berbeda untuk hal yang sama. Aturan otoritas: kebijakan narasi berada di atas kontrak sistem (RM:8), KAI:23 mengalahkan KN:9 yang berlabel "disarankan", dan KAI:29 menyatakan bahwa istilah status Inggris adalah enum internal. Urutan statusnya sama di kedua dokumen; yang berbeda hanya nama.

## Tujuan

Menetapkan nama status, jenis sumber, event, dan kunci lingkup narasi yang dipakai, agar implementasi tidak memilih sendiri.

## Ruang Lingkup

Berlaku untuk mesin status narasi dan kunci lingkup kasus narasi. Tidak mencakup pemberitahuan kepada Tim (K-17) dan tidak mencakup kebijakan pemakaian AI (lihat dokumen terkait).

## Pernyataan Kebijakan

1. **Daftar 14 status** (KAI:23), yaitu `SOURCE_CHECKED`, `AI_DRAFT`, `NEED_FACT`, `TEAM_REVIEW`, `TEAM_VERIFIED`, `SUBJECT_REVIEW`, `SUBJECT_CONFIRMED`, `SUBJECT_CORRECTION`, `SUBJECT_REJECTED`, `SUBJECT_UNCERTAIN`, `FINAL_TEAM_REVIEW`, `RELEASED_FACT`, `RELEASED_LIMITED`, `RETURN_FOR_CLARIFICATION`.
1. **Jenis sumber** memakai `F1_FORMAL..F5_RESEARCH` (SN-D, SQL:404), bukan `F1_FORMAL_DOC` (KN:7).
1. **Event** mengikuti SQL:430-432.
1. **Kunci lingkup** memakai kolom eksplisit: `instrument_id`, `field_key`, `peran_ref`, `periode`, `sekolah_id` (null), `assignment_ref` (null), `target_subject_ref` (null), `konteks_kode` (null). Kunci ini **tidak memakai `context_id`**. `context_id` hanya muncul di API dan DDL konseptual; grain sudah ada di KN:5, dan KN:17 meminta `scope_id` serta `period_id`. Jangan memetakannya ke K-NN: K-NN adalah tema usulan, bukan lingkup.
1. **Aturan menang:** KAI:23 menang atas KN:9 menurut RM:8.
1. **Bila Tim kelak memberi definisi lain,** cukup pemetaan, tanpa migrasi perilaku.

## Tanggung Jawab Pelaksanaan

Pemilik dokumen: Sponsor, data steward, dan security. Nama orang penanggung jawab tidak ditulis; hanya peran.

## Referensi

- Sumber: `Rencana-Pemanggil-AI.md` versi 4 November 2026 (K-15), disetujui user 4 November 2026.
- Pelacakan: `cakrawala-tumbuh/ypii-support#442`.
- Dokumen Terkait: [OD-11 Kebijakan Pemakaian AI, Versi 1](/docs/kebijakan/od-11-kebijakan-ai.md) (`KBJ-2ebb120b`).
