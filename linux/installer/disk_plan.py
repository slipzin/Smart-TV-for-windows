"""Fail-closed disk plan validation for the Smart TV OS installer.

This module only validates a proposed plan. It NEVER executes partitioning,
formatting, mounting, filesystem creation, or bootloader changes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

GIB = 1024 ** 3
MIB = 1024 ** 2
MIN_ROOT_BYTES = 40 * GIB
MIN_EFI_BYTES = 100 * MIB
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
    windows_pre_detected: bool = False
    bitlocker_detected: bool = False
    bitlocker_acknowledged_by_user: bool = False
    user_confirmed: bool = False


def validate_install_plan(plan: InstallPlan, inventory: dict[str, Any]) -> dict[str, Any]:
    """Validate a plan against a fresh inventory and exact free-space geometry."""
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
    if not plan.windows_pre_detected:
        raise UnsafeInstallPlan("A pré-detecção Windows não foi associada com segurança; instalação bloqueada.")
    confirmed_windows_disks = {
        item.get("disk_path")
        for item in inventory.get("windows_installations", [])
        if item.get("disk_path")
    }
    if plan.disk_path not in confirmed_windows_disks:
        raise UnsafeInstallPlan(
            "A pré-detecção Windows não foi associada ao disco selecionado; dual boot neste disco está bloqueado."
        )
    if plan.windows_present and not plan.bitlocker_acknowledged_by_user:
        raise UnsafeInstallPlan(
            "O estado do BitLocker não pode ser verificado nesta versão. Reconheça o aviso; isso não autoriza instalação."
        )
    if (
        plan.bitlocker_detected
        or inventory.get("bitlocker_detected")
        or inventory.get("bitlocker_partitions")
    ):
        raise UnsafeInstallPlan(
            "Foi identificado um volume BitLocker no inventário ou no plano; até sua situação ser verificada de forma confiável, o plano permanece bloqueado."
        )
    if plan.free_region_start < MIB or plan.free_region_start % MIB != 0:
        raise UnsafeInstallPlan("Início da região livre inválido ou não alinhado a 1 MiB.")
    if plan.free_region_bytes < MIN_ROOT_BYTES:
        raise UnsafeInstallPlan("A região não alocada precisa ter pelo menos 40 GiB.")
    if plan.root_bytes < MIN_ROOT_BYTES or plan.root_bytes > plan.free_region_bytes:
        raise UnsafeInstallPlan("Tamanho da partição raiz inválido para a região livre.")
    if plan.root_bytes % MIB != 0:
        raise UnsafeInstallPlan("O tamanho da partição raiz precisa estar alinhado a 1 MiB.")

    disks = inventory.get("disks", [])
    disk = next((d for d in disks if d.get("path") == plan.disk_path), None)
    if disk is None:
        raise UnsafeInstallPlan("Disco não encontrado na inspeção atual.")
    if (disk.get("partition_table") or "").lower() != "gpt":
        raise UnsafeInstallPlan("A tabela de partições mudou desde a inspeção.")

    exact_region = next(
        (region for region in inventory.get("free_regions", [])
         if region.get("disk_path") == plan.disk_path
         and region.get("start_bytes") == plan.free_region_start
         and region.get("size_bytes") == plan.free_region_bytes),
        None,
    )
    if exact_region is None:
        raise UnsafeInstallPlan(
            "A região livre não corresponde à geometria lida pelo parted nesta inspeção."
        )

    efi = next(
        (p for p in inventory.get("efi_partitions", [])
         if p.get("path") == plan.efi_partition_path),
        None,
    )
    if efi is None or efi.get("disk_path") != plan.disk_path:
        raise UnsafeInstallPlan("Partição EFI existente no disco selecionado não foi confirmada.")
    if (efi.get("parttype") or "").lower() != EFI_GUID:
        raise UnsafeInstallPlan("O tipo GPT da partição selecionada não é EFI System Partition.")
    if (efi.get("fstype") or "").lower() != "vfat":
        raise UnsafeInstallPlan("A partição EFI não está em FAT; operação bloqueada.")
    efi_size = efi.get("size_bytes")
    if not isinstance(efi_size, int) or efi_size < MIN_EFI_BYTES:
        raise UnsafeInstallPlan("A partição EFI tem menos de 100 MiB ou tamanho desconhecido; operação bloqueada.")

    return {
        "preflight_valid": True,
        "validation_scope": "read_only_preflight_simulation",
        "windows_installation_verified": False,
        "bitlocker_state_verified": False,
        "installation_authorized": False,
        "writes_performed": False,
        "disk": plan.disk_path,
        "partition_table": "gpt",
        "boot_mode": "uefi",
        "target": "unallocated_space_only",
        "free_region_start": plan.free_region_start,
        "free_region_bytes": plan.free_region_bytes,
        "root_bytes": plan.root_bytes,
        "efi": {"path": plan.efi_partition_path, "size_bytes": efi_size, "format": False, "reuse": True},
        "existing_partitions_modified": False,
        "windows_pre_detection": True,
        "execution_enabled": False,
        "message": "Pré-plano coerente apenas para simulação. Windows e BitLocker não foram verificados; nenhuma instalação é autorizada.",
    }
