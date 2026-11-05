#!/usr/bin/env python3
"""Smart TV OS installer preflight. This module is intentionally read-only.

It inventories disks and boot mode and produces a safety report. It does not
partition, format, mount, install packages, or modify boot entries.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_json(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    return json.loads(result.stdout)


def inspect_system() -> dict[str, Any]:
    if not shutil.which("lsblk"):
        raise RuntimeError("Comando lsblk não encontrado.")
    data = run_json([
        "lsblk", "--json", "--bytes", "--output",
        "NAME,PATH,TYPE,SIZE,FSTYPE,LABEL,UUID,PARTUUID,MOUNTPOINTS,PTTYPE,PARTTYPE,MODEL,TRAN"
    ])
    disks = []
    for device in data.get("blockdevices", []):
        if device.get("type") != "disk":
            continue
        disks.append({
            "name": device.get("name"),
            "path": device.get("path"),
            "size_bytes": device.get("size"),
            "model": device.get("model"),
            "transport": device.get("tran"),
            "partition_table": device.get("pttype"),
            "children": device.get("children", []),
        })

    uefi = Path("/sys/firmware/efi").exists()
    windows_entries = []
    if shutil.which("os-prober"):
        probe = subprocess.run(["os-prober"], text=True, capture_output=True)
        for line in probe.stdout.splitlines():
            if "windows" in line.lower() or "microsoft" in line.lower():
                windows_entries.append(line)

    efi_partitions = []
    def visit(items):
        for item in items:
            parttype = (item.get("parttype") or "").lower()
            fstype = (item.get("fstype") or "").lower()
            if parttype == "c12a7328-f81f-11d2-ba4b-00a0c93ec93b" or fstype == "vfat" and item.get("parttype"):
                efi_partitions.append({
                    "path": item.get("path"),
                    "size_bytes": item.get("size"),
                    "fstype": item.get("fstype"),
                    "label": item.get("label"),
                    "parttype": item.get("parttype"),
                })
            visit(item.get("children") or [])
    visit(data.get("blockdevices", []))

    warnings = [
        "Esta etapa apenas inspeciona o computador; nenhuma alteração no disco é permitida.",
        "A presença de espaço livre/não alocado ainda precisa ser confirmada por leitura de geometria de partições.",
    ]
    if not uefi:
        warnings.append("Inicialização UEFI não detectada. O instalador deve parar nesta condição.")
    if not windows_entries:
        warnings.append("Nenhuma instalação Windows foi confirmada pelo os-prober.")
    return {
        "product": "Smart TV OS Installer Preflight",
        "mode": "read-only",
        "uefi": uefi,
        "windows_detected": windows_entries,
        "efi_partitions": efi_partitions,
        "disks": disks,
        "warnings": warnings,
        "installation_allowed": False,
        "reason": "Instalação e particionamento permanecem bloqueados nesta versão.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnóstico somente leitura do instalador Smart TV OS")
    parser.add_argument("--inspect", action="store_true", help="Inspeciona discos e inicialização sem modificá-los")
    parser.add_argument("--json", action="store_true", help="Imprime o relatório em JSON")
    args = parser.parse_args()
    if not args.inspect:
        parser.print_help()
        return 0
    try:
        report = inspect_system()
    except (RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"Falha na inspeção: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("SMART TV OS — VERIFICAÇÃO DO COMPUTADOR")
        print(f"Modo: {report['mode']} | UEFI: {'sim' if report['uefi'] else 'não'}")
        print(f"Windows detectado: {'sim' if report['windows_detected'] else 'não confirmado'}")
        print(f"Discos encontrados: {len(report['disks'])}")
        for disk in report["disks"]:
            print(f"  {disk.get('path')} — {disk.get('model') or 'modelo desconhecido'} — {disk.get('size_bytes')} bytes")
        print("\nINSTALAÇÃO BLOQUEADA")
        print(report["reason"])
        for warning in report["warnings"]:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
