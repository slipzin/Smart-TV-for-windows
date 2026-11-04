#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/smart-tv/cast"
CERTS_FILE="$DATA_DIR/certs.json"
PLAYER_DIR="/usr/local/share/smarttv/cast-player"
LOG_FILE="$DATA_DIR/vibecast.log"
PLAYER_LOG="$DATA_DIR/player-http.log"
BROWSER_LOG="$DATA_DIR/player-browser.log"

show_error() {
  if command -v kdialog >/dev/null 2>&1 && [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
    kdialog --title "Google Cast — TV Sala" --error "$1" || true
  else
    printf '%s\n' "$1" >&2
  fi
}

if ! command -v vibecast >/dev/null 2>&1; then
  show_error "O receptor Google Cast não está instalado nesta imagem."
  exit 1
fi

if [ ! -s "$CERTS_FILE" ]; then
  show_error "O receptor Cast foi instalado, mas ainda não pode aceitar conexões. Falta o arquivo privado de autenticação do dispositivo Cast em:

$CERTS_FILE

O VibeCast exige material de autenticação válido de um dispositivo Google Cast real. Esse material não é distribuído com a ISO e não deve ser publicado no GitHub nem enviado a terceiros.

Quando o arquivo autorizado estiver disponível, coloque-o nesse caminho com permissão restrita e abra novamente este atalho."
  exit 2
fi

python3 - "$CERTS_FILE" <<'PY'
import json
import sys

path = sys.argv[1]
try:
    with open(path, "r", encoding="utf-8") as stream:
        data = json.load(stream)
except Exception as error:
    raise SystemExit("Arquivo de autenticação inválido (JSON): " + str(error))

if not isinstance(data, dict):
    raise SystemExit("O arquivo de autenticação precisa ser um objeto JSON.")
if not isinstance(data.get("cpu"), str) or not data["cpu"].strip():
    raise SystemExit("Certificado de dispositivo ausente (cpu).")
if not isinstance(data.get("ica"), str) or not data["ica"].strip():
    raise SystemExit("Cadeia intermediária ausente (ica).")
peers = data.get("certs")
if not isinstance(peers, list) or not peers:
    raise SystemExit("Lista de certificados de autenticação ausente (certs).")
for index, item in enumerate(peers):
    if not isinstance(item, dict) or not all(
        isinstance(item.get(key), str) and item[key].strip()
        for key in ("pu", "pr", "sig_sha1", "sig_sha256")
    ):
        raise SystemExit(f"Certificado de sessão {index} incompleto.")
PY

chmod 600 "$CERTS_FILE"
mkdir -p "$DATA_DIR"
if [ ! -s "$DATA_DIR/config.toml" ]; then
  cat > "$DATA_DIR/config.toml" <<'EOF'
[device]
model = "Smart TV OS"
manufacturer = "Smart TV OS"
locale = "pt-BR"
country_code = "BR"
certs = "certs.json"

[network]
bind_host = "0.0.0.0"
player_port = 8010
EOF
  chmod 600 "$DATA_DIR/config.toml"
fi

if [ ! -s "$PLAYER_DIR/player.html" ] || [ ! -s "$PLAYER_DIR/player.js" ]; then
  show_error "Os arquivos do player Google Cast não foram encontrados em $PLAYER_DIR."
  exit 1
fi

if command -v chromium >/dev/null 2>&1; then
  BROWSER="$(command -v chromium)"
elif command -v chromium-browser >/dev/null 2>&1; then
  BROWSER="$(command -v chromium-browser)"
else
  show_error "Chromium não foi encontrado."
  exit 1
fi

mkdir -p "$DATA_DIR/browser-profile"

vibecast --data-dir "$DATA_DIR" --model "Smart TV OS" --bind-host 0.0.0.0 --player-port 8010 >>"$LOG_FILE" 2>&1 &
RECEIVER_PID=$!
python3 -m http.server 8020 --bind 127.0.0.1 --directory "$PLAYER_DIR" >>"$PLAYER_LOG" 2>&1 &
PLAYER_HTTP_PID=$!

cleanup() {
  kill "$PLAYER_HTTP_PID" "$RECEIVER_PID" 2>/dev/null || true
  wait "$PLAYER_HTTP_PID" "$RECEIVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

for _ in $(seq 1 30); do
  if ! kill -0 "$RECEIVER_PID" 2>/dev/null; then
    show_error "O receptor Google Cast encerrou durante a inicialização. Consulte $LOG_FILE."
    exit 1
  fi
  if (exec 3<>/dev/tcp/127.0.0.1/8010) 2>/dev/null; then
    break
  fi
  sleep 1
done

if ! (exec 3<>/dev/tcp/127.0.0.1/8010) 2>/dev/null; then
  show_error "O serviço Google Cast não abriu a porta 8010. Consulte $LOG_FILE."
  exit 1
fi

"$BROWSER" --no-first-run --disable-session-crashed-bubble \
  --user-data-dir="$DATA_DIR/browser-profile" \
  --kiosk --autoplay-policy=no-user-gesture-required \
  http://127.0.0.1:8020/ >>"$BROWSER_LOG" 2>&1

