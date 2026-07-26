#!/bin/bash
# Materialize live /etc and /var from seed fixtures; pin nft digest.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/nftables.d /etc/nft/floors \
  /var/lib/nft/ops/abort.d /var/lib/nft/floors /var/lib/nft/state \
  /var/lib/nft/ops /var/run/nft /var/log/nft /output

cp -a "$SEED/nftables.conf" /etc/nftables.conf
cp -a "$SEED/nftables.d/." /etc/nftables.d/
cp -a "$SEED/abort.d/." /var/lib/nft/ops/abort.d/
cp -a "$SEED/journal.jsonl" /var/lib/nft/ops/journal.jsonl
cp -a "$SEED/prefer.conf" /var/lib/nft/ops/prefer.conf
cp -a "$ROOT/config/surface_prefer.conf" /etc/nft/surface_prefer.conf
cp -a "$DATA/roster.list" /etc/nft/roster.list
printf '7\n' >/var/lib/nft/state/gen.target
printf '3\n' >/var/lib/nft/state/gen.live
printf '1700000000\n' >/var/lib/nft/state/clock.epoch
rm -f /var/lib/nft/state/cutover.ok
: >/var/lib/nft/ops/kernel.nft
rm -f /var/lib/nft/ops/fold.nft /var/lib/nft/ops/applied.nft

# Durable floors
while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  k="${k%%#*}"
  k="$(echo "$k" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/var/lib/nft/floors/${k}.floor"
done <"$SEED/floors.toml"

# Live decoy floors
while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  k="${k%%#*}"
  k="$(echo "$k" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/etc/nft/floors/${k}.floor"
done <"$SEED/live_floors.toml"

# Map fragment stem -> table name for seating helpers
printf '10-core.nft filter\n20-nat.nft nat\n30-mangle.nft mangle\n40-raw.nft raw\n' \
  >/var/lib/nft/state/frag_map.tsv

# Packaging digest for immutable fixtures
(
  cd "$DATA/nft"
  sha256sum *.nft | sort -k2
) >"$ROOT/packaging/nft.sha256"
cp -a "$ROOT/packaging/nft.sha256" /app/packaging/nft.sha256 2>/dev/null || true
