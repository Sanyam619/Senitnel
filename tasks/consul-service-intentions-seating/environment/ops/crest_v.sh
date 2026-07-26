#!/bin/bash
set -euo pipefail
J_F="${ROSTER_J:-/var/lib/consul/ops/roster.jsonl}"
O_F="${TIP_TSV:-/var/lib/consul/ops/live/tip.tsv}"
G_F="${GEN_LIVE:-/var/lib/consul/ops/state/generation.live}"
mkdir -p "$(dirname "$O_F")" "$(dirname "$G_F")"
: >"$O_F"
if [[ ! -f "$J_F" ]]; then
  printf '0\n' >"$G_F"
  exit 0
fi
picked="$(jq -c -s 'map(select(.kind=="batch")) | sort_by(.gen) | .[-1] // empty' "$J_F")"
if [[ -z "$picked" || "$picked" == "null" ]]; then
  printf '0\n' >"$G_F"
  exit 0
fi
printf '%s\n' "$(jq -r '.gen // 0' <<<"$picked")" >"$G_F"
jq -r '.rows[]? | [.name, .node, (.gen|tonumber)] | @tsv' <<<"$picked" \
  | LC_ALL=C sort -t$'\t' -k1,1 >"$O_F"
