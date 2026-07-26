#!/bin/bash
tag_r() {
  set -euo pipefail

  ROOT="${IPA_ROOT:-/var/lib/ipa}"
  LIVE_FLOORS="${LIVE_FLOORS:-/etc/ipa/floors}"
  HOSTS="${HOSTS:-/etc/ipa/hosts.list}"
  STATE="$ROOT/state"

  mkdir -p "$STATE"

  while IFS=$'\t' read -r name fqdn || [[ -n "$name" ]]; do
    name="$(echo "$name" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$name" || "$name" =~ ^# ]] && continue
    fpr="missing"
    [[ -f "$ROOT/${name}/keytab.fpr" ]] && fpr=$(tr -d '[:space:]' <"$ROOT/${name}/keytab.fpr")
    gen=1
    [[ -f "$STATE/tip_${name}.gen" ]] && gen=$(tr -d '[:space:]' <"$STATE/tip_${name}.gen")
    floor=0
    [[ -f "$LIVE_FLOORS/${name}.floor" ]] && floor=$(tr -d '[:space:]' <"$LIVE_FLOORS/${name}.floor")
    if (( gen > floor )); then
      printf '1\n' >"$STATE/elig_${name}"
    else
      printf '0\n' >"$STATE/elig_${name}"
    fi
    printf '%s\n' "$gen" >"$STATE/pub_${name}.gen"
    printf '%s\n' "$fpr" >"$STATE/pub_${name}.fpr"
  done <"$HOSTS"
}
tag_r
