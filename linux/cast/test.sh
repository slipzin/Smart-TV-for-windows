#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
START="$ROOT/linux/cast/start.sh"
TMP="$(mktemp -d)"
MOCK_BIN="$TMP/bin"
MOCK_PLAYER="$TMP/player"
mkdir -p "$MOCK_BIN" "$MOCK_PLAYER"
cleanup() {
  rm -rf "$TMP"
}
trap cleanup EXIT

cat > "$MOCK_BIN/vibecast" <<'EOF'
#!/usr/bin/env bash
# Mock HTTP endpoint for launcher lifecycle testing only.
exec python3 -m http.server 8010 --bind 127.0.0.1 --directory "$MOCK_PLAYER_ROOT"
EOF
chmod +x "$MOCK_BIN/vibecast"

# 1. Missing credentials must fail closed before starting any service.
MISSING_HOME="$TMP/missing"
set +e
env -u DISPLAY -u WAYLAND_DISPLAY HOME="$MISSING_HOME" XDG_CONFIG_HOME="$MISSING_HOME/.config" \
  MOCK_PLAYER_ROOT="$MOCK_PLAYER" PATH="$MOCK_BIN:/usr/bin:/bin" \
  bash "$START" >"$TMP/missing.log" 2>&1
MISSING_STATUS=$?
set -e
if [[ "$MISSING_STATUS" -ne 2 ]] || ! grep -q "Falta o arquivo privado" "$TMP/missing.log"; then
  cat "$TMP/missing.log" >&2
  echo "Missing-certificate test failed." >&2
  exit 1
fi

# 2. Malformed JSON must also fail closed.
BAD_HOME="$TMP/bad"
mkdir -p "$BAD_HOME/.config/smart-tv/cast"
printf '{not valid json' > "$BAD_HOME/.config/smart-tv/cast/certs.json"
set +e
env -u DISPLAY -u WAYLAND_DISPLAY HOME="$BAD_HOME" XDG_CONFIG_HOME="$BAD_HOME/.config" \
  MOCK_PLAYER_ROOT="$MOCK_PLAYER" PATH="$MOCK_BIN:/usr/bin:/bin" \
  bash "$START" >"$TMP/bad.log" 2>&1
BAD_STATUS=$?
set -e
if [[ "$BAD_STATUS" -eq 0 ]] || ! grep -q "Arquivo de autenticação inválido" "$TMP/bad.log"; then
  cat "$TMP/bad.log" >&2
  echo "Malformed-certificate test failed." >&2
  exit 1
fi

# 3. Use explicitly fake, structurally shaped values to test only launcher
# orchestration. These values are NOT valid Cast credentials and cannot
# authenticate a phone or a real Google Cast Sender.
VALID_HOME="$TMP/valid"
mkdir -p "$VALID_HOME/.config/smart-tv/cast"
cat > "$VALID_HOME/.config/smart-tv/cast/certs.json" <<'EOF'
{
  "cpu": "FAKE DEVICE CERTIFICATE — TEST ONLY",
  "ica": "FAKE INTERMEDIATE CERTIFICATE — TEST ONLY",
  "certs": [
    {
      "pu": "FAKE PEER CERTIFICATE — TEST ONLY",
      "pr": "FAKE PRIVATE KEY — TEST ONLY",
      "sig_sha1": "ZmFrZQ==",
      "sig_sha256": "ZmFrZQ=="
    }
  ]
}
EOF

cat > "$MOCK_PLAYER/index.html" <<'EOF'
<!doctype html><html><head><title>TV Sala test player</title></head>
<body>TV Sala mock player endpoint</body></html>
EOF

cat > "$MOCK_BIN/chromium" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
url="${@: -1}"
[[ "$url" == "http://127.0.0.1:8010/" ]]
curl -fsS "$url" | grep -q "TV Sala mock player endpoint"
touch "$BROWSER_TEST_MARKER"
EOF
chmod +x "$MOCK_BIN/chromium"

env -u DISPLAY -u WAYLAND_DISPLAY HOME="$VALID_HOME" XDG_CONFIG_HOME="$VALID_HOME/.config" \
  MOCK_PLAYER_ROOT="$MOCK_PLAYER" \
  BROWSER_TEST_MARKER="$TMP/browser-opened" \
  PATH="$MOCK_BIN:/usr/bin:/bin" \
  bash "$START" >"$TMP/valid.log" 2>&1

if [[ ! -e "$TMP/browser-opened" ]]; then
  cat "$TMP/valid.log" >&2
  echo "Browser/player startup test failed." >&2
  exit 1
fi
CERT_MODE="$(stat -c '%a' "$VALID_HOME/.config/smart-tv/cast/certs.json")"
if [[ "$CERT_MODE" != "600" ]]; then
  echo "Certificate file permissions are $CERT_MODE; expected 600." >&2
  exit 1
fi

echo "TV Sala Cast launcher tests passed (mock server; no real Cast authentication tested)."
