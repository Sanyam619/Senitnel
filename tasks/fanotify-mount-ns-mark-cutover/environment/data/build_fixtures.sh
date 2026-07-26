#!/bin/bash
set -euo pipefail

LAB=/data/lab
SEED=/data/fixtures/watch-seed
APP=/app

rm -rf "$LAB" "$SEED"
mkdir -p "$LAB"/{units/live.service.d,identity,inherit,race/jitter,journal,trees/host,trees/broker,marks/host,marks/broker} \
         "$SEED"/{trees/host,marks/host,units} /output /opt/fev/units /opt/fev/config/gens

cp "$APP/units/broker.service" "$LAB/units/live.service"
cp "$APP/units/broker.service" "$SEED/units/live.service"
cp "$APP/units/broker-watches.conf" /opt/fev/units/
cp "$APP/config/lab.toml" /opt/fev/config/
cp "$APP/config/field-notes.md" /opt/fev/config/
cp "$APP/config/path-tiers.conf" /opt/fev/config/
cp "$APP/config/roster.conf" /opt/fev/config/
cp "$APP/config/cutover.toml" /opt/fev/config/
cp "$APP/config/holds.conf" /opt/fev/config/
cp -a "$APP/config/gens/." /opt/fev/config/gens/

printf '%s\n' '[Service]' 'PrivateMounts=yes' > "$LAB/units/live.service.d/10-private.conf"

# Stuck on prior generation after abort
echo -n 'g2' > "$LAB/identity/policy_gen"
echo -n 'broker' > "$LAB/identity/mnt_ns"

cat > "$LAB/journal/cutover.abort" <<'EOF'
cutover wave aborted mid-flight
target_generation=g3
identity left on prior generation
reopen rows must follow the target generation roster order
EOF

echo -n '' > "$LAB/inherit/table"
echo -n '0' > "$LAB/inherit/ok"
echo -n 'dirty' > "$LAB/race/last_pulse"

echo -n "watch:path-alpha" > "$LAB/trees/broker/path-alpha"
echo -n "filesystem" > "$LAB/marks/broker/path-alpha"

echo -n "watch:path-beta" > "$LAB/trees/broker/path-beta"
echo -n "inode" > "$LAB/marks/broker/path-beta"

echo -n "watch:path-gamma" > "$LAB/trees/host/path-gamma"
echo -n "watch:path-gamma" > "$LAB/trees/broker/path-gamma"
echo -n "filesystem" > "$LAB/marks/broker/path-gamma"

echo -n "watch:path-delta" > "$LAB/trees/host/path-delta"
echo -n "inode" > "$LAB/marks/host/path-delta"

echo -n "watch:path-epsilon" > "$LAB/trees/broker/path-epsilon"
echo -n "filesystem" > "$LAB/marks/broker/path-epsilon"

echo -n "watch:path-zeta" > "$LAB/trees/host/path-zeta"
echo -n "inode" > "$LAB/marks/host/path-zeta"

for n in path-alpha path-beta path-gamma path-delta path-epsilon path-zeta; do
  echo -n "jitter" > "$LAB/race/jitter/$n"
done

for n in path-alpha path-beta path-gamma path-delta path-epsilon path-zeta; do
  echo -n "watch:$n" > "$SEED/trees/host/$n"
  echo -n "inode" > "$SEED/marks/host/$n"
done
cp "$APP/units/broker.service" "$SEED/units/live.service"
