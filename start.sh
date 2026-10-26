#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
test -f pond.js || { echo 'Esegui prima ./setup.sh'; exit 1; }
python3 -m http.server 8765 --bind 127.0.0.1
