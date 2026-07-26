#!/bin/bash
# fold_d.sh — abort rematerialize + lexical fold of ceremony drop-ins.
set -euo pipefail

mkdir -p /etc/ceremony/reconcile.d /var/lib/ceremony/ops/abort.d /var/lib/ceremony/state
abort_pkg="/var/lib/ceremony/ops/abort.d/90-local.conf"
live_dropin="/etc/ceremony/reconcile.d/90-local.conf"
cutover_receipt="/var/lib/ceremony/state/cutover.ok"

if [[ -f "$abort_pkg" ]]; then
  cp -f "$abort_pkg" "$live_dropin"
fi
rm -f "$cutover_receipt"

# Lexical fold of drop-ins into effective reconcile.conf
: >/etc/ceremony/reconcile.conf
shopt -s nullglob
for f in /etc/ceremony/reconcile.d/*.conf; do
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" ]] && continue
    [[ "$line" != *=* ]] && continue
    key="${line%%=*}"
    val="${line#*=}"
    if grep -q "^${key}=" /etc/ceremony/reconcile.conf 2>/dev/null; then
      grep -v "^${key}=" /etc/ceremony/reconcile.conf >/tmp/ceremony.fold || true
      mv /tmp/ceremony.fold /etc/ceremony/reconcile.conf
    fi
    echo "${key}=${val}" >>/etc/ceremony/reconcile.conf
  done <"$f"
done
shopt -u nullglob
