#!/usr/bin/env bash
set -euo pipefail
pref_q() {
  f=/etc/ingest/pref.d/10-harbor.conf
  mode=rollback
  if [[ -f "$f" ]] && grep -q 'cutover=seal' "$f" 2>/dev/null; then
    mode=seal
  fi
  mkdir -p /var/lib/ingest/meta
  echo -n "$mode" > /var/lib/ingest/meta/pref.armed
}
pref_q
