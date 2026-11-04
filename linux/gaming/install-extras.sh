#!/usr/bin/env bash
set -euo pipefail

MANIFEST_DIR="${SMARTTV_GAMING_MANIFEST_DIR:-/usr/share/smarttv-gaming}"
APT_MANIFEST="$MANIFEST_DIR/console-apt-packages.txt"
FLATPAK_MANIFEST="$MANIFEST_DIR/console-flatpaks.txt"
BACKPORTS_MANIFEST="$MANIFEST_DIR/console-backports-packages.txt"

for manifest in "$APT_MANIFEST" "$FLATPAK_MANIFEST" "$BACKPORTS_MANIFEST"; do
  if [ ! -r "$manifest" ]; then
    echo "Manifesto gamer ausente: $manifest" >&2
    exit 1
  fi
done

mapfile -t APT_PACKAGES < <(sed 's/#.*//' "$APT_MANIFEST" | awk 'NF')
mapfile -t FLATPAK_APPS < <(sed 's/#.*//' "$FLATPAK_MANIFEST" | awk 'NF')
mapfile -t BACKPORTS_PACKAGES < <(sed 's/#.*//' "$BACKPORTS_MANIFEST" | awk 'NF')
if [ "${#APT_PACKAGES[@]}" -eq 0 ] || [ "${#FLATPAK_APPS[@]}" -eq 0 ] || [ "${#BACKPORTS_PACKAGES[@]}" -eq 0 ]; then
  echo "Manifestos do Modo Console incompletos." >&2
  exit 1
fi

# CI can inspect the exact package plan without root, network or modifying a host.
if [ "${1:-}" = "--print-plan" ]; then
  printf 'APT: %s\n' "${APT_PACKAGES[*]}"
  printf 'BACKPORTS: %s\n' "${BACKPORTS_PACKAGES[*]}"
  printf 'FLATPAK: %s\n' "${FLATPAK_APPS[*]}"
  exit 0
fi
if [ "$#" -ne 0 ]; then
  echo "Uso: smart-tv-install-gaming [--print-plan]" >&2
  exit 2
fi
if [ "$(id -u)" -ne 0 ]; then
  echo "Execute com privilégios administrativos (o atalho já chama pkexec)." >&2
  exit 1
fi
if ! command -v apt-get >/dev/null 2>&1 || ! command -v flatpak >/dev/null 2>&1; then
  echo "Este instalador exige Debian 13 com APT e Flatpak." >&2
  exit 1
fi
if [ "$(dpkg --print-architecture)" != "amd64" ]; then
  echo "O perfil Console desta ISO foi preparado para Debian amd64." >&2
  exit 1
fi
. /etc/os-release
if [ "${ID:-}" != "debian" ] || [ "${VERSION_CODENAME:-}" != "trixie" ]; then
  echo "O instalador gamer desta versão exige Debian 13 Trixie amd64." >&2
  exit 1
fi
echo "Este pacote instala ferramentas de compatibilidade, emuladores e launchers."
echo "Os jogos, BIOS, firmware e contas não são fornecidos."
echo
read -r -p "Continuar com a instalação gamer? [s/N] " answer
case "${answer,,}" in s|sim|y|yes) ;; *) echo "Cancelado."; exit 0 ;; esac

export DEBIAN_FRONTEND=noninteractive
dpkg --add-architecture i386
apt-get update

# Steam is in Debian contrib; fail clearly when the source component is absent.
if ! apt-cache policy steam-installer | grep -Eq 'Candidate: [^ (]'; then
  echo "O pacote steam-installer não tem candidato APT. Verifique se contrib está habilitado." >&2
  exit 1
fi
apt-get install -y --no-install-recommends "${APT_PACKAGES[@]}"

# Gamescope is delivered from Trixie Backports, which is not enabled in TV mode.
if ! grep -Rqs 'trixie-backports' /etc/apt/sources.list /etc/apt/sources.list.d 2>/dev/null; then
  printf '%s\n' 'deb http://deb.debian.org/debian trixie-backports main contrib non-free non-free-firmware' \
    > /etc/apt/sources.list.d/smarttv-trixie-backports.list
fi
apt-get update
apt-get install -y -t trixie-backports "${BACKPORTS_PACKAGES[@]}"

flatpak remote-add --system --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install --system --noninteractive -y flathub "${FLATPAK_APPS[@]}"

echo
echo "Componentes do Modo Console instalados."
echo "Abra a Steam e entre na sua conta para baixar os jogos localmente."
echo "Heroic permite conectar suas contas Epic, GOG e Amazon."
echo "ProtonUp-Qt instala versões adicionais GE-Proton."
echo "Emuladores não incluem ROMs, BIOS ou firmware; use arquivos obtidos legalmente."
echo "Reinicie a sessão se dispositivos de controle instalados via udev não aparecerem."
