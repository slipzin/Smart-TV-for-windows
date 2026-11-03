#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd -- "$(dirname -- "$0")" && pwd)"
APP_ROOT="$HERE"
if [ -n "${SMARTTV_HOME:-}" ]; then APP_ROOT="$SMARTTV_HOME"; fi
WEB_DIR="$APP_ROOT/web"
if [ -n "${SMARTTV_WEB:-}" ]; then WEB_DIR="$SMARTTV_WEB"; fi
FUNDOS_DIR="$HOME/Pictures/SmartTV/Fundos"
PORT=48765
if [ -n "${SMARTTV_PORT:-}" ]; then PORT="$SMARTTV_PORT"; fi

if [ ! -d "$WEB_DIR" ]; then
  echo "Pasta da interface não encontrada: $WEB_DIR" >&2
  exit 1
fi
BROWSER=""
for candidate in chromium chromium-browser google-chrome-stable google-chrome; do
  if command -v "$candidate" >/dev/null 2>&1; then BROWSER="$(command -v "$candidate")"; break; fi
done
if [ -z "$BROWSER" ]; then
  echo "Chromium não encontrado. Instale o pacote chromium." >&2
  exit 1
fi

mkdir -p "$FUNDOS_DIR" "$HOME/.config/smart-tv"
python3 "$APP_ROOT/smarttv.py" --web "$WEB_DIR" --fundos "$FUNDOS_DIR" --port "$PORT" &
SERVER_PID=$!
cleanup() {
  if ps -p "$SERVER_PID" >/dev/null 2>&1; then kill "$SERVER_PID" 2>/dev/null || true; fi
  wait "$SERVER_PID" 2>/dev/null || true
  if [ -n "${BROWSER_PID:-}" ] && ps -p "$BROWSER_PID" >/dev/null 2>&1; then
    kill -- "-$BROWSER_PID" 2>/dev/null || kill "$BROWSER_PID" 2>/dev/null || true
    wait "$BROWSER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

READY=0
for attempt in $(seq 1 100); do
  if ! ps -p "$SERVER_PID" >/dev/null 2>&1; then
    echo "O backend Smart TV encerrou antes de iniciar." >&2
    exit 1
  fi
  if curl --silent --fail "http://127.0.0.1:$PORT/api/about" >/dev/null 2>&1; then READY=1; break; fi
  sleep 0.1
done
if [ "$READY" != "1" ]; then echo "Não foi possível iniciar o servidor local." >&2; exit 1; fi

PROFILE="$HOME/.config/smart-tv/chromium"
URL="http://127.0.0.1:$PORT/?platform=linux"
if command -v setsid >/dev/null 2>&1; then
  setsid "$BROWSER" --user-data-dir="$PROFILE" --kiosk "$URL" --no-first-run --no-default-browser-check --disable-session-crashed-bubble --autoplay-policy=no-user-gesture-required &
else
  "$BROWSER" --user-data-dir="$PROFILE" --kiosk "$URL" --no-first-run --no-default-browser-check --disable-session-crashed-bubble --autoplay-policy=no-user-gesture-required &
fi
BROWSER_PID=$!

alive() {
  state="$(ps -o stat= -p "$1" 2>/dev/null | tr -d ' ' || true)"
  [ -n "$state" ] && [ "${state#Z}" = "$state" ]
}
while alive "$SERVER_PID" && alive "$BROWSER_PID"; do sleep 0.25; done
if alive "$BROWSER_PID"; then
  kill -- "-$BROWSER_PID" 2>/dev/null || kill "$BROWSER_PID" 2>/dev/null || true
fi
wait "$BROWSER_PID" 2>/dev/null || true
