#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v npm >/dev/null || { echo 'Serve Node.js e npm'; exit 1; }
if [ ! -f package.json ]; then printf '{"private":true,"name":"koi-pond-wallpaper","version":"1.0.0"}\n' > package.json; fi
npm install --no-save --ignore-scripts esbuild
./node_modules/.bin/esbuild main.ts --bundle --platform=browser --format=iife --target=es2020 --outfile=pond.js
printf '\nPronto. Esegui: ./start.sh\n'
