#!/bin/bash
set -euo pipefail

LAB=/data/lab
SEED=/data/fixtures/broker-seed
APP=/app

rm -rf "$LAB" "$SEED"
mkdir -p "$LAB"/{caps,units/live.d,identity,race,mnt/host/dev,mnt/host/stale,mnt/broker/dev,ops} \
         "$SEED"/caps "$SEED"/mnt/host/dev "$SEED"/units /output /opt/broker/units /opt/broker/config

cp "$APP/units/broker.service" "$LAB/units/live.service"
cp "$APP/units/broker.service" "$SEED/units/live.service"
cp "$APP/units/10-private.conf" "$LAB/units/live.d/10-private.conf"
cp "$APP/units/broker-devices.conf" /opt/broker/units/
cp "$APP/config/lab.toml" /opt/broker/config/
cp "$APP/config/fleet-caps.conf" /opt/broker/config/
cp "$APP/config/harbor-caps.conf" /opt/broker/config/
cp "$APP/config/field-notes.md" /opt/broker/config/

echo -n 'cap_net_admin,cap_sys_admin,cap_sys_rawio' > "$LAB/caps/bounding"
echo -n '' > "$LAB/caps/ambient"
echo -n 'cap_sys_admin' > "$LAB/caps/effective"

echo -n 'host' > "$LAB/identity/mnt_ns"
echo -n 'dirty' > "$LAB/race/last_pulse"

echo -n "node:dev-alpha" > "$LAB/mnt/host/dev/dev-alpha"
echo -n "node:dev-beta" > "$LAB/mnt/host/dev/dev-beta"
echo -n "node:dev-gamma" > "$LAB/mnt/broker/dev/dev-gamma"

echo -n "stale" > "$LAB/mnt/host/stale/dev-alpha"
echo -n "stale" > "$LAB/mnt/host/stale/dev-beta"
echo -n "stale" > "$LAB/mnt/host/stale/dev-gamma"

cat > "$LAB/ops/cutover.log" <<'OLOG'
[2024-03-01T14:23:01Z] CUTOVER-START profile=fleet mode=legacy
[2024-03-01T14:23:02Z] STEP-1 lane-apply: mode=legacy status=OK
[2024-03-01T14:23:03Z] STEP-2 node-seat: dev-gamma=OK dev-alpha=TIMEOUT dev-beta=PENDING
[2024-03-01T14:23:04Z] STEP-3 race-pulse: status=DIRTY reason=stale_markers_present
[2024-03-01T14:23:05Z] UNIT-MERGE note=live.d/10-private.conf still active
[2024-03-01T14:23:06Z] CUTOVER-ABORT reason=step3-dirty lockout=none
OLOG

for n in dev-alpha dev-beta dev-gamma; do
  echo -n "node:$n" > "$SEED/mnt/host/dev/$n"
done
echo -n 'cap_net_admin,cap_sys_admin' > "$SEED/caps/bounding"
echo -n '' > "$SEED/caps/ambient"

TMP_MANIFEST=$(mktemp)
(
  cd "$SEED"
  find . -type f | sort | while read -r f; do
    sha256sum "$f"
  done
) > "$TMP_MANIFEST"
mv "$TMP_MANIFEST" "$SEED/checksums.sha256"
