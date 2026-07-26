#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?destination}"
MODE="${2:?active|stale}"
SRC_ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT"

install_payload_tree() {
  local bucket="$1"
  local base="$SRC_ROOT/$bucket"
  [[ -d "$base" ]] || return 0
  while IFS= read -r -d '' payload; do
    local rel="${payload#"$base"/}"
    rel="${rel%.payload}"
    mkdir -p "$ROOT/$(dirname "$rel")"
    cp "$payload" "$ROOT/$rel"
  done < <(find "$base" -type f -name '*.payload' -print0 | sort -z)
}

install_payload_tree payloads
if [[ "$MODE" == "stale" ]]; then
  install_payload_tree stale-payloads
fi
