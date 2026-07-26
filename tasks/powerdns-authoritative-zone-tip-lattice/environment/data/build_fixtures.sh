#!/bin/bash
# Materialize live /etc and /var from seed fixtures; pin zone digest.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/powerdns/pdns.d /etc/powerdns/floors /etc/powerdns/zones.d \
  /etc/powerdns/serials \
  /var/lib/powerdns/zones /var/lib/powerdns/floors \
  /var/lib/powerdns/ops/abort.d /var/lib/powerdns/state \
  /var/lib/powerdns/surface/zones.d /var/lib/powerdns/surface/tips \
  /var/lib/powerdns/surface/serials \
  /var/run/powerdns /var/log/powerdns /output

cp -a "$SEED/pdns.conf" /etc/powerdns/pdns.conf
cp -a "$SEED/pdns.d/." /etc/powerdns/pdns.d/
cp -a "$SEED/zones.d/." /etc/powerdns/zones.d/
cp -a "$SEED/abort.d/." /var/lib/powerdns/ops/abort.d/
cp -a "$SEED/zone_journal.jsonl" /var/lib/powerdns/ops/zone_journal.jsonl
cp -a "$SEED/store_registry.jsonl" /var/lib/powerdns/ops/store_registry.jsonl
cp -a "$SEED/retired_stores.jsonl" /var/lib/powerdns/ops/retired_stores.jsonl
cp -a "$SEED/holds.jsonl" /var/lib/powerdns/ops/holds.jsonl
cp -a "$SEED/surface/zones.d/." /var/lib/powerdns/surface/zones.d/
cp -a "$SEED/surface/tips/." /var/lib/powerdns/surface/tips/
cp -a "$SEED/surface/serials/." /var/lib/powerdns/surface/serials/
cp -a "$ROOT/config/prefer.surface.toml" /var/lib/powerdns/ops/prefer.toml
cp -a "$SEED/tip_bind.accept" /var/lib/powerdns/ops/tip_bind.accept
cp -a "$SEED/state/clock.epoch" /var/lib/powerdns/state/clock.epoch
cp -a "$DATA/zone.roster" /etc/powerdns/zone.roster
printf '7\n' >/var/lib/powerdns/state/gen.target
printf '3\n' >/var/lib/powerdns/state/gen.live
printf 'stub-desk-store\n' >/var/lib/powerdns/pdns.sqlite3
rm -f /var/lib/powerdns/state/cutover.ok

# Durable apex data from frozen fixtures
for f in "$DATA"/pdns/*.toml; do
  name=$(basename "$f" .toml)
  ns=$(grep -E '^ns\s*=' "$f" | head -n1 | sed 's/.*=\s*"\(.*\)"/\1/')
  printf '%s\n' "$ns" >"/var/lib/powerdns/zones/${name}.ns"
done

# Durable floors
while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  k=$(echo "$k" | tr -d '[:space:]')
  v=$(echo "$v" | tr -d '[:space:]')
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/var/lib/powerdns/floors/${k}.floor"
done <"$SEED/floors.toml"

# Live floor sheets
while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  k=$(echo "$k" | tr -d '[:space:]')
  v=$(echo "$v" | tr -d '[:space:]')
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/etc/powerdns/floors/${k}.floor"
done <"$SEED/live_floors.toml"

# Live serial sheets
while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  k=$(echo "$k" | tr -d '[:space:]')
  v=$(echo "$v" | tr -d '[:space:]')
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/etc/powerdns/serials/${k}.serial"
done <"$SEED/serials.toml"

# Tip generations before cutover
for n in crest.example harbor.example mesa.example quarry.example tundra.example; do
  printf '1\n' >"/var/lib/powerdns/state/tip_${n}.gen"
done

# Packaging digest for immutable fixtures (operator inventory only)
(
  cd "$DATA/pdns"
  sha256sum ./*.toml | sort
) >"$ROOT/packaging/zones.sha256"
