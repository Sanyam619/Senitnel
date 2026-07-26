#!/bin/bash
set -euo pipefail
ROOT="${SAMBA_VAR:-/var/lib/samba}"
ROSTER="${IDMAP_ROSTER:-/etc/samba/idmap.roster}"
ENV_FILE="${SAMBA_DESKD_ENV:-/etc/samba/deskd.env}"
ATTACH="$ROOT/attach"
ORIGINS="$ROOT/origins"
mkdir -p "$ATTACH"
hold=""
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  hold="${HOLD_TOKEN:-}"
fi
[[ -n "$hold" ]] || { echo "link_v: missing HOLD_TOKEN" >&2; exit 1; }
lineage="${PAYLOAD_LINEAGE:-decoy}"
rm -rf "$ATTACH"/*/
while read -r nm sid lo hi uid || [[ -n "${nm:-}" ]]; do
  [[ -z "${nm:-}" || "$nm" == \#* ]] && continue
  src="$ORIGINS/$nm/$lineage/map.bin"
  [[ -f "$src" ]] || src="$ORIGINS/$nm/decoy/map.bin"
  dst="$ATTACH/$nm.bin"
  rm -f "$dst"
  cp -f "$src" "$dst"
  printf '%s\n' "$hold" >"$ATTACH/.hold.$nm"
done <"$ROSTER"
