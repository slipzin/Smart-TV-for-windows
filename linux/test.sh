#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s linux -p 'test_*.py'
python3 -m py_compile linux/smarttv.py
bash -n linux/run.sh linux/install-user.sh linux/build-iso.sh
echo "Linux runtime syntax and unit tests passed."
