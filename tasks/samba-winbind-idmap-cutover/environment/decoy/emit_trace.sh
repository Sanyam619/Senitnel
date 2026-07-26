#!/bin/bash
# Dumps raw conf snippets to stderr; does not write /output.
set -euo pipefail
ETC="${SAMBA_ETC:-/etc/samba}"
for f in "$ETC"/smb.conf.d/*.conf; do
  [[ -f "$f" ]] || continue
  echo "=== $f ===" >&2
  cat "$f" >&2
done
