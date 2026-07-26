#!/bin/bash
# Materialize live /etc and /var from seed fixtures; pin instance digest.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/postfix/master.d /etc/postfix/floors /etc/postfix/maps \
  /var/lib/postfix/floors \
  /var/lib/postfix/ops/abort.d /var/lib/postfix/ops/maps \
  /var/lib/postfix/state \
  /var/lib/postfix/surface/tips /var/lib/postfix/surface/maps \
  /var/lib/postfix/surface/main.d \
  /var/run/postfix /var/log/postfix /output

cp -a "$SEED/main.cf" /etc/postfix/main.cf
cp -a "$SEED/master.d/." /etc/postfix/master.d/
cp -a "$SEED/abort.d/." /var/lib/postfix/ops/abort.d/
cp -a "$SEED/prefer.jsonl" /var/lib/postfix/ops/prefer.jsonl
cp -a "$SEED/instances.jsonl" /var/lib/postfix/ops/instances.jsonl
cp -a "$SEED/maps/nexthop.prefer" /var/lib/postfix/ops/maps/nexthop.prefer
cp -a "$SEED/maps/nexthop.prefer" /var/lib/postfix/ops/maps/nexthop.durable
cp -a "$SEED/maps/nexthop.live" /etc/postfix/maps/nexthop.live
cp -a "$SEED/surface/maps/." /var/lib/postfix/surface/maps/
cp -a "$SEED/surface/tips/." /var/lib/postfix/surface/tips/
cp -a "$SEED/surface/main.d/." /var/lib/postfix/surface/main.d/
cp -a "$ROOT/config/prefer.surface.toml" /var/lib/postfix/ops/prefer.toml
cp -a "$SEED/tip_bind.accept" /var/lib/postfix/ops/tip_bind.accept
cp -a "$SEED/state/clock.epoch" /var/lib/postfix/state/clock.epoch
cp -a "$DATA/roster.list" /etc/postfix/roster.list
printf '7\n' >/var/lib/postfix/state/gen.target
printf '3\n' >/var/lib/postfix/state/gen.live
rm -f /var/lib/postfix/state/cutover.ok

# Live instance trees from decoy seeds
while IFS= read -r name || [[ -n "${name:-}" ]]; do
  [[ -z "$name" ]] && continue
  mkdir -p "/etc/postfix-${name}"
  cp -a "$SEED/instances/${name}/main.cf" "/etc/postfix-${name}/main.cf"
done <"$DATA/roster.list"

# Durable floors
while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  k=$(echo "$k" | tr -d '[:space:]')
  v=$(echo "$v" | tr -d '[:space:]')
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/var/lib/postfix/floors/${k}.floor"
done <"$SEED/floors.toml"

# Live floor sheets
while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  k=$(echo "$k" | tr -d '[:space:]')
  v=$(echo "$v" | tr -d '[:space:]')
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/etc/postfix/floors/${k}.floor"
done <"$SEED/live_floors.toml"

# Tip generations before cutover
for n in mesa ridge beacon cinder quay; do
  printf '1\n' >"/var/lib/postfix/state/tip_${n}.gen"
  printf '/var/spool/postfix-%s-decoy\n' "$n" >"/var/lib/postfix/state/tip_${n}.queue"
done

# Packaging digest for immutable fixtures
(
  cd "$DATA/postfix"
  sha256sum ./*.toml | sort
) >"$ROOT/packaging/instances.sha256"
