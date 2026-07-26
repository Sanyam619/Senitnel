#!/bin/bash
set -euo pipefail
ROOT="${POOL_ROOT:-/var/lib/pool}"
RUNTIME="$ROOT/meta/runtime.tsv"
PREF_D="${POOL_PREF_D:-/etc/pool/pref.d}"
[[ -f "$RUNTIME" ]] || exit 0
mode="strict-gt"
if [[ -d "$PREF_D" ]]; then
  while IFS= read -r f; do
    [[ -f "$f" ]] || continue
    if grep -q 'mode=equality-inclusive' "$f" 2>/dev/null; then
      mode="equality-inclusive"
    fi
    if grep -q 'mode=strict-gt' "$f" 2>/dev/null; then
      mode="strict-gt"
    fi
  done < <(find "$PREF_D" -type f | sort)
fi
tmp="$(mktemp)"
while IFS=$'\t' read -r idx drill tip origin kind epoch floor || [[ -n "${idx:-}" ]]; do
  [[ -z "${idx:-}" ]] && continue
  if [[ "$mode" == "strict-gt" && "$epoch" -eq "$floor" ]]; then
    floor=$((floor + 1))
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$idx" "$drill" "$tip" "$origin" "$kind" "$epoch" "$floor"
done <"$RUNTIME" >"$tmp"
mv "$tmp" "$RUNTIME"
