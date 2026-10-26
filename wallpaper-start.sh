#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ "${XDG_SESSION_TYPE:-x11}" = wayland ]; then
  echo 'Questa integrazione supporta Cinnamon X11, non Wayland.' >&2; exit 1
fi
exec /usr/bin/python3 "$(pwd)/wallpaper.py"
