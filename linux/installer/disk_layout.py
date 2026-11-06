"""Read-only partition geometry inspection for the Smart TV OS installer."""
from __future__ import annotations

import re
import shutil
import subprocess
from typing import Any

_BYTE_VALUE = re.compile(r"^([0-9]+(?:\.[0-9]+)?)B$", re.IGNORECASE)


def _bytes(value: str) -> int | None:
    match = _BYTE_VALUE.fullmatch(value.strip())
    if not match:
        return None
    return int(float(match.group(1)))


def parse_parted_free_regions(output: str, disk_path: str) -> list[dict[str, Any]]:
    """Parse GNU parted machine output; only rows explicitly marked Free Space count."""
    if not disk_path.startswith("/dev/"):
        raise ValueError("Dispositivo de disco inválido.")
    regions: list[dict[str, Any]] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.upper() == "BYT;" or line.startswith("/dev/"):
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
        if start is None or end is None or size is None or end < start or size <= 0:
            continue
        regions.append({
            "disk_path": disk_path,
            "start_bytes": start,
            "end_bytes": end,
            "size_bytes": size,
        })
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
