"""Read-only partition geometry inspection for the Smart TV OS installer."""
from __future__ import annotations

import re
import shutil
import subprocess
from decimal import Decimal, InvalidOperation
from typing import Any

_BYTE_VALUE = re.compile(r"^([0-9]+(?:\\.[0-9]+)?)B$", re.IGNORECASE)


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
    """Parse GNU parted machine output; accept only consistent Free Space rows."""
    if not disk_path.startswith("/dev/"):
        raise ValueError("Dispositivo de disco inválido.")
    regions: list[dict[str, Any]] = []
    header_seen = False
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.upper() == "BYT;":
            continue
        if line.startswith("/dev/"):
            reported_disk = line.split(":", 1)[0]
            if reported_disk != disk_path:
                raise ValueError("O parted retornou a geometria de outro dispositivo.")
            header_seen = True
            continue
        fields = line.rstrip(";").split(":")
        if len(fields) < 5:
            continue
        description = ":".join(fields[4:]).strip().lower()
        if "free space" not in description and description != "free":
            continue
        start = _bytes(fields[1])
        end = _bytes(fields[2])
        size = _bytes(fields[3])
        if start is None or end is None or size is None:
            continue
        if end < start or size <= 0 or end - start + 1 != size:
            continue
        regions.append({
            "disk_path": disk_path,
            "start_bytes": start,
            "end_bytes": end,
            "size_bytes": size,
        })
    if output.strip() and not header_seen:
        raise ValueError("Cabeçalho do parted não confirmou o dispositivo consultado.")
    return regions


def inspect_free_regions(disk_path: str) -> list[dict[str, Any]]:
    """Read partition geometry with parted print free. No write-mode command is used."""
    if not disk_path.startswith("/dev/") or any(ch.isspace() for ch in disk_path):
        raise ValueError("Caminho de disco inválido.")
    if not shutil.which("parted"):
        raise RuntimeError("O comando parted não está disponível.")
    result = subprocess.run(
        ["parted", "--machine", "--script", disk_path, "unit", "B", "print", "free"],
        check=False,
        text=True,
        capture_output=True,
        timeout=20,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "parted não conseguiu ler a tabela de partições."
        raise RuntimeError(detail)
    return parse_parted_free_regions(result.stdout, disk_path)