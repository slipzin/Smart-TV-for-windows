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
  "$WORK/config/includes.chroot/etc/skel/Desktop" "$WORK/config/includes.chroot/etc/default/grub.d" "$WORK/config/hooks/live"
cd "$WORK"

# Build a pinned VibeCast receiver from source. The player name and public
# receiver name are patched to the product's friendly name: "TV Sala".
mkdir -p "$ROOT/out"
VIBECAST_BUILD="$ROOT/out/vibecast-build"
rm -rf "$VIBECAST_BUILD"
mkdir -p "$VIBECAST_BUILD"
VIBECAST_SRC="$VIBECAST_BUILD/source"
VIBECAST_TARGET="$VIBECAST_BUILD/target"
git clone --depth 1 --branch v0.2.0 https://github.com/emilsvennesson/vibecast.git "$VIBECAST_SRC"

export CARGO_HOME="$VIBECAST_BUILD/cargo-home"
export RUSTUP_HOME="$VIBECAST_BUILD/rustup-home"
if [ ! -x "$CARGO_HOME/bin/rustup" ]; then
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o "$VIBECAST_BUILD/rustup-init.sh"
  sh "$VIBECAST_BUILD/rustup-init.sh" -y --no-modify-path --profile minimal --default-toolchain 1.88.0
fi
export PATH="$CARGO_HOME/bin:$PATH"
rustup toolchain install 1.88.0 --profile minimal
rustup default 1.88.0

python3 - "$VIBECAST_SRC" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
manager = root / "crates/vibecast-platform/src/manager.rs"
text = manager.read_text(encoding="utf-8")
old = 'let friendly_name = format!("{} [vibecast]", registration.name);'
new = 'let friendly_name = registration.name.clone();'
if text.count(old) != 1:
    raise SystemExit("VibeCast 0.2.0 manager naming code changed; review patch before building.")
manager.write_text(text.replace(old, new), encoding="utf-8")

player = root / "crates/vibecast-bridge/assets/player.js"
text = player.read_text(encoding="utf-8")
old_name = 'name: "Browser",'
old_url = 'return wsProtocol + "://" + window.location.host + "/player";'
if text.count(old_name) != 1 or text.count(old_url) != 1:
    raise SystemExit("VibeCast browser player changed; review TV Sala patch before building.")
text = text.replace(old_name, 'name: "TV Sala",')
text = text.replace(old_url, 'return "ws://127.0.0.1:8010/player";')
player.write_text(text, encoding="utf-8")
PY

# Run the upstream YouTube receiver's protocol, Lounge, resolver and playback tests.
CARGO_TARGET_DIR="$VIBECAST_TARGET" cargo test --release --locked --manifest-path "$VIBECAST_SRC/Cargo.toml" -p vibecast-apps-youtube
CARGO_TARGET_DIR="$VIBECAST_TARGET" cargo build --release --locked --manifest-path "$VIBECAST_SRC/Cargo.toml" -p vibecast-cli
install -D -m 0755 "$VIBECAST_TARGET/release/vibecast" \
  "$WORK/config/includes.chroot/usr/local/bin/vibecast"
install -D -m 0644 "$VIBECAST_SRC/LICENSE" \
  "$WORK/config/includes.chroot/usr/share/doc/smarttv-vibecast/LICENSE"

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

cat > "$WORK/config/includes.chroot/etc/skel/Desktop/Receber AirPlay.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Receber AirPlay
Comment=Receba espelhamento AirPlay compatível com PIN de segurança
Exec=konsole -e uxplay -n Smart-TV-OS -pin
Icon=network-wireless
Terminal=false
Categories=Network;AudioVideo;
EOF
chmod 0755 "$WORK/config/includes.chroot/etc/skel/Desktop/Receber AirPlay.desktop"

install -D -m 0755 "$ROOT/linux/gaming/install-extras.sh" \
  "$WORK/config/includes.chroot/usr/local/bin/smart-tv-install-gaming"
install -D -m 0644 "$ROOT/linux/gaming/README.md" \
  "$WORK/config/includes.chroot/usr/share/doc/smarttv-gaming/README.md"

for destination in \
  "$WORK/config/includes.chroot/etc/skel/Desktop/Instalar extras de jogos.desktop" \
  "$WORK/config/includes.chroot/usr/share/applications/smart-tv-install-gaming.desktop"; do
cat > "$destination" <<'EOF'
[Desktop Entry]
Type=Application
Name=Instalar extras de jogos
Comment=Instala Steam Input, Wine, Heroic, emuladores e ferramentas opcionais
Exec=konsole -e pkexec /usr/local/bin/smart-tv-install-gaming
Icon=applications-games
Terminal=false
Categories=System;Utility;
EOF
done
chmod 0755 "$WORK/config/includes.chroot/etc/skel/Desktop/Instalar extras de jogos.desktop"

install -D -m 0755 "$ROOT/linux/cast/start.sh" \
  "$WORK/config/includes.chroot/usr/local/bin/smart-tv-cast"
cp "$ROOT/linux/cast/README.md" \
  "$WORK/config/includes.chroot/usr/share/doc/smarttv-vibecast/SMART-TV-OS-SETUP.md"
cat > "$WORK/config/includes.chroot/etc/skel/Desktop/Iniciar Google Cast - TV Sala.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Iniciar Google Cast - TV Sala
Comment=Inicia o receptor Google Cast quando a autenticação estiver configurada
Exec=konsole -e /usr/local/bin/smart-tv-cast
Icon=network-wireless
Terminal=false
Categories=Network;AudioVideo;
EOF
chmod 0755 "$WORK/config/includes.chroot/etc/skel/Desktop/Iniciar Google Cast - TV Sala.desktop"

cat > "$WORK/config/hooks/live/0500-flathub.hook.chroot" <<'EOF'
#!/bin/sh
set -eu
if command -v flatpak >/dev/null 2>&1; then
  flatpak remote-add --system --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
fi
EOF
chmod 0755 "$WORK/config/hooks/live/0500-flathub.hook.chroot"

echo "GRUB_DISABLE_OS_PROBER=false" > "$WORK/config/includes.chroot/etc/default/grub.d/50-smarttv-os-prober.cfg"

cat > "$WORK/config/package-lists/smarttv.list.chroot" <<'EOF'
live-boot
live-config
live-config-systemd
systemd-sysv
plasma-desktop
plasma-workspace
plasma-nm
kwin-x11
sddm
xserver-xorg
xwayland
konsole
dolphin
network-manager
avahi-daemon
pipewire-audio
pipewire-pulse
wireplumber
udisks2
xdg-desktop-portal
xdg-desktop-portal-kde
bluez
blueman
sudo
python3
chromium
curl
flatpak
firmware-linux
firmware-linux-nonfree
mesa-vulkan-drivers
vlc
kodi
uxplay
gstreamer1.0-libav
gstreamer1.0-plugins-good
plasma-discover
plasma-discover-backend-flatpak
calamares
calamares-settings-debian
os-prober
ntfs-3g
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
