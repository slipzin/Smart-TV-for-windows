#!/usr/bin/env bash
set -euo pipefail

provider="${1:-}"
case "$provider" in
  xbox)
    url="https://www.xbox.com/pt-BR/play"
    profile="xbox"
    ;;
  geforcenow)
    url="https://play.geforcenow.com/"
    profile="geforce-now"
    ;;
  boosteroid)
    url="https://cloud.boosteroid.com/"
    profile="boosteroid"
    ;;
  moonlight)
    exec moonlight "$@"
    ;;
  steamlink)
    exec steamlink "$@"
    ;;
  *)
    echo "Uso: smart-tv-cloud-game {xbox|geforcenow|boosteroid|moonlight|steamlink}" >&2
    exit 2
    ;;
esac

if ! command -v chromium >/dev/null 2>&1; then
  echo "Chromium não está instalado." >&2
  exit 1
fi

data_home="${XDG_DATA_HOME:-$HOME/.local/share}"
profile_dir="$data_home/smart-tv/cloud-profiles/$profile"
mkdir -p "$profile_dir"
chmod 700 "$data_home/smart-tv" "$data_home/smart-tv/cloud-profiles" "$profile_dir" 2>/dev/null || true

# A separate persistent browser profile keeps provider logins isolated from
# the Smart TV shell and from other cloud providers.
exec chromium \
  --app="$url" \
  --start-fullscreen \
  --no-first-run \
  --no-default-browser-check \
  --disable-session-crashed-bubble \
  --user-data-dir="$profile_dir"
