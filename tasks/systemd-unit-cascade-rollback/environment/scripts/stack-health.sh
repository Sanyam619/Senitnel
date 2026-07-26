#!/usr/bin/env bash
set -euo pipefail
root="/data/stack/units"
for name in stack.target ingress.service cache.service store.service journal.service relay.service; do
  if [[ ! -f "$root/$name" ]]; then
    echo "missing unit body: $name" >&2
    exit 1
  fi
done
echo "unit bodies present; activation still failing"
exit 1
