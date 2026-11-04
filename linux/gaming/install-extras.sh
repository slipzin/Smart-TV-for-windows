#!/usr/bin/env bash
set -euo pipefail

# Optional, deliberately user-triggered gaming stack. Run from KDE's terminal
# launcher; package installs require an administrator session.
if [ "$(id -u)" -ne 0 ]; then
  echo "Execute com privilégios administrativos (o atalho já chama pkexec)." >&2
  exit 1
fi
if ! command -v apt-get >/dev/null 2>&1 || ! command -v flatpak >/dev/null 2>&1; then
  echo "Este instalador exige Debian/derivados com APT e Flatpak." >&2
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
apt-get install -y --no-install-recommends \
  steam-devices \
  wine wine64 wine32 winetricks \
  dosbox scummvm \
  bluez blueman

# Gamescope is in Debian 13 backports rather than the base Trixie suite.
if grep -q 'VERSION_CODENAME=trixie' /etc/os-release; then
  printf '%s\n' 'deb http://deb.debian.org/debian trixie-backports main contrib non-free non-free-firmware' \
    > /etc/apt/sources.list.d/smarttv-trixie-backports.list
  apt-get update
  apt-get install -y -t trixie-backports gamescope
fi

flatpak remote-add --system --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install --system --noninteractive -y flathub \
  com.heroicgameslauncher.hgl \
  com.usebottles.bottles \
  net.davidotek.pupgui2 \
  org.libretro.RetroArch \
  org.DolphinEmu.dolphin-emu \
  org.ppsspp.PPSSPP \
  net.pcsx2.PCSX2 \
  net.rpcs3.RPCS3

echo
echo "Instalação concluída."
echo "Steam: abra o instalador Steam pelo menu e conclua a instalação na sua conta."
echo "Heroic: conecte suas contas Epic, GOG e Amazon dentro do aplicativo."
echo "ProtonUp-Qt: use para instalar GE-Proton/compatibilidade adicional."
echo "Emuladores exigem jogos, BIOS e firmware obtidos legalmente pelo próprio usuário."
echo "Reinicie a sessão se controles USB/Bluetooth não aparecerem após instalar steam-devices."
