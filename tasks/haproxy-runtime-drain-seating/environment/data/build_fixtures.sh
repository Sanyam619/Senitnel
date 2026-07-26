#!/bin/bash
# Materialize live /etc and /var from seed fixtures; pin backends digest.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/haproxy/conf.d /etc/haproxy/floors \
  /var/lib/haproxy/backends /var/lib/haproxy/floors /var/lib/haproxy/leases \
  /var/lib/haproxy/ops/abort.d /var/lib/haproxy/state /var/run/haproxy \
  /var/log/haproxy /output /etc/haproxy/tips

cp -a "$SEED/haproxy.cfg" /etc/haproxy/haproxy.cfg
cp -a "$SEED/conf.d/." /etc/haproxy/conf.d/
cp -a "$SEED/abort.d/." /var/lib/haproxy/ops/abort.d/
cp -a "$SEED/journal.jsonl" /var/lib/haproxy/ops/journal.jsonl
cp -a "$SEED/clock.epoch" /var/lib/haproxy/state/clock.epoch
cp -a "$DATA/roster.list" /etc/haproxy/roster.list
printf '7\n' >/var/lib/haproxy/state/gen.target
printf '3\n' >/var/lib/haproxy/state/gen.live
rm -f /var/lib/haproxy/state/cutover.ok

# Durable backend addresses from fixtures
for f in "$DATA"/backends/*.toml; do
  name=$(basename "$f" .toml)
  server=$(grep -E '^server\s*=' "$f" | head -n1 | sed 's/.*=\s*"\(.*\)"/\1/')
  printf '%s\n' "$server" >"/var/lib/haproxy/backends/${name}.addr"
  # live tip decoy addresses
  printf '127.0.0.1:9\n' >"/etc/haproxy/tips/${name}.addr"
done

# Durable floors
while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  k=$(echo "$k" | tr -d '[:space:]')
  v=$(echo "$v" | tr -d '[:space:]')
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/var/lib/haproxy/floors/${k}.floor"
done <"$SEED/floors.toml"

# Live decoy floors
while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  k=$(echo "$k" | tr -d '[:space:]')
  v=$(echo "$v" | tr -d '[:space:]')
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/etc/haproxy/floors/${k}.floor"
done <"$SEED/live_floors.toml"

# Leases
while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  k=$(echo "$k" | tr -d '[:space:]')
  v=$(echo "$v" | tr -d '[:space:]')
  [[ -z "$k" ]] && continue
  printf 'until_epoch=%s\n' "$v" >"/var/lib/haproxy/leases/${k}.lease"
done <"$SEED/leases.toml"

# Stale tip generations (pre-cutover)
for n in alpha beta gamma delta epsilon; do
  printf '1\n' >"/var/lib/haproxy/state/tip_${n}.gen"
done

# Stale runtime map
{
  echo "alpha 1 0"
  echo "beta 1 0"
  echo "gamma 1 0"
  echo "delta 999 0"
  echo "epsilon 1 0"
} >/var/run/haproxy/runtime.map

# Packaging digest for immutable fixtures
(
  cd "$DATA/backends"
  sha256sum ./*.toml | sort
) >"$ROOT/packaging/backends.sha256"
