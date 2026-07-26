#!/bin/bash
# Rebuild the Java sources, then run the merge driver.
# Writes /output/merge-report.json.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
REPORT="${MERGE_REPORT:-/output/merge-report.json}"

mkdir -p "$(dirname "${REPORT}")"

bash "${APP_ROOT}/scripts/build.sh"

java -cp "${APP_ROOT}/build/classes" io.terminus.stitch.driver.MergeDriver \
    --bases "${APP_ROOT}/data/bases" \
    --adapters "${APP_ROOT}/data/adapters" \
    --eval "${APP_ROOT}/data/eval" \
    --target S3 \
    --report "${REPORT}"

echo "report at ${REPORT}"
