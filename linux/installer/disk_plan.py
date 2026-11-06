"""Fail-closed disk plan validation for the Smart TV OS installer.

This module only validates a proposed plan. It NEVER executes partitioning,
formatting, mounting, filesystem creation, or bootloader changes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

GIB = 1024 ** 3
MIN_ROOT_BYTES = 40 * GIB
EFI_GUID = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"


class UnsafeInstallPlan(ValueError):
    """Raised when a proposed disk plan cannot be proven safe."""


@dataclass(frozen=True)
class InstallPlan:
    disk_path: str
    table: str
    boot_mode: str
    free_region_start: int
    free_region_bytes: int
    root_bytes: int
    efi_partition_path: str
    format_efi: bool = False
    format_existing_partitions: bool = False
    windows_present: bool = False
    bitlocker_detected: bool = False
    user_confirmed: bool = False


def validate_install_plan(plan: InstallPlan, inventory: dict[str, Any]) -> dict[str, Any]:
    """Validate a plan against a fresh lsblk-like inventory; no side effects."""
    if plan.boot_mode.lower() != "uefi":
        raise UnsafeInstallPlan("Somente inicialização UEFI é aceita nesta versão.")
    if plan.table.lower() != "gpt":
        raise UnsafeInstallPlan("O disco de destino precisa usar GPT.")
    if not plan.disk_path.startswith("/dev/"):
        raise UnsafeInstallPlan("Dispositivo de destino inválido.")
    if plan.format_efi or plan.format_existing_partitions:
        raise UnsafeInstallPlan("É proibido formatar a EFI ou partições existentes.")
    if not plan.user_confirmed:
        raise UnsafeInstallPlan("A revisão final do usuário ainda não foi confirmada.")
    if plan.windows_present and plan.bitlocker_detected:
        raise UnsafeInstallPlan(
            "BitLocker detectado: suspenda a proteção e confirme a chave de recuperação no Windows antes de continuar."
        )
    if plan.free_region_start < 1 * 1024 * 1024:
        raise UnsafeInstallPlan("Início da região livre inválido ou não alinhado.")
    if plan.free_region_bytes < MIN_ROOT_BYTES:
        raise UnsafeInstallPlan("A região não alocada precisa ter pelo menos 40 GiB.")
    if plan.root_bytes < MIN_ROOT_BYTES or plan.root_bytes > plan.free_region_bytes:
        raise UnsafeInstallPlan("Tamanho da partição raiz inválido para a região livre.")

    disks = inventory.get("disks", [])
    disk = next((d for d in disks if d.get("path") == plan.disk_path), None)
    if disk is None:
        raise UnsafeInstallPlan("Disco não encontrado na inspeção atual.")
    if (disk.get("partition_table") or "").lower() != "gpt":
        raise UnsafeInstallPlan("A tabela de partições mudou desde a inspeção.")

    efi = next(
        (p for p in inventory.get("efi_partitions", [])
         if p.get("path") == plan.efi_partition_path),
        None,
    )
    if efi is None:
        raise UnsafeInstallPlan("Partição EFI existente não foi confirmada.")
    if efi.get("fstype") != "vfat":
        raise UnsafeInstallPlan("A partição EFI não está em FAT32; operação bloqueada.")

    return {
        "valid": True,
        "disk": plan.disk_path,
        "partition_table": "gpt",
        "boot_mode": "uefi",
        "target": "unallocated_space_only",
        "root_bytes": plan.root_bytes,
        "efi": {"path": plan.efi_partition_path, "format": False, "reuse": True},
        "existing_partitions_modified": False,
        "execution_enabled": False,
        "message": "Plano validado em modo de simulação; execução de escrita continua desabilitada.",
    }
