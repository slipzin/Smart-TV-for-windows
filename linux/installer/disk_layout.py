"""Read-only partition geometry inspection for the Smart TV OS installer."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from decimal import Decimal, InvalidOperation
from typing import Any

_BYTE_VALUE = re.compile(r"^([0-9]+(?:\.[0-9]+)?)B$", re.IGNORECASE)


def _bytes(value: str) -> int | None:
    match = _BYTE_VALUE.fullmatch(value.strip())
    if not match:
        return None
    try:
        number = Decimal(match.group(1))
    except InvalidOperation:
        return None
    if number != number.to_integral_value():
        return None
    return int(number)


def parse_parted_free_regions(output: str, disk_path: str) -> list[dict[str, Any]]:
    """Parse GNU parted machine output and reject untrustworthy geometry."""
    if not disk_path.startswith("/dev/") or any(ch.isspace() for ch in disk_path):
        raise ValueError("Dispositivo de disco inválido.")

    disk_size_bytes: int | None = None
    header_seen = False
    regions: list[dict[str, Any]] = []

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.upper() == "BYT;":
            continue

        if line.startswith("/dev/"):
            if header_seen:
                raise ValueError("O parted retornou mais de um cabeçalho de disco.")
            fields = line.rstrip(";").split(":")
            reported_disk = fields[0]
            if reported_disk != disk_path:
                raise ValueError("O parted retornou a geometria de outro dispositivo.")
            if len(fields) < 3:
                raise ValueError("Cabeçalho do parted incompleto.")
            disk_size_bytes = _bytes(fields[1])
            if disk_size_bytes is None or disk_size_bytes <= 0:
                raise ValueError("O parted não informou um tamanho de disco válido em bytes.")
            header_seen = True
            continue

        fields = line.rstrip(";").split(":")
        if not fields or not fields[0].isdigit():
            continue
        if len(fields) < 5:
            raise ValueError("Linha de partição do parted incompleta.")

        description = ":".join(fields[4:]).strip().lower()
        if "free space" not in description and description != "free":
            continue
        if not header_seen or disk_size_bytes is None:
            raise ValueError("O parted informou espaço livre antes de confirmar o disco.")

        start = _bytes(fields[1])
        end = _bytes(fields[2])
        size = _bytes(fields[3])
        if start is None or end is None or size is None:
            raise ValueError("O parted retornou limites de espaço livre inválidos.")
        if start < 0 or end < start or size <= 0:
            raise ValueError("O parted retornou uma região livre com limites inválidos.")
        if end - start + 1 != size:
            raise ValueError("O tamanho da região livre não corresponde aos limites informados.")
        if end >= disk_size_bytes:
            raise ValueError("A região livre ultrapassa o tamanho físico informado pelo parted.")

        regions.append({
            "disk_path": disk_path,
            "disk_size_bytes": disk_size_bytes,
            "start_bytes": start,
            "end_bytes": end,
            "size_bytes": size,
        })

    if not header_seen or disk_size_bytes is None:
        raise ValueError("O cabeçalho do parted não confirmou o dispositivo e seu tamanho.")

    regions.sort(key=lambda item: item["start_bytes"])
    previous_end = -1
    for region in regions:
        if region["start_bytes"] <= previous_end:
            raise ValueError("O parted retornou regiões livres sobrepostas ou duplicadas.")
        previous_end = region["end_bytes"]

    return regions


def inspect_free_regions(disk_path: str) -> list[dict[str, Any]]:
    """Read partition geometry with parted print free; never opens write mode."""
    if not disk_path.startswith("/dev/") or any(ch.isspace() for ch in disk_path):
        raise ValueError("Caminho de disco inválido.")
    if not shutil.which("parted"):
        raise RuntimeError("O comando parted não está disponível.")

    env = os.environ.copy()
    env.update({"LC_ALL": "C", "LANG": "C"})
    result = subprocess.run(
        ["parted", "--machine", "--script", disk_path, "unit", "B", "print", "free"],
        check=False,
        text=True,
        capture_output=True,
        timeout=20,
        env=env,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "parted não conseguiu ler a tabela de partições."
        raise RuntimeError(detail)
    return parse_parted_free_regions(result.stdout, disk_path)
