#!/bin/bash
# Materialize the live /etc and /var desk from seed fixtures; pin frozen digests.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/glusterfs/glusterd.d /etc/glusterfs/bricks.d /etc/glusterfs/floors \
  /var/lib/glusterd/volumes /var/lib/glusterd/floors /var/lib/glusterd/holds \
  /var/lib/glusterd/state /var/lib/glusterd/ops/abort.d /var/lib/glusterd/ops/state \
  /var/run/gluster /var/log/gluster /output

cp -a "$DATA/gluster/volumes/." /var/lib/glusterd/volumes/
cp -a "$DATA/roster.list" /etc/glusterfs/roster.list
cp -a "$SEED/glusterd.d/." /etc/glusterfs/glusterd.d/
cp -a "$SEED/bricks.d/." /etc/glusterfs/bricks.d/
cp -a "$SEED/abort.d/." /var/lib/glusterd/ops/abort.d/
cp -a "$SEED/prefer.toml" /var/lib/glusterd/ops/prefer.toml
cp -a "$SEED/surface.bricks" /var/lib/glusterd/ops/surface.bricks
cp -a "$SEED/brick_journal.jsonl" /var/lib/glusterd/ops/brick_journal.jsonl
cp -a "$SEED/clock.epoch" /var/lib/glusterd/state/clock.epoch
printf '9\n' >/var/lib/glusterd/state/gen.target
printf '3\n' >/var/lib/glusterd/state/gen.live
rm -f /var/lib/glusterd/ops/state/apply.ok

while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/var/lib/glusterd/floors/${k}.floor"
done <"$SEED/floors.toml"

while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/etc/glusterfs/floors/${k}.floor"
done <"$SEED/live_floors.toml"

# Holds: brick_id|path|until_epoch
while IFS='|' read -r hid bpath until || [[ -n "${hid:-}" ]]; do
  [[ -z "${hid:-}" || "$hid" =~ ^# ]] && continue
  printf 'brick=%s\nuntil_epoch=%s\n' "$bpath" "$until" \
    >"/var/lib/glusterd/holds/${hid}.hold"
done <"$SEED/holds.tsv"

while IFS= read -r n || [[ -n "${n:-}" ]]; do
  [[ -z "${n:-}" || "$n" =~ ^# ]] && continue
  printf '2\n' >"/var/lib/glusterd/state/tip_${n}.gen"
done <"$DATA/roster.list"

(
  cd "$DATA/gluster"
  sha256sum volumes/*.toml | LC_ALL=C sort -k2
) >"$ROOT/packaging/gluster.sha256"
