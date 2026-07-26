#!/bin/bash
set -euo pipefail
J="${TRIGGER_J:-/var/lib/systemd/ops/triggers.jsonl}"
OUT="${TRIG_TSV:-/var/lib/systemd/ops/live/trig.tsv}"
mkdir -p "$(dirname "$OUT")"
: >"$OUT"
[[ -f "$J" ]] || exit 0

declare -A fire_epoch=()
declare -A eid_unit=()

while IFS= read -r line || [[ -n "${line:-}" ]]; do
  [[ -z "${line:-}" ]] && continue
  kind="$(jq -r '.kind // empty' <<<"$line")"
  if [[ "$kind" == "fire" ]]; then
    eid="$(jq -r '.eid' <<<"$line")"
    unit="$(jq -r '.unit' <<<"$line")"
    epoch="$(jq -r '.epoch' <<<"$line")"
    fire_epoch["$eid"]="$epoch"
    eid_unit["$eid"]="$unit"
  elif [[ "$kind" == "retract" ]]; then
    eid="$(jq -r '.eid' <<<"$line")"
    if [[ -n "${eid_unit[$eid]:-}" ]]; then
      unit="${eid_unit[$eid]}"
      for other in "${!eid_unit[@]}"; do
        if [[ "${eid_unit[$other]}" == "$unit" ]]; then
          unset "fire_epoch[$other]"
          unset "eid_unit[$other]"
        fi
      done
    fi
  fi
done <"$J"

declare -A last=() has=()
for eid in "${!eid_unit[@]}"; do
  unit="${eid_unit[$eid]}"
  ep="${fire_epoch[$eid]}"
  has["$unit"]=1
  if [[ -z "${last[$unit]:-}" || "$ep" -gt "${last[$unit]}" ]]; then
    last["$unit"]="$ep"
  fi
done

for unit in $(printf '%s\n' "${!has[@]}" | LC_ALL=C sort); do
  printf '%s\t%s\t%s\n' "$unit" "${last[$unit]}" "1" >>"$OUT"
done
