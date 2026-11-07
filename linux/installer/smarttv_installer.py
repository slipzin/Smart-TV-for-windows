#!/usr/bin/env python3
"""Read-only inventory for the Smart TV OS dual-boot installer."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

EFI_GUID = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"


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
    windows_candidates = []
    bitlocker_partitions = []
    partition_index: dict[str, dict[str, Any]] = {}

    for device in data.get("blockdevices", []):
        if device.get("type") != "disk":
            continue
        disk_path = device.get("path")
        disks.append({
            "name": device.get("name"),
            "path": disk_path,
            "size_bytes": device.get("size"),
            "model": device.get("model"),
            "transport": device.get("tran"),
            "partition_table": device.get("pttype"),
            "children": device.get("children", []),
        })

        def inspect_children(items: list[dict[str, Any]]) -> None:
            for item in items:
                path = item.get("path")
                if path:
                    partition_index[path] = {
                        "path": path,
                        "disk_path": disk_path,
                        "fstype": item.get("fstype"),
                        "label": item.get("label"),
                        "parttype": item.get("parttype"),
                    }
                fs = (item.get("fstype") or "").lower()
                label = (item.get("label") or "").lower()
                if fs == "ntfs" or "windows" in label or "microsoft" in label:
                    windows_candidates.append({
                        "path": path,
                        "fstype": item.get("fstype"),
                        "label": item.get("label"),
                        "disk_path": disk_path,
                    })
                if fs in {"bitlocker", "bitlk"}:
                    bitlocker_partitions.append(path)
                inspect_children(item.get("children") or [])

        inspect_children(device.get("children") or [])

    uefi = Path("/sys/firmware/efi").exists()
    windows_entries: list[str] = []
    windows_installations: list[dict[str, Any]] = []
    windows_unmapped_entries: list[str] = []
    if shutil.which("os-prober"):
        probe = subprocess.run(
            ["os-prober"], text=True, capture_output=True, timeout=30
        )
        # Never treat partial stdout from a failed probe as proof of Windows.
        if probe.returncode == 0:
            for line in probe.stdout.splitlines():
                if "windows" not in line.lower() and "microsoft" not in line.lower():
                    continue
                fields = line.split(":")
                raw_device = fields[0] if fields else ""
                # os-prober may append @/path/to/boot. Only the device before
                # that suffix can be matched against the current lsblk snapshot.
                probe_device = raw_device.split("@", 1)[0]
                partition = partition_index.get(probe_device)
                if not partition:
                    windows_unmapped_entries.append(line)
                    continue
                # A boot-manager entry alone is insufficient if this disk has
                # no NTFS Windows volume in the same inventory snapshot.
                same_disk_ntfs = any(
                    candidate.get("disk_path") == partition["disk_path"]
                    and (candidate.get("fstype") or "").lower() == "ntfs"
                    for candidate in windows_candidates
                )
                if not same_disk_ntfs:
                    windows_unmapped_entries.append(line)
                    continue
                windows_entries.append(line)
                windows_installations.append({
                    "entry": line,
                    "boot_partition_path": probe_device,
                    "disk_path": partition["disk_path"],
                })

    efi_partitions = []

    def visit(items: list[dict[str, Any]], disk_path: str | None) -> None:
        for item in items:
            parttype = (item.get("parttype") or "").lower()
            if parttype == EFI_GUID:
                efi_partitions.append({
                    "path": item.get("path"),
                    "disk_path": disk_path,
                    "size_bytes": item.get("size"),
                    "fstype": item.get("fstype"),
                    "label": item.get("label"),
                    "parttype": parttype,
                })
            visit(item.get("children") or [], disk_path)

    for device in data.get("blockdevices", []):
        if device.get("type") == "disk":
            visit(device.get("children") or [], device.get("path"))

    windows_disk_paths = sorted({
        item["disk_path"] for item in windows_installations if item.get("disk_path")
    })
    warnings = [
        "Esta etapa apenas inspeciona o computador; nenhuma alteração no disco é permitida.",
        "BitLocker não pode ser certificado como desativado por esta inspeção; a confirmação no Windows é obrigatória.",
        "A validação de Windows exige que o os-prober corresponda a uma partição conhecida e a um volume NTFS no mesmo disco.",
    ]
    if not uefi:
        warnings.append("Inicialização UEFI não detectada. O instalador deve parar nesta condição.")
    if not windows_entries:
        warnings.append("Windows 10/11 não foi confirmado com correspondência entre os-prober e lsblk; não basta encontrar uma partição NTFS.")
    if windows_unmapped_entries:
        warnings.append("Há entradas do os-prober que não puderam ser associadas com segurança a um disco; elas não foram aceitas como confirmação.")
    if windows_candidates and not windows_entries:
        warnings.append("Há partições NTFS candidatas, mas elas não comprovam uma instalação Windows.")
    if bitlocker_partitions:
        warnings.append("Foi identificado um volume BitLocker; a instalação deve permanecer bloqueada.")
    if not efi_partitions:
        warnings.append("Nenhuma partição EFI System Partition foi confirmada pelo GUID GPT correto.")

    return {
        "product": "Smart TV OS Installer Preflight",
        "mode": "read-only",
        "uefi": uefi,
        "windows_detected": windows_entries,
        "windows_installations": windows_installations,
        "windows_disk_paths": windows_disk_paths,
        "windows_unmapped_entries": windows_unmapped_entries,
        "windows_candidates": windows_candidates,
        "bitlocker_detected": bool(bitlocker_partitions),
        "bitlocker_partitions": bitlocker_partitions,
        "efi_partitions": efi_partitions,
        "disks": disks,
        "warnings": warnings,
        "installation_allowed": False,
        "reason": "A interface e o planejamento ainda não executam operações no disco.",
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
    except (RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(f"Falha na inspeção: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("SMART TV OS — VERIFICAÇÃO DO COMPUTADOR")
        print(f"Modo: {report['mode']} | UEFI: {'sim' if report['uefi'] else 'não'}")
        print(f"Windows confirmado: {'sim' if report['windows_detected'] else 'não'}")
        print(f"Discos com Windows confirmado: {', '.join(report['windows_disk_paths']) or 'nenhum'}")
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
