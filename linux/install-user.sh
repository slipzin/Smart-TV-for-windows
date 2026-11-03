#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
TARGET="$HOME/.local/share/smart-tv"
BIN="$HOME/.local/bin"
AUTOSTART="$HOME/.config/autostart"
TEMP="$(mktemp -d)"
trap 'rm -rf "$TEMP"' EXIT

if ! command -v python3 >/dev/null 2>&1; then echo "Python 3 é necessário." >&2; exit 1; fi
if ! command -v chromium >/dev/null 2>&1 && ! command -v chromium-browser >/dev/null 2>&1; then
  echo "Instale o Chromium antes (ex.: sudo apt install chromium)." >&2
  exit 1
fi

python3 "$ROOT/pc/build.py" --out "$TEMP/SmartTV"
mkdir -p "$TARGET" "$BIN" "$AUTOSTART" "$HOME/Pictures/SmartTV/Fundos"
rm -rf "$TARGET/web"
cp -a "$TEMP/SmartTV/sistema/web" "$TARGET/web"
cp "$ROOT/linux/smarttv.py" "$ROOT/linux/run.sh" "$TARGET/"
chmod 0755 "$TARGET/run.sh"
printf '#!/usr/bin/env bash\nexec "%s/run.sh" "$@"\n' "$TARGET" > "$BIN/smart-tv"
chmod 0755 "$BIN/smart-tv"
cat > "$AUTOSTART/smart-tv.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Smart TV
Comment=Start Smart TV OS at login
Exec=$BIN/smart-tv
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

echo "Smart TV OS instalado para este usuário em: $TARGET"
echo "Inicie com: $BIN/smart-tv"
echo "A inicialização automática está configurada para a sessão gráfica deste usuário."
