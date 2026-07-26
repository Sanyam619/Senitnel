#!/bin/bash
# Materialize the live /etc and /var desk from seed fixtures; pin frozen digests.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/lvm/lvm.conf.d /etc/lvm/cache.d /etc/lvm/floors \
  /var/lib/lvm/volumes /var/lib/lvm/floors /var/lib/lvm/holds \
  /var/lib/lvm/state /var/lib/lvm/ops/abort.d /var/lib/lvm/ops/state \
  /var/run/lvm /var/log/lvm /output

cp -a "$DATA/lvm/volumes/." /var/lib/lvm/volumes/
cp -a "$DATA/lvm/pool.map" /var/lib/lvm/ops/pool.map
cp -a "$DATA/roster.list" /etc/lvm/roster.list
cp -a "$SEED/lvm.conf.d/." /etc/lvm/lvm.conf.d/
cp -a "$SEED/cache.d/." /etc/lvm/cache.d/
cp -a "$SEED/abort.d/." /var/lib/lvm/ops/abort.d/
cp -a "$SEED/prefer.toml" /var/lib/lvm/ops/prefer.toml
cp -a "$SEED/surface.modes" /var/lib/lvm/ops/surface.modes
cp -a "$SEED/journal.jsonl" /var/lib/lvm/ops/journal.jsonl
cp -a "$SEED/clock.epoch" /var/lib/lvm/state/clock.epoch
printf '9\n' >/var/lib/lvm/state/gen.target
printf '3\n' >/var/lib/lvm/state/gen.live
rm -f /var/lib/lvm/ops/state/apply.ok

# Durable generation floors.
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/var/lib/lvm/floors/${k}.floor"
done <"$SEED/floors.toml"

# Live floor sheets kept for the surface probe.
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/etc/lvm/floors/${k}.floor"
done <"$SEED/live_floors.toml"

# Maintenance windows.
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf 'until_epoch=%s\n' "$v" >"/var/lib/lvm/holds/${k}.hold"
done <"$SEED/holds.toml"

# Pre-cutover tip generations left on the desk.
while IFS= read -r n || [[ -n "${n:-}" ]]; do
  [[ -z "${n:-}" || "$n" =~ ^# ]] && continue
  printf '2\n' >"/var/lib/lvm/state/tip_${n}.gen"
done <"$DATA/roster.list"

# Digest pin for the frozen fixture tree.
(
  cd "$DATA/lvm"
  sha256sum pool.map volumes/*.toml | LC_ALL=C sort -k2
) >"$ROOT/packaging/lvm.sha256"
