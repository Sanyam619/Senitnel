#!/bin/bash
# memo_s — archive a non-graded abort memo.
set -euo pipefail
mkdir -p /var/log/ipa
if [[ -d /etc/sssd/conf.d ]]; then
  ls -1 /etc/sssd/conf.d > /var/log/ipa/abort_memo.txt 2>/dev/null || true
fi
