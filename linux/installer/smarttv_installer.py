#!/usr/bin/env python3
"""Read-only inventory for the Smart TV OS dual-boot installer.

Windows identification here is preliminary evidence only. It is not sufficient
to authorize a future disk-writing installer: the Windows system volume and
BitLocker state must be independently verified before any write operation.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

EFI_GUID = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
MS_BASIC_DATA_GUID = "ebd0a0a2-b9e5-4433-87c0-68b6b72699c7"


def run_json(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    return json.loads(result.stdout)


def _is_windows_chain(fields: list[str]) -> bool:
    """Accept only an os-prober Windows chain entry, not arbitrary text matches."""
    return (
        len(fields) >= 4
        and "windows" in fields[1].lower()
        and fields[2].strip().lower() == "windows"
        and fields[3].strip().lower() == "chain"
    )


def inspect_system() -> dict[str, Any]:
    if not shutil.which("lsblk"):
        raise RuntimeError("Comando lsblk não encontrado.")
    data = run_json([
        "lsblk", "--json", "--bytes", "--output",
        "NAME,PATH,TYPE,SIZE,FSTYPE,LABEL,UUID,PARTUUID,MOUNTPOINTS,PTTYPE,PARTTYPE,MODEL,TRAN"
    ])

    disks = []
    windows_candidates = []
    windows_volume_candidates = []
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
                parttype = (item.get("parttype") or "").lower()
                if path:
                    partition_index[path] = {
                        "path": path,
                        "disk_path": disk_path,
                        "fstype": item.get("fstype"),
                        "label": item.get("label"),
                        "parttype": parttype,
                    }
                fs = (item.get("fstype") or "").lower()
                label = (item.get("label") or "").lower()
                if fs == "ntfs" or "windows" in label or "microsoft" in label:
                    candidate = {
                        "path": path,
                        "fstype": fs,
                        "label": item.get("label"),
                        "parttype": parttype,
                        "disk_path": disk_path,
                        "size_bytes": item.get("size"),
                    }
                    windows_candidates.append(candidate)
                    # This is only a volume candidate. It does not prove that
                    # the volume contains a bootable Windows installation.
                    if fs == "ntfs" and parttype == MS_BASIC_DATA_GUID:
                        windows_volume_candidates.append(candidate)
                if fs in {"bitlocker", "bitlk"}:
                    bitlocker_partitions.append(path)
                inspect_children(item.get("children") or [])

        inspect_children(device.get("children") or [])

    uefi = Path("/sys/firmware/efi").exists()
    windows_entries: list[str] = []
    windows_installations: list[dict[str, Any]] = []
    windows_unmapped_entries: list[str] = []
    windows_ambiguous_entries: list[str] = []
    os_prober_available = bool(shutil.which("os-prober"))
    os_prober_succeeded = False

    if os_prober_available:
        probe = subprocess.run(
            ["os-prober"], text=True, capture_output=True, timeout=30
        )
        # Never treat partial stdout from a failed probe as proof of Windows.
        os_prober_succeeded = probe.returncode == 0
        if os_prober_succeeded:
            for line in probe.stdout.splitlines():
                fields = line.split(":")
                if not _is_windows_chain(fields):
                    continue
                raw_device = fields[0].strip()
                # os-prober may append @/path/to/boot.
                probe_device = raw_device.split("@", 1)[0]
                partition = partition_index.get(probe_device)
                if not partition:
                    windows_unmapped_entries.append(line)
                    continue

                candidates_on_disk = [
                    candidate for candidate in windows_volume_candidates
                    if candidate.get("disk_path") == partition["disk_path"]
                ]
                # More than one NTFS Basic Data volume is ambiguous. Never
                # guess which one is the Windows system volume.
                if len(candidates_on_disk) != 1:
                    windows_ambiguous_entries.append(line)
                    continue
                volume = candidates_on_disk[0]

                # The boot-chain partition must be either the actual unique
                # NTFS Basic Data candidate or a valid FAT EFI System Partition
                # on the same physical disk. Recovery and arbitrary data
                # partitions are not accepted as Windows boot evidence.
                is_same_windows_volume = (
                    probe_device == volume.get("path")
                    and partition.get("parttype") == MS_BASIC_DATA_GUID
                    and (partition.get("fstype") or "").lower() == "ntfs"
                )
                is_efi_boot_partition = (
                    partition.get("parttype") == EFI_GUID
                    and (partition.get("fstype") or "").lower() == "vfat"
                )
                if not (is_same_windows_volume or is_efi_boot_partition):
                    windows_unmapped_entries.append(line)
                    continue

                windows_entries.append(line)
                windows_installations.append({
                    "entry": line,
                    "boot_partition_path": probe_device,
                    "windows_volume_path": volume["path"],
                    "disk_path": partition["disk_path"],
                    "evidence": "os-prober-windows-chain+single-ntfs-basic-data",
                    "preliminary_only": True,
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
        "A associação os-prober + NTFS único é uma pré-detecção, não prova definitiva de uma instalação Windows funcional.",
        "Antes de qualquer futura escrita, será necessária verificação somente leitura do conteúdo do volume Windows e da configuração BCD.",
        "BitLocker não pode ser certificado como desativado por esta inspeção; a confirmação no Windows não substitui uma verificação técnica.",
    ]
    if not uefi:
        warnings.append("Inicialização UEFI não detectada. O instalador deve parar nesta condição.")
    if not os_prober_available:
        warnings.append("os-prober não está instalado; Windows não pode ser pré-detectado.")
    elif not os_prober_succeeded:
        warnings.append("os-prober falhou; qualquer saída parcial foi ignorada.")
    if not windows_entries:
        warnings.append("Nenhuma cadeia Windows foi associada a uma EFI válida ou ao único volume NTFS Basic Data do mesmo disco.")
    if windows_unmapped_entries:
        warnings.append("Há entradas do os-prober sem associação segura; elas não foram aceitas.")
    if windows_ambiguous_entries:
        warnings.append("Há mais de um volume NTFS Basic Data no disco; a associação do Windows é ambígua e foi bloqueada.")
    if windows_candidates and not windows_entries:
        warnings.append("Há partições candidatas, mas elas não comprovam uma instalação Windows.")
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
        "windows_ambiguous_entries": windows_ambiguous_entries,
        "windows_candidates": windows_candidates,
        "windows_volume_candidates": windows_volume_candidates,
        "os_prober_available": os_prober_available,
        "os_prober_succeeded": os_prober_succeeded,
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
        print(f"Pré-detecção Windows: {'sim' if report['windows_detected'] else 'não confirmada'}")
        print(f"Discos com pré-detecção Windows: {', '.join(report['windows_disk_paths']) or 'nenhum'}")
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
