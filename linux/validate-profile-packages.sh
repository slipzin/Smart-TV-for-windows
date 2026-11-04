#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
PROFILES="$ROOT/linux/profiles"

if [ "$(id -u)" -ne 0 ]; then
  echo "Execute este verificador em um container Debian como root." >&2
  exit 1
fi
if ! grep -q 'VERSION_CODENAME=trixie' /etc/os-release; then
  echo "A resolução de pacotes deve ser feita em Debian 13 Trixie." >&2
  exit 1
fi

read_manifest() {
  sed 's/#.*//' "$1" | awk 'NF'
}
mapfile -t CONSOLE_APT < <(read_manifest "$PROFILES/console-apt-packages.txt")
mapfile -t BACKPORTS < <(read_manifest "$PROFILES/console-backports-packages.txt")
mapfile -t FLATPAKS < <(read_manifest "$PROFILES/console-flatpaks.txt")

export DEBIAN_FRONTEND=noninteractive

# The Debian container may expose only main by default. Match the ISO's archive
# areas so Steam (contrib) and firmware/graphics packages resolve in simulation.
if [ -f /etc/apt/sources.list.d/debian.sources ]; then
  python3 - /etc/apt/sources.list.d/debian.sources <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
lines = path.read_text(encoding="utf-8").splitlines()
areas = ("main", "contrib", "non-free", "non-free-firmware")
for index, line in enumerate(lines):
    if line.startswith("Components:"):
        existing = line.split(":", 1)[1].split()
        lines[index] = "Components: " + " ".join(dict.fromkeys([*existing, *areas]))
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
else
  printf '%s\n' 'deb http://deb.debian.org/debian trixie main contrib non-free non-free-firmware' \
    > /etc/apt/sources.list.d/smarttv-validation.list
fi
dpkg --add-architecture i386
apt-get update
echo "Validando dependências APT do Modo Console (simulação; nenhum pacote gamer será instalado)..."
apt-get -s --no-install-recommends install "${CONSOLE_APT[@]}"

printf '%s\n' 'deb http://deb.debian.org/debian trixie-backports main contrib non-free non-free-firmware' \
  > /etc/apt/sources.list.d/smarttv-trixie-backports.list
apt-get update
echo "Validando Gamescope em Trixie Backports (simulação)..."
apt-get -s -t trixie-backports --no-install-recommends install "${BACKPORTS[@]}"

apt-get install -y --no-install-recommends flatpak
flatpak remote-add --system --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
for app in "${FLATPAKS[@]}"; do
  if ! flatpak remote-info --system flathub "$app" >/dev/null; then
    echo "Aplicativo Flatpak não encontrado no Flathub: $app" >&2
    exit 1
  fi
done

echo "Console APT, Backports e Flathub manifests validated."
