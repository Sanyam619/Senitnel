#!/bin/bash
# Materialize live /etc and /var from seed fixtures; pin maps digest.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/auto.master.d /etc/autofs/floors /etc/autofs/maps \
  /var/lib/autofs/maps /var/lib/autofs/floors /var/lib/autofs/holds \
  /var/lib/autofs/ops/abort.d /var/lib/autofs/state /var/run/autofs \
  /var/log/autofs /output

cp -a "$DATA/maps/." /var/lib/autofs/maps/
cp -a "$DATA/maps/." /etc/autofs/maps/
cp -a "$DATA/roster.list" /etc/autofs/roster.list
cp -a "$SEED/auto.master.d/." /etc/auto.master.d/
cp -a "$SEED/abort.d/." /var/lib/autofs/ops/abort.d/
cp -a "$SEED/journal.jsonl" /var/lib/autofs/ops/journal.jsonl
cp -a "$SEED/clock.epoch" /var/lib/autofs/state/clock.epoch
printf '7\n' >/var/lib/autofs/state/gen.target
printf '3\n' >/var/lib/autofs/state/gen.live
rm -f /var/lib/autofs/state/cutover.ok

# Durable floors
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/var/lib/autofs/floors/${k}.floor"
done <"$SEED/floors.toml"

# Live decoy floors (disagree with durable)
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/etc/autofs/floors/${k}.floor"
done <"$SEED/live_floors.toml"

# Holds
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf 'until_epoch=%s\n' "$v" >"/var/lib/autofs/holds/${k}.hold"
done <"$SEED/holds.toml"

# Stale tip generations (pre-cutover)
for n in alpha beta gamma delta epsilon; do
  printf '1\n' >"/var/lib/autofs/state/tip_${n}.gen"
done

# Packaging digest for immutable fixtures
(
  cd "$DATA/maps"
  sha256sum *.map | sort -k2
) >"$ROOT/packaging/maps.sha256"

# Also keep a copy of fixtures at /app/data/maps (already present via COPY)
cp -a "$ROOT/packaging/maps.sha256" /app/packaging/maps.sha256 2>/dev/null || true
