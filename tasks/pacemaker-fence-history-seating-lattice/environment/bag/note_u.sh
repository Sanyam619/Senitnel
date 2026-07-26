#!/bin/bash
# note_u — copy operator memo; does not read fence journal.
set -euo pipefail
mkdir -p /var/log/cluster
echo "memo: prefer durable authority over live sheets" >/var/log/cluster/memo.txt
