#!/bin/bash
# note_t — archive a non-graded hold memo.
set -euo pipefail
mkdir -p /var/log/ldap
if [[ -d /var/lib/ldap/holds ]]; then
  ls -1 /var/lib/ldap/holds > /var/log/ldap/hold_memo.txt 2>/dev/null || true
fi
