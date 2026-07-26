#!/bin/bash
# Regenerates the deterministic dataset under /app/data/{bases,adapters,eval}.
# Invoked from the Dockerfile after the sources are compiled. Reads seeds
# from /app/config/seeds.json and drives io.terminus.stitch.io.DataGenerator.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"

bash "${APP_ROOT}/scripts/build.sh"

rm -rf "${APP_ROOT}/data/bases" "${APP_ROOT}/data/adapters" "${APP_ROOT}/data/eval"
mkdir -p "${APP_ROOT}/data/bases" "${APP_ROOT}/data/adapters" "${APP_ROOT}/data/eval"

java -cp "${APP_ROOT}/build/classes" io.terminus.stitch.io.DataGenerator \
    --seeds "${APP_ROOT}/config/seeds.json" \
    --bases "${APP_ROOT}/data/bases" \
    --adapters "${APP_ROOT}/data/adapters" \
    --eval "${APP_ROOT}/data/eval"

echo "regenerated dataset under ${APP_ROOT}/data"
