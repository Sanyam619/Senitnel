#!/bin/bash
set -euo pipefail
J_F="${INTENTS_J:-/var/lib/consul/ops/intents.jsonl}"
O_F="${CMT_TSV:-/var/lib/consul/ops/live/cmt.tsv}"
mkdir -p "$(dirname "$O_F")"
: >"$O_F"
[[ -f "$J_F" ]] || exit 0

declare -A row=() head_of=()
while IFS= read -r line || [[ -n "${line:-}" ]]; do
  [[ -z "${line:-}" ]] && continue
  kind="$(jq -r '.kind // empty' <<<"$line")"
  eid="$(jq -r '.eid // empty' <<<"$line")"
  [[ -n "$eid" ]] || continue
  if [[ "$kind" == "commit" ]]; then
    row["$eid"]="$line"
    head_of["$eid"]="$(jq -r '.source' <<<"$line")"
  elif [[ "$kind" == "retract" ]]; then
    if [[ -n "${head_of[$eid]:-}" ]]; then
      s="${head_of[$eid]}"
      for other in "${!head_of[@]}"; do
        if [[ "${head_of[$other]}" == "$s" ]]; then
          unset "row[$other]"
          unset "head_of[$other]"
        fi
      done
    else
      unset "row[$eid]"
      unset "head_of[$eid]"
    fi
  fi
done <"$J_F"

{
  for eid in "${!row[@]}"; do
    jq -r '[.source, .destination, .eid, (.epoch|tonumber)] | @tsv' <<<"${row[$eid]}"
  done
} | LC_ALL=C sort -t$'\t' -k1,1 -k2,2 -k3,3 >"$O_F"
