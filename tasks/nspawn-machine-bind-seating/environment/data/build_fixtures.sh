#!/bin/bash
# Materialize live /etc and /var from seed fixtures; pin machine digests.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/systemd/nspawn/floors \
  /etc/systemd/system/machines.target.wants \
  /var/lib/machines/images \
  /var/lib/machines/live \
  /var/lib/machines/volumes \
  /var/lib/machines/bind \
  /var/lib/machines/floors \
  /var/lib/machines/ops/abort.d \
  /var/lib/machines/state \
  /var/run/machines \
  /var/log/machines \
  /output

cp -a "$DATA/roster.list" /etc/systemd/nspawn/roster.list
cp -a "$SEED/nspawn.d/." /etc/systemd/nspawn/
cp -a "$SEED/machines.target.wants/." /etc/systemd/system/machines.target.wants/
cp -a "$SEED/abort.d/." /var/lib/machines/ops/abort.d/
cp -a "$SEED/journal.jsonl" /var/lib/machines/ops/journal.jsonl
cp -a "$SEED/ports.toml" /var/lib/machines/ops/ports.toml
cp -a "$SEED/live_ports.toml" /etc/systemd/nspawn/ports.toml
cp -a "$SEED/clock.epoch" /var/lib/machines/state/clock.epoch
printf '7\n' >/var/lib/machines/state/gen.target
printf '3\n' >/var/lib/machines/state/gen.live
rm -f /var/lib/machines/state/cutover.ok

# Durable floors
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/var/lib/machines/floors/${k}.floor"
done <"$SEED/floors.toml"

# Live decoy floors
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/etc/systemd/nspawn/floors/${k}.floor"
done <"$SEED/live_floors.toml"

# Image tips, shadows, volumes, and bind paths
for n in alpha beta gamma delta epsilon; do
  mkdir -p "/var/lib/machines/images/${n}" "/var/lib/machines/live/${n}" \
    "/var/lib/machines/volumes/${n}" "/var/lib/machines/bind/${n}"
  # Durable tip content
  cp -a "$DATA/machines/${n}.img" "/var/lib/machines/images/${n}/root"
  # Live shadow decoy (different content marker)
  printf 'live-shadow-%s\n' "$n" >"/var/lib/machines/live/${n}/root"
  # Sealed volume object
  printf 'sealed-vol-%s\n' "$n" >"/var/lib/machines/volumes/${n}/data"
  # Initial bind path materialization
  cp -f "/var/lib/machines/volumes/${n}/data" "/var/lib/machines/bind/${n}/data"
  # Initial tip stamps
  printf '1\n' >"/var/lib/machines/state/tip_${n}.gen"
done

# Packaging digest for immutable fixtures
(
  cd "$DATA/machines"
  sha256sum *.img | sort -k2
) >"$ROOT/packaging/machines.sha256"

cp -a "$ROOT/packaging/machines.sha256" /app/packaging/machines.sha256 2>/dev/null || true
