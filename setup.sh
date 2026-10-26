#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v curl >/dev/null || { echo 'Serve curl'; exit 1; }
command -v npm >/dev/null || { echo 'Serve Node.js e npm'; exit 1; }
BASE='https://raw.githubusercontent.com/Dao-Ho/portfolio/main/src/app/components/koi-pond'
for file in renderer.ts shape.ts world.ts; do
  echo "Scarico $file dalla repository originale..."
  curl --fail --location --retry 2 --silent --show-error "$BASE/$file" -o "$file"
done
if [ ! -f package.json ]; then printf '{"private":true,"name":"daoho-pond-wallpaper","version":"1.0.0"}\n' > package.json; fi
npm install --no-save --ignore-scripts esbuild
./node_modules/.bin/esbuild main.ts --bundle --platform=browser --format=iife --target=es2020 --outfile=pond.js
printf '\nPronto. Esegui: ./start.sh\n'
