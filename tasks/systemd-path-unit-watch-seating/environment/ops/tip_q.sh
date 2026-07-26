#!/bin/bash
set -euo pipefail
J="${PREFER_J:-/var/lib/systemd/ops/prefer.jsonl}"
OUT="${TIP_TSV:-/var/lib/systemd/ops/live/tip.tsv}"
GL="${GEN_LIVE:-/var/lib/systemd/ops/state/generation.live}"
mkdir -p "$(dirname "$OUT")" "$(dirname "$GL")"
: >"$OUT"

if [[ ! -f "$J" ]]; then
  printf '0\n' >"$GL"
  exit 0
fi

picked="$(jq -c -s 'sort_by(.gen) | .[-1] // empty' "$J")"
if [[ -z "$picked" || "$picked" == "null" ]]; then
  printf '0\n' >"$GL"
  exit 0
fi
gen="$(jq -r '.gen // 0' <<<"$picked")"
printf '%s\n' "$gen" >"$GL"

# Empty path cells become "-" so bash IFS=$'\t' read does not collapse columns.
jq -r '
  .rows[]? |
  [
    .id,
    (if (.exists // "") == "" then "-" else .exists end),
    (if (.changed // "") == "" then "-" else .changed end),
    (.tip | tostring)
  ] | @tsv
' <<<"$picked" >>"$OUT"
