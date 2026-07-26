#!/bin/bash
set -euo pipefail
ROOT="${NBODY_ROOT:-/app}"
echo "manifests:"
ls -1 "$ROOT/config/manifests" || true
echo "cases:"
ls -1 "$ROOT/data/cases" || true
