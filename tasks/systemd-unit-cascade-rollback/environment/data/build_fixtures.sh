#!/usr/bin/env bash
set -euo pipefail

UNITS=/data/stack/units
OV=/data/stack/overrides
RUN=/data/stack/runtime
SEED=/data/fixtures/stack-seed
mkdir -p "$UNITS" "$OV" "$RUN" "$SEED/units"

write_unit() {
  local name="$1"
  shift
  printf '%s\n' "$@" > "$UNITS/$name"
  cp "$UNITS/$name" "$SEED/units/$name"
}

write_unit journal.service '[Unit]
Description=Journal backend'

write_unit store.service '[Unit]
Description=Store layer
After=journal.service
Requires=journal.service'

write_unit cache.service '[Unit]
Description=Cache layer
After=store.service
Wants=store.service'

write_unit ingress.service '[Unit]
Description=Ingress edge
After=cache.service
Requires=cache.service'

write_unit relay.service '[Unit]
Description=Relay sidecar
After=journal.service
BindsTo=store.service'

write_unit stack.target '[Unit]
Description=Stack target
Wants=ingress.service relay.service
After=ingress.service relay.service'

mkdir -p "$OV/relay.service.d"
cat > "$OV/relay.service.d/10-cutover.conf" <<'EOF'
BindsTo=store.service
EOF
cat > "$OV/relay.service.d/90-legacy.conf" <<'EOF'
BindsTo=store-v1.service
EOF

mkdir -p "$OV/store.service.d"
cat > "$OV/store.service.d/20-promote.conf" <<'EOF'
PartOf=stack.target
EOF

(
  cd "$SEED/units"
  sha256sum ./* | sed 's|  ./|  units/|' > ../checksums.sha256
)

rm -rf "$RUN"/*
