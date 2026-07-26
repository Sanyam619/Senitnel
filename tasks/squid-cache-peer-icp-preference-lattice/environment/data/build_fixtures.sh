#!/bin/bash
# Materialize live /etc and /var from seed fixtures; pin peer digest.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/squid/conf.d /etc/squid/floors /etc/squid/peers.d \
  /var/lib/squid/peers /var/lib/squid/floors \
  /var/lib/squid/ops/abort.d /var/lib/squid/state \
  /var/lib/squid/surface/peers.d /var/lib/squid/surface/tips \
  /var/run/squid /var/log/squid /output

cp -a "$SEED/squid.conf" /etc/squid/squid.conf
cp -a "$SEED/conf.d/." /etc/squid/conf.d/
cp -a "$SEED/abort.d/." /var/lib/squid/ops/abort.d/
cp -a "$SEED/prefer.jsonl" /var/lib/squid/ops/prefer.jsonl
cp -a "$SEED/peers.jsonl" /var/lib/squid/ops/peers.jsonl
cp -a "$SEED/peers.d/." /etc/squid/peers.d/
cp -a "$SEED/surface/peers.d/." /var/lib/squid/surface/peers.d/
cp -a "$SEED/surface/tips/." /var/lib/squid/surface/tips/
cp -a "$ROOT/config/prefer.surface.toml" /var/lib/squid/ops/prefer.toml
cp -a "$SEED/tip_bind.accept" /var/lib/squid/ops/tip_bind.accept
cp -a "$SEED/state/clock.epoch" /var/lib/squid/state/clock.epoch
cp -a "$DATA/roster.list" /etc/squid/roster.list
printf '7\n' >/var/lib/squid/state/gen.target
printf '3\n' >/var/lib/squid/state/gen.live
rm -f /var/lib/squid/state/cutover.ok

# Durable hosts from fixtures
for f in "$DATA"/squid/*.toml; do
  name=$(basename "$f" .toml)
  host=$(grep -E '^host\s*=' "$f" | head -n1 | sed 's/.*=\s*"\(.*\)"/\1/')
  printf '%s\n' "$host" >"/var/lib/squid/peers/${name}.host"
done

# Durable floors
while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  k=$(echo "$k" | tr -d '[:space:]')
  v=$(echo "$v" | tr -d '[:space:]')
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/var/lib/squid/floors/${k}.floor"
done <"$SEED/floors.toml"

# Live floor sheets
while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  k=$(echo "$k" | tr -d '[:space:]')
  v=$(echo "$v" | tr -d '[:space:]')
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/etc/squid/floors/${k}.floor"
done <"$SEED/live_floors.toml"

# Tip generations before cutover
for n in north east south west core; do
  printf '1\n' >"/var/lib/squid/state/tip_${n}.gen"
done

# Packaging digest for immutable fixtures (operator inventory only)
(
  cd "$DATA/squid"
  sha256sum ./*.toml | sort
) >"$ROOT/packaging/peers.sha256"
