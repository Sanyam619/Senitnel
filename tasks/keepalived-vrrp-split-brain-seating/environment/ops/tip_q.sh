#!/bin/bash
set -euo pipefail
J_F="${PREFER_J:-/var/lib/keepalived/ops/prefer.jsonl}"
P_D="${PEER_D:-/app/data/vrrp}"
X_D="${EXTRA_D:-/var/lib/keepalived/ops/extra}"
O_F="${CAND_TSV:-/var/lib/keepalived/ops/live/cand.tsv}"
LIVE="${GEN_LIVE:-/var/lib/keepalived/ops/state/generation.live}"
mkdir -p "$(dirname "$O_F")" "$(dirname "$LIVE")"
: >"$O_F"

declare -A peer_vrid=() peer_vip=()
shopt -s nullglob
for root in "$P_D" "$X_D"; do
  [[ -d "$root" ]] || continue
  for f in "$root"/*.conf; do
    id=""; vrid=""; vip=""
    while IFS= read -r line || [[ -n "${line:-}" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ -z "$line" || "$line" != *=* ]] && continue
      k="${line%%=*}"; v="${line#*=}"
      case "$k" in
        id) id="$v" ;;
        vrid) vrid="$v" ;;
        vip) vip="$v" ;;
      esac
    done <"$f"
    [[ -n "$id" ]] || continue
    peer_vrid["$id"]="$vrid"
    peer_vip["$id"]="$vip"
  done
done
shopt -u nullglob

if [[ ! -f "$J_F" ]]; then
  printf '0\n' >"$LIVE"
  exit 0
fi

picked="$(jq -c -s 'sort_by(.gen) | .[-1] // empty' "$J_F")"
if [[ -z "$picked" || "$picked" == "null" ]]; then
  printf '0\n' >"$LIVE"
  exit 0
fi
gen="$(jq -r '.gen // 0' <<<"$picked")"
printf '%s\n' "$gen" >"$LIVE"

while IFS=$'\t' read -r pid tip rank || [[ -n "${pid:-}" ]]; do
  [[ -z "${pid:-}" ]] && continue
  printf '%s\t%s\t%s\t%s\t%s\n' \
    "$pid" "$tip" "$rank" "${peer_vrid[$pid]:-0}" "${peer_vip[$pid]:-}" >>"$O_F"
done < <(jq -r '.rows[]? | [.id, (.tip|tonumber), (.rank|tonumber)] | @tsv' <<<"$picked")
