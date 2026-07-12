#!/usr/bin/env python3
"""Ekstrak master data Task Inventory dari Task Bank v2_19.

Sumber: sheet `05_Raw_Task_Migration` pada Task_Bank_Complete_AllRoles_v2_19.xlsx.
Skrip ini murni membaca — tidak menyentuh database maupun jaringan, aman dijalankan
berulang. Lihat rencana-revisi-master-data-task-inventory.md di root repo untuk
konteks & keputusan lengkap di balik setiap aturan di bawah.

Pemetaan kolom sumber -> field catalog:
    D  Role_Name            -> kategori_jabatan
    I  Duty_Area            -> tugas_pokok
    J  Sub_Duty              -> detil_tugas (boleh kosong)
    L  Task_Statement_5C     -> uraian_tugas
    B  Task_ID               -> kode
    V  Preliminary_VA_Category  -> std_va_type
    Y  Formal_Actual         -> std_sumber_bukti
    Z  Baseline_Peak         -> std_kondisi (direkonstruksi utk baris terkontaminasi)
    AA Frequency             -> std_frekuensi_teks
    AB Duration_Estimate     -> std_durasi_per_kali (teks bebas)
    AR Final_Decision        -> baris "Retire" dibuang

Kolom G (Jenjang) diabaikan -> `unit` diisi konstanta "ALL" (lihat keputusan #2).

265 baris kolom Z terkontaminasi nilai frekuensi (bukan nilai kondisi Baseline/Peak).
Nilai yang benar sudah direkonstruksi sebelumnya (lihat §5.2 rencana) dan disimpan di
`tebakan_kondisi_kolom_Z.csv` -- skrip ini memakainya sebagai lookup, bukan menghitung
ulang, supaya hasilnya deterministik & sama persis dengan yang sudah divalidasi silang.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import openpyxl

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_XLSX = SCRIPT_DIR / "Task_Bank_Complete_AllRoles_v2_19 (1).xlsx"
DEFAULT_SHEET = "05_Raw_Task_Migration"
DEFAULT_TEBAKAN_CSV = SCRIPT_DIR / "tebakan_kondisi_kolom_Z.csv"
DEFAULT_OUT_JSON = (
    SCRIPT_DIR.parent.parent
    / "anjab-abk-backend"
    / "src"
    / "anjab_abk_backend"
    / "taskinv"
    / "data"
    / "task_catalog.json"
)
DEFAULT_OUT_ANOMALI = SCRIPT_DIR / "anomali_task_bank.csv"

UNIT_CONST = "ALL"

VA_TYPE_DOMAIN = {"VA-Core", "VA-Enable", "NVA-Residual", "Context-Dependent", "Needs Validation"}
SUMBER_BUKTI_DOMAIN = {"Formal", "Aktual", "Keduanya"}
KONDISI_DOMAIN = {"Baseline", "Peak", "Both"}

# Baris Y = "Perlu Validasi" tanpa padanan di tebakan CSV -> disalin dari induk kanonik
# yang ditunjuk eksplisit oleh Reviewer_Notes (lihat §5.2 rencana).
Y_CANONICAL_OVERRIDE = {
    "STSAR-ALL-LEAD-026": "Formal",
    "STSAR-ALL-LEAD-027": "Formal",
}


def load_tebakan(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return {row["Task_ID"]: row for row in csv.DictReader(f)}


def load_rows(xlsx_path: Path, sheet_name: str) -> list[dict[str, Any]]:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb[sheet_name]
    rows_iter = ws.iter_rows(values_only=True)
    header = next(rows_iter)
    idx = {h: i for i, h in enumerate(header)}
    required = [
        "Task_ID",
        "Role_Name",
        "Duty_Area",
        "Sub_Duty",
        "Task_Statement_5C",
        "Preliminary_VA_Category",
        "Formal_Actual",
        "Baseline_Peak",
        "Frequency",
        "Duration_Estimate",
        "Final_Decision",
    ]
    missing = [c for c in required if c not in idx]
    if missing:
        raise SystemExit(f"Kolom wajib tidak ditemukan di sheet: {missing}")
    out = []
    for row in rows_iter:
        if row is None or all(v is None for v in row):
            continue
        out.append({col: row[i] for col, i in idx.items()})
    return out


def extract(
    xlsx_path: Path, sheet_name: str, tebakan_csv: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Kembalikan (catalog_items, anomali_rows, ringkasan)."""
    raw_rows = load_rows(xlsx_path, sheet_name)
    tebakan = load_tebakan(tebakan_csv)

    catalog: list[dict[str, Any]] = []
    anomali: list[dict[str, Any]] = []
    urutan_counter: Counter[str] = Counter()
    seen_kode: set[str] = set()

    n_retire = 0
    n_va_out_of_domain = 0
    n_sumber_bukti_reconstructed = 0
    n_kondisi_reconstructed = 0

    for row in raw_rows:
        final_decision = (row.get("Final_Decision") or "").strip()
        kode = (row.get("Task_ID") or "").strip()

        if final_decision == "Retire":
            n_retire += 1
            anomali.append(
                {
                    "kode": kode,
                    "role_name": row.get("Role_Name"),
                    "jenis": "DIBUANG_RETIRE",
                    "detail": "Final_Decision = Retire",
                }
            )
            continue

        if not kode:
            continue
        if kode in seen_kode:
            anomali.append(
                {
                    "kode": kode,
                    "role_name": row.get("Role_Name"),
                    "jenis": "KODE_DUPLIKAT",
                    "detail": "Task_ID muncul >1 kali di baris non-Retire, baris kedua dibuang",
                }
            )
            continue
        seen_kode.add(kode)

        role_name = (row.get("Role_Name") or "").strip()
        duty_area = (row.get("Duty_Area") or "").strip()
        sub_duty = (row.get("Sub_Duty") or "").strip()
        statement = (row.get("Task_Statement_5C") or "").strip()

        va_type = (row.get("Preliminary_VA_Category") or "").strip()
        if va_type not in VA_TYPE_DOMAIN:
            n_va_out_of_domain += 1
            anomali.append(
                {
                    "kode": kode,
                    "role_name": role_name,
                    "jenis": "VA_TYPE_DI_LUAR_DOMAIN",
                    "detail": f"Preliminary_VA_Category={va_type!r} tidak dikenal, dibiarkan apa adanya",
                }
            )

        sumber_bukti = (row.get("Formal_Actual") or "").strip()
        if sumber_bukti not in SUMBER_BUKTI_DOMAIN:
            override = Y_CANONICAL_OVERRIDE.get(kode)
            if override:
                anomali.append(
                    {
                        "kode": kode,
                        "role_name": role_name,
                        "jenis": "SUMBER_BUKTI_DISALIN_DARI_INDUK",
                        "detail": f"Formal_Actual={sumber_bukti!r} -> {override!r} (induk kanonik STSAR-ALL-LEAD-025)",
                    }
                )
                sumber_bukti = override
                n_sumber_bukti_reconstructed += 1
            else:
                anomali.append(
                    {
                        "kode": kode,
                        "role_name": role_name,
                        "jenis": "SUMBER_BUKTI_DI_LUAR_DOMAIN_TANPA_PADANAN",
                        "detail": f"Formal_Actual={sumber_bukti!r} tidak dikenal & tanpa override, dibiarkan apa adanya",
                    }
                )

        kondisi_asli = (row.get("Baseline_Peak") or "").strip()
        frekuensi_asli = (row.get("Frequency") or "").strip()
        kondisi = kondisi_asli
        frekuensi = frekuensi_asli
        tebakan_row = tebakan.get(kode)
        if tebakan_row:
            kondisi = tebakan_row["kondisi_final"]
            frekuensi = tebakan_row["frekuensi_final"]
            n_kondisi_reconstructed += 1
            anomali.append(
                {
                    "kode": kode,
                    "role_name": role_name,
                    "jenis": f"KONDISI_DIREKONSTRUKSI_{tebakan_row['kasus']}",
                    "detail": (
                        f"Z_asli={tebakan_row['Z_asli']!r} AA_asli={tebakan_row['AA_asli']!r} -> "
                        f"kondisi={kondisi!r} frekuensi={frekuensi!r} "
                        f"(keyakinan={tebakan_row['keyakinan']}, metode={tebakan_row['metode']}, "
                        f"perlu_review={tebakan_row['perlu_review']})"
                    ),
                }
            )
        elif kondisi not in KONDISI_DOMAIN:
            anomali.append(
                {
                    "kode": kode,
                    "role_name": role_name,
                    "jenis": "KONDISI_DI_LUAR_DOMAIN_TANPA_TEBAKAN",
                    "detail": f"Baseline_Peak={kondisi!r} tidak dikenal & tanpa entri tebakan, dibiarkan apa adanya",
                }
            )

        durasi = (row.get("Duration_Estimate") or "").strip()

        urutan_counter[role_name] += 1

        catalog.append(
            {
                "kode": kode,
                "unit": UNIT_CONST,
                "kategori_jabatan": role_name,
                "tugas_pokok": duty_area,
                "detil_tugas": sub_duty,
                "uraian_tugas": statement,
                "urutan": urutan_counter[role_name],
                "std_va_type": va_type or None,
                "std_sumber_bukti": sumber_bukti or None,
                "std_kondisi": kondisi or None,
                "std_frekuensi_teks": frekuensi or None,
                "std_durasi_per_kali": durasi or None,
            }
        )

    ringkasan = {
        "baris_dibaca": len(raw_rows),
        "baris_retire_dibuang": n_retire,
        "uraian_tugas_dihasilkan": len(catalog),
        "va_type_di_luar_domain": n_va_out_of_domain,
        "sumber_bukti_direkonstruksi": n_sumber_bukti_reconstructed,
        "kondisi_direkonstruksi": n_kondisi_reconstructed,
        "jabatan_unik": len({it["kategori_jabatan"] for it in catalog}),
        "tugas_pokok_unik": len({it["tugas_pokok"] for it in catalog}),
        "detil_tugas_unik": len(
            {(it["tugas_pokok"], it["detil_tugas"]) for it in catalog if it["detil_tugas"]}
        ),
    }
    return catalog, anomali, ringkasan


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    parser.add_argument("--sheet", default=DEFAULT_SHEET)
    parser.add_argument("--tebakan-csv", type=Path, default=DEFAULT_TEBAKAN_CSV)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-anomali-csv", type=Path, default=DEFAULT_OUT_ANOMALI)
    args = parser.parse_args()

    if not args.xlsx.exists():
        raise SystemExit(f"Berkas xlsx tidak ditemukan: {args.xlsx}")
    if not args.tebakan_csv.exists():
        raise SystemExit(f"Berkas tebakan CSV tidak ditemukan: {args.tebakan_csv}")

    catalog, anomali, ringkasan = extract(args.xlsx, args.sheet, args.tebakan_csv)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
        f.write("\n")

    with args.out_anomali_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["kode", "role_name", "jenis", "detail"])
        writer.writeheader()
        writer.writerows(anomali)

    print("=== Ringkasan ekstraksi Task Bank v2_19 ===", file=sys.stderr)
    for k, v in ringkasan.items():
        print(f"  {k}: {v}", file=sys.stderr)
    print(f"Output JSON  -> {args.out_json}", file=sys.stderr)
    print(f"Output CSV   -> {args.out_anomali_csv} ({len(anomali)} baris)", file=sys.stderr)


if __name__ == "__main__":
    main()
