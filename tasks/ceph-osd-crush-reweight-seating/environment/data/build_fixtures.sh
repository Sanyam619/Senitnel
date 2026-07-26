#!/bin/bash
# Materialize the live /etc and /var trees from seed fixtures, pack the
# durable placement image, and pin the frozen fixture digests.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/ceph/reweight.d /etc/ceph/pools.d \
  /var/lib/ceph/ops/state /var/run/ceph /var/log/ceph /output

cp -a "$SEED/ceph.conf" /etc/ceph/ceph.conf
cp -a "$SEED/reweight.d/." /etc/ceph/reweight.d/
cp -a "$SEED/pools.d/." /etc/ceph/pools.d/
cp -a "$SEED/prefer.toml" /var/lib/ceph/ops/prefer.toml
cp -a "$SEED/surface.map" /var/lib/ceph/ops/surface.map
cp -a "$DATA/ceph/out_journal.jsonl" /var/lib/ceph/ops/record.jsonl
cp -a "$DATA/ceph/holds.jsonl" /var/lib/ceph/ops/window.jsonl

awk -F'= *' '/^clock/ {print $2}' "$DATA/ceph/epochs.toml" | tr -d ' ' \
  >/var/lib/ceph/ops/now.mark
awk -F'= *' '/^floor/ {print $2}' "$DATA/ceph/epochs.toml" | tr -d ' ' \
  >/var/lib/ceph/ops/gen.low
awk -F'= *' '/^target/ {print $2}' "$DATA/ceph/epochs.toml" | tr -d ' ' \
  >/var/lib/ceph/ops/gen.aim

printf '3\n' >/var/lib/ceph/ops/state/gen.live
rm -f /var/lib/ceph/ops/state/apply.ok

# Pack the durable placement image: 8-byte magic then a deterministic
# gzip stream of the row text carried by the mirror.
printf 'CRUSHB1\000' >/var/lib/ceph/ops/crushmap.bin
gzip -cn9 "$DATA/crush/crush_map.txt" >>/var/lib/ceph/ops/crushmap.bin

# Pin the frozen fixture digests.
(
  cd "$DATA"
  find ceph crush -type f | LC_ALL=C sort | xargs sha256sum
) >"$ROOT/packaging/fixtures.sha256"
