#!/bin/bash
# knit_stream.sh — seat credential/WAL stream order into live ceremony state.
set -euo pipefail

mkdir -p /var/lib/ceremony/state
printf 'jsonl-then-wal\n' >/var/lib/ceremony/state/stream.order
