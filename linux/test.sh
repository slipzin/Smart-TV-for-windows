#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s linux -p 'test_*.py'
python3 -m py_compile linux/smarttv.py
if command -v node >/dev/null 2>&1; then node --check web/tv.js; node --check web/home.js; fi
bash -n linux/run.sh linux/install-user.sh linux/build-iso.sh linux/cast/start.sh linux/cast/test.sh linux/gaming/install-extras.sh linux/cloud-gaming/launch-cloud-game.sh linux/cloud-gaming/test.sh linux/validate-profile-packages.sh
bash linux/cast/test.sh
bash linux/cloud-gaming/test.sh
echo "Linux runtime syntax and unit tests passed."
