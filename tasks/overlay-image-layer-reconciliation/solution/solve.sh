#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

patch -p1 < "$ROOT_DIR/patches/seq.go.patch"
patch -p1 < "$ROOT_DIR/patches/merge.go.patch"
patch -p1 < "$ROOT_DIR/patches/bundle.go.patch"
patch -p1 < "$ROOT_DIR/patches/main.go.patch"

go build -mod=readonly -trimpath -ldflags="-s -w" -o bin/packctl ./cmd/packctl

mkdir -p /output
rm -f /output/reconcile-report.json
/opt/packlab/bin/packctl --root /data/images --out /output/reconcile-report.json

test -s /output/reconcile-report.json
