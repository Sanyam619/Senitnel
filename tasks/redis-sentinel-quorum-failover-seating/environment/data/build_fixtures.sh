#!/bin/bash
# Materialize the live /etc and /var desk from seed fixtures; pin frozen digests.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/redis/sentinel.d /etc/redis/monitors.d /etc/redis/floors \
  /var/lib/redis/masters /var/lib/redis/floors /var/lib/redis/state \
  /var/lib/redis/ops/abort.d /var/lib/redis/ops/state \
  /var/run/redis /var/log/redis /output

cp -a "$DATA/redis/masters/." /var/lib/redis/masters/
cp -a "$DATA/roster.list" /etc/redis/roster.list
cp -a "$DATA/replica.list" /etc/redis/replica.list
cp -a "$SEED/sentinel.d/." /etc/redis/sentinel.d/
cp -a "$SEED/monitors.d/." /etc/redis/monitors.d/
cp -a "$SEED/abort.d/." /var/lib/redis/ops/abort.d/
cp -a "$SEED/prefer.toml" /var/lib/redis/ops/prefer.toml
cp -a "$SEED/surface.monitors" /var/lib/redis/ops/surface.monitors
cp -a "$SEED/surface.quorum" /var/lib/redis/ops/surface.quorum
cp -a "$SEED/failover_journal.jsonl" /var/lib/redis/ops/failover_journal.jsonl
cp -a "$SEED/replicas.tsv" /var/lib/redis/ops/replicas.tsv
cp -a "$SEED/clock.epoch" /var/lib/redis/state/clock.epoch
printf '9\n' >/var/lib/redis/state/gen.target
printf '3\n' >/var/lib/redis/state/gen.live
rm -f /var/lib/redis/ops/state/apply.ok

while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/var/lib/redis/floors/${k}.floor"
done <"$SEED/floors.toml"

while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/etc/redis/floors/${k}.floor"
done <"$SEED/live_floors.toml"

while IFS= read -r n || [[ -n "${n:-}" ]]; do
  [[ -z "${n:-}" || "$n" =~ ^# ]] && continue
  printf '2\n' >"/var/lib/redis/state/tip_${n}.gen"
  printf '10.20.1.10:6379\n' >"/var/lib/redis/state/tip_${n}.addr"
done <"$DATA/roster.list"

(
  cd "$DATA/redis"
  sha256sum masters/*.toml | LC_ALL=C sort -k2
) >"$ROOT/packaging/redis.sha256"
