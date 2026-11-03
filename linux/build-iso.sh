#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
WORK="$ROOT/out/linux-live"
DIST="trixie"
ARCH="amd64"
if [ -n "${SMARTTV_LIVE_WORK:-}" ]; then WORK="$SMARTTV_LIVE_WORK"; fi
if [ -n "${SMARTTV_DEBIAN_SUITE:-}" ]; then DIST="$SMARTTV_DEBIAN_SUITE"; fi
if [ -n "${SMARTTV_ARCH:-}" ]; then ARCH="$SMARTTV_ARCH"; fi

if [ "$(id -u)" != "0" ]; then echo "Execute com sudo: sudo linux/build-iso.sh" >&2; exit 1; fi
for tool in lb debootstrap xorriso mksquashfs; do
  command -v "$tool" >/dev/null 2>&1 || { echo "Ferramenta ausente: $tool" >&2; exit 1; }
done

rm -rf "$WORK"
mkdir -p "$WORK/config/package-lists" \
  "$WORK/config/includes.chroot/usr/local/lib/smarttv" \
  "$WORK/config/includes.chroot/usr/local/bin" \
  "$WORK/config/includes.chroot/etc/xdg/autostart" \
  "$WORK/config/includes.chroot/etc/skel/.config/autostart" \
  "$WORK/config/includes.chroot/etc/skel/Desktop"
cd "$WORK"

python3 "$ROOT/pc/build.py" --out "$WORK/windows-build"
cp -a "$WORK/windows-build/sistema/web" "$WORK/config/includes.chroot/usr/local/lib/smarttv/web"
cp "$ROOT/linux/smarttv.py" "$ROOT/linux/run.sh" "$WORK/config/includes.chroot/usr/local/lib/smarttv/"
chmod 0755 "$WORK/config/includes.chroot/usr/local/lib/smarttv/run.sh"
cat > "$WORK/config/includes.chroot/usr/local/bin/smart-tv" <<'EOF'
#!/usr/bin/env bash
export SMARTTV_HOME=/usr/local/lib/smarttv
exec /usr/local/lib/smarttv/run.sh "$@"
EOF
chmod 0755 "$WORK/config/includes.chroot/usr/local/bin/smart-tv"

for destination in \
  "$WORK/config/includes.chroot/etc/xdg/autostart/smart-tv.desktop" \
  "$WORK/config/includes.chroot/etc/skel/.config/autostart/smart-tv.desktop"; do
cat > "$destination" <<'EOF'
[Desktop Entry]
Type=Application
Name=Smart TV
Comment=Open Smart TV OS after login
Exec=/usr/local/bin/smart-tv
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
done

cat > "$WORK/config/includes.chroot/etc/skel/Desktop/Instalar Smart TV OS.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Instalar Smart TV OS
Comment=Open the Calamares installer
Exec=pkexec calamares
Icon=calamares
Terminal=false
Categories=System;
EOF
chmod 0755 "$WORK/config/includes.chroot/etc/skel/Desktop/Instalar Smart TV OS.desktop"

cat > "$WORK/config/package-lists/smarttv.list.chroot" <<'EOF'
live-boot
live-config
live-config-systemd
systemd-sysv
task-kde-desktop
plasma-desktop
sddm
xserver-xorg
xwayland
konsole
dolphin
network-manager
network-manager-gnome
sudo
python3
chromium
curl
flatpak
firmware-linux
firmware-linux-nonfree
mesa-vulkan-drivers
vulkan-tools
gamemode
mangohud
steam-installer
lutris
wine
wine64
winetricks
vlc
kodi
calamares
calamares-settings-debian
os-prober
parted
dosfstools
btrfs-progs
grub-efi-amd64
shim-signed
EOF

lb config \
  --distribution "$DIST" \
  --architectures "$ARCH" \
  --binary-images iso-hybrid \
  --debian-installer none \
  --archive-areas "main contrib non-free non-free-firmware" \
  --apt-recommends true \
  --bootappend-live "boot=live components locales=pt_BR.UTF-8 keyboard-layouts=br" \
  --memtest none

lb build
ISO="$(find . -maxdepth 1 -type f -name '*.iso' -print -quit)"
if [ -z "$ISO" ]; then echo "live-build terminou sem gerar ISO." >&2; exit 1; fi
mkdir -p "$ROOT/out"
cp "$ISO" "$ROOT/out/SmartTV-OS-live-$DIST-$ARCH.iso"
echo "ISO experimental gerada: $ROOT/out/SmartTV-OS-live-$DIST-$ARCH.iso"
