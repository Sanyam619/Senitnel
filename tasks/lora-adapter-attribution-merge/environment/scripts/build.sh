#!/bin/bash
# Compiles every Java source under /app/src/main/java into /app/build/classes.
# The verifier invokes this before running the driver so the compiled
# classes always reflect the current sources.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
SRC="${APP_ROOT}/src/main/java"
OUT="${APP_ROOT}/build/classes"

rm -rf "${OUT}"
mkdir -p "${OUT}"

# Collect sources; keep the list stable across runs.
SRC_LIST="$(cd "${SRC}" && find . -type f -name '*.java' | sort)"
if [ -z "${SRC_LIST}" ]; then
    echo "no Java sources under ${SRC}" >&2
    exit 1
fi

# shellcheck disable=SC2086
(cd "${SRC}" && javac -encoding UTF-8 -d "${OUT}" ${SRC_LIST})

echo "compiled $(echo "${SRC_LIST}" | wc -l | tr -d ' ') sources into ${OUT}"
