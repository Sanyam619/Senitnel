#!/bin/bash
# Materialize live /etc and /var from seed fixtures; pin client digest.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/openvpn/server/conf.d /etc/openvpn/server/floors /etc/openvpn/ccd \
  /var/lib/openvpn/floors \
  /var/lib/openvpn/ops/abort.d /var/lib/openvpn/state \
  /var/lib/openvpn/surface/ccd /var/lib/openvpn/surface/tips \
  /var/run/openvpn /var/log/openvpn /output

cp -a "$SEED/server.conf" /etc/openvpn/server/server.conf
cp -a "$SEED/conf.d/." /etc/openvpn/server/conf.d/
cp -a "$SEED/abort.d/." /var/lib/openvpn/ops/abort.d/
cp -a "$SEED/prefer.jsonl" /var/lib/openvpn/ops/prefer.jsonl
cp -a "$SEED/clients.jsonl" /var/lib/openvpn/ops/clients.jsonl
cp -a "$SEED/pools.toml" /var/lib/openvpn/ops/pools.toml
cp -a "$SEED/ccd/." /etc/openvpn/ccd/
cp -a "$SEED/surface/ccd/." /var/lib/openvpn/surface/ccd/
cp -a "$SEED/surface/tips/." /var/lib/openvpn/surface/tips/
cp -a "$ROOT/config/prefer.surface.toml" /var/lib/openvpn/ops/prefer.toml
cp -a "$SEED/tip_bind.accept" /var/lib/openvpn/ops/tip_bind.accept
cp -a "$SEED/state/clock.epoch" /var/lib/openvpn/state/clock.epoch
cp -a "$DATA/roster.list" /etc/openvpn/server/roster.list
printf '8\n' >/var/lib/openvpn/state/gen.target
printf '3\n' >/var/lib/openvpn/state/gen.live
rm -f /var/lib/openvpn/state/cutover.ok

# Durable floors
while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  k=$(echo "$k" | tr -d '[:space:]')
  v=$(echo "$v" | tr -d '[:space:]')
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/var/lib/openvpn/floors/${k}.floor"
done <"$SEED/floors.toml"

# Live floor sheets (bait)
while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  k=$(echo "$k" | tr -d '[:space:]')
  v=$(echo "$v" | tr -d '[:space:]')
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/etc/openvpn/server/floors/${k}.floor"
done <"$SEED/live_floors.toml"

for n in flint quartz jasper onyx beryl mica; do
  printf '1\n' >"/var/lib/openvpn/state/tip_${n}.gen"
done

(
  cd "$DATA/ovpn"
  sha256sum ./*.toml | sort
) >"$ROOT/packaging/clients.sha256"
