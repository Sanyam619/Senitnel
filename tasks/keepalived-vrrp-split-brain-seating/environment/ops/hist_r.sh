#!/bin/bash
set -euo pipefail
J_F="${TRANS_J:-/var/lib/keepalived/ops/transitions.jsonl}"
O_F="${MOVES_TSV:-/var/lib/keepalived/ops/live/moves.tsv}"
mkdir -p "$(dirname "$O_F")"
: >"$O_F"
[[ -f "$J_F" ]] || exit 0

declare -A active_json=()
declare -A eid_vrid=()

while IFS= read -r line || [[ -n "${line:-}" ]]; do
  [[ -z "${line:-}" ]] && continue
  kind="$(jq -r '.kind // empty' <<<"$line")"
  if [[ "$kind" == "move" ]]; then
    eid="$(jq -r '.eid' <<<"$line")"
    vrid="$(jq -r '.vrid' <<<"$line")"
    active_json["$eid"]="$line"
    eid_vrid["$eid"]="$vrid"
  elif [[ "$kind" == "retract" ]]; then
    eid="$(jq -r '.eid' <<<"$line")"
    if [[ -n "${eid_vrid[$eid]:-}" ]]; then
      vrid="${eid_vrid[$eid]}"
      for other in "${!eid_vrid[@]}"; do
        if [[ "${eid_vrid[$other]}" == "$vrid" ]]; then
          unset "active_json[$other]"
          unset "eid_vrid[$other]"
        fi
      done
    else
      unset "active_json[$eid]"
      unset "eid_vrid[$eid]"
    fi
  fi
done <"$J_F"

for eid in "${!active_json[@]}"; do
  jq -r '[.vrid, .epoch, .from, .to, .eid] | @tsv' <<<"${active_json[$eid]}"
done | sort -t$'\t' -k1,1n -k2,2n -k5,5 >"$O_F"
