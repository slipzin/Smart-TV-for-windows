#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
SCRIPT="$ROOT/linux/cloud-gaming/launch-cloud-game.sh"
TEMP="$(mktemp -d)"
trap 'rm -rf "$TEMP"' EXIT
mkdir -p "$TEMP/bin" "$TEMP/home"
cat > "$TEMP/bin/chromium" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" > "$CLOUD_TEST_ARGS"
EOF
chmod +x "$TEMP/bin/chromium"
export HOME="$TEMP/home"
export CLOUD_TEST_ARGS="$TEMP/args"
export PATH="$TEMP/bin:$PATH"

bash "$SCRIPT" xbox
grep -Fxq -- '--app=https://www.xbox.com/pt-BR/play' "$CLOUD_TEST_ARGS"
grep -Fxq -- "--user-data-dir=$HOME/.local/share/smart-tv/cloud-profiles/xbox" "$CLOUD_TEST_ARGS"
grep -Fxq -- '--enable-features=VaapiVideoDecodeLinuxGL' "$CLOUD_TEST_ARGS"

bash "$SCRIPT" geforcenow
grep -Fxq -- '--app=https://play.geforcenow.com/' "$CLOUD_TEST_ARGS"
grep -Fxq -- "--user-data-dir=$HOME/.local/share/smart-tv/cloud-profiles/geforce-now" "$CLOUD_TEST_ARGS"

bash "$SCRIPT" boosteroid
grep -Fxq -- '--app=https://cloud.boosteroid.com/' "$CLOUD_TEST_ARGS"
grep -Fxq -- "--user-data-dir=$HOME/.local/share/smart-tv/cloud-profiles/boosteroid" "$CLOUD_TEST_ARGS"

if bash "$SCRIPT" not-a-provider >/dev/null 2>&1; then
  echo "Provider desconhecido foi aceito indevidamente." >&2
  exit 1
fi
echo "Cloud gaming launchers passed."
