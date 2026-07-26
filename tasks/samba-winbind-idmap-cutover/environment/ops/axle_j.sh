#!/bin/bash
set -euo pipefail
META="${SAMBA_VAR:-/var/lib/samba}/meta"
OPS="${SAMBA_VAR:-/var/lib/samba}/ops"
ENV_FILE="${SAMBA_DESKD_ENV:-/etc/samba/deskd.env}"
mkdir -p "$META"
jsonl="$OPS/journal.jsonl"
if [[ ! -f "$jsonl" ]]; then
  echo "axle_j: missing journal.jsonl" >&2
  exit 1
fi
last="$(tail -n1 "$jsonl")"
mode=$(printf '%s' "$last" | sed -n 's/.*"mode"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
gen=$(printf '%s' "$last" | sed -n 's/.*"gen"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p')
hold=$(printf '%s' "$last" | sed -n 's/.*"hold"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[[ -n "$mode" ]] || mode=rollback
[[ -n "$gen" ]] || gen=0
[[ -n "$hold" ]] || hold=lab-tmp
printf '%s\n' "$gen" >"$META/gen.live"
printf 'seal\n' >"$META/attach.intent"
printf '%s\n' "$hold" >"$META/hold.token"
rm -f "$META/cutover.ok"
tmp="$(mktemp)"
if [[ -f "$ENV_FILE" ]]; then
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    [[ "$line" == PAYLOAD_LINEAGE=* || "$line" == HOLD_TOKEN=* ]] && continue
    printf '%s\n' "$line"
  done <"$ENV_FILE" >"$tmp"
else
  : >"$tmp"
fi
printf 'PAYLOAD_LINEAGE=%s\nHOLD_TOKEN=%s\n' "$mode" "$hold" >>"$tmp"
mv -f "$tmp" "$ENV_FILE"
