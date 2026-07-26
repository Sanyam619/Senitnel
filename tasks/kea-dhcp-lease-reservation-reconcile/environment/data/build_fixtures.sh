#!/bin/bash
# Materialize live /etc and /var from seed fixtures; pin kea digest.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/kea/kea-dhcp4.d /etc/kea/floors /etc/kea/pools \
  /var/lib/kea/floors /var/lib/kea/pools /var/lib/kea/ops/abort.d \
  /var/lib/kea/state /var/run/kea /var/log/kea /output

cp -a "$SEED/kea-dhcp4.conf" /etc/kea/kea-dhcp4.conf
cp -a "$SEED/kea-dhcp4.d/." /etc/kea/kea-dhcp4.d/
cp -a "$SEED/abort.d/." /var/lib/kea/ops/abort.d/
cp -a "$SEED/journal.jsonl" /var/lib/kea/ops/journal.jsonl
cp -a "$SEED/memfile.csv" /var/lib/kea/ops/memfile.csv
cp -a "$SEED/prefer.toml" /var/lib/kea/ops/prefer.toml
cp -a "$DATA/roster.list" /etc/kea/roster.list
printf '7\n' >/var/lib/kea/state/gen.target
printf '3\n' >/var/lib/kea/state/gen.live
rm -f /var/lib/kea/state/cutover.ok

# Durable + live pools / floors from fixtures
for f in "$DATA"/kea/subnet_*.toml; do
  id=$(grep -E '^id\s*=' "$f" | head -n1 | sed 's/.*=\s*//')
  durable=$(grep -E '^durable_pool\s*=' "$f" | head -n1 | sed 's/.*=\s*"\(.*\)"/\1/')
  live=$(grep -E '^live_pool\s*=' "$f" | head -n1 | sed 's/.*=\s*"\(.*\)"/\1/')
  floor=$(grep -E '^floor\s*=' "$f" | head -n1 | sed 's/.*=\s*//')
  printf '%s\n' "$durable" >"/var/lib/kea/pools/${id}.pool"
  printf '%s\n' "$live" >"/etc/kea/pools/${id}.pool"
  printf '%s\n' "$floor" >"/var/lib/kea/floors/${id}.floor"
done

# Live decoy floors
while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  k=$(echo "$k" | tr -d '[:space:]')
  v=$(echo "$v" | tr -d '[:space:]')
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/etc/kea/floors/${k}.floor"
done <"$SEED/live_floors.toml"

# Prior tip generations (pre-cutover)
for n in 10 20 30; do
  printf '1\n' >"/var/lib/kea/state/tip_${n}.gen"
done

# Packaging digest for immutable fixtures (subnet defs + fold seeds)
{
  (
    cd "$DATA/kea"
    sha256sum ./*.toml
  )
  (
    cd "$DATA/seed/kea-dhcp4.d"
    sha256sum 10-core.conf 40-lab.conf
  )
  (
    cd "$ROOT/config"
    sha256sum site_standard.conf
  )
} | sort >"$ROOT/packaging/kea.sha256"
