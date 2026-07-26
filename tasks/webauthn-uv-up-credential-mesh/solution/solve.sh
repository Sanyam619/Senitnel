#!/usr/bin/env bash
set -euo pipefail

cd /app

# Align live local drop-in with site-standard tokens (abort package stays forensic).
cat >/etc/ceremony/reconcile.d/90-local.conf <<'EOF'
# Local operator override — aligned with site standard after cutover.
authority=strict-tier
ceremony_plane=durable
seat_mode=profile
EOF
cp -f /etc/ceremony/reconcile.d/90-local.conf /app/config/reconcile.d/90-local.conf

# Durable sealed cutover receipt matching gen.target.
target_gen=$(cat /var/lib/ceremony/state/gen.target)
cat >/var/lib/ceremony/state/cutover.ok <<EOF
gen=${target_gen}
mode=seal
EOF

cat >/app/ops/seat_uv.sh <<'EOF'
#!/bin/bash
# seat_uv.sh — seat UV/UP policy into live ceremony state.
set -euo pipefail

mkdir -p /var/lib/ceremony/state
cat >/var/lib/ceremony/state/uv_policy.conf <<'POLICY'
fleet_a_uv=1
fleet_a_up=1
fleet_b_uv=0
fleet_b_up=1
POLICY
EOF

cat >/app/ops/axle_hold.sh <<'EOF'
#!/bin/bash
# axle_hold.sh — seat ledger hold bound into live ceremony state.
set -euo pipefail

mkdir -p /var/lib/ceremony/state
printf 'exclusive\n' >/var/lib/ceremony/state/hold_bound
EOF

cat >/app/ops/knit_stream.sh <<'EOF'
#!/bin/bash
# knit_stream.sh — seat credential/WAL stream order into live ceremony state.
set -euo pipefail

mkdir -p /var/lib/ceremony/state
printf 'interleave-asc\n' >/var/lib/ceremony/state/stream.order
EOF

cat >/app/ops/fold_d.sh <<'EOF'
#!/bin/bash
# fold_d.sh — abort rematerialize + lexical fold of ceremony drop-ins.
set -euo pipefail

mkdir -p /etc/ceremony/reconcile.d /var/lib/ceremony/ops/abort.d /var/lib/ceremony/state
abort_pkg="/var/lib/ceremony/ops/abort.d/90-local.conf"
live_dropin="/etc/ceremony/reconcile.d/90-local.conf"
cutover_receipt="/var/lib/ceremony/state/cutover.ok"
target_gen=$(cat /var/lib/ceremony/state/gen.target)

need_abort=1
if [[ -f "$cutover_receipt" ]]; then
  gen_ok=$(grep -E '^gen=' "$cutover_receipt" | head -n1 | cut -d= -f2- || true)
  mode_ok=$(grep -E '^mode=' "$cutover_receipt" | head -n1 | cut -d= -f2- || true)
  if [[ "$gen_ok" == "$target_gen" && "$mode_ok" == "seal" ]]; then
    need_abort=0
  fi
fi

if [[ "$need_abort" -eq 1 ]]; then
  if [[ -f "$abort_pkg" ]]; then
    cp -f "$abort_pkg" "$live_dropin"
  fi
  rm -f "$cutover_receipt"
fi

# Lexical fold of drop-ins into effective reconcile.conf
: >/etc/ceremony/reconcile.conf
shopt -s nullglob
for f in /etc/ceremony/reconcile.d/*.conf; do
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" ]] && continue
    [[ "$line" != *=* ]] && continue
    key="${line%%=*}"
    val="${line#*=}"
    if grep -q "^${key}=" /etc/ceremony/reconcile.conf 2>/dev/null; then
      grep -v "^${key}=" /etc/ceremony/reconcile.conf >/tmp/ceremony.fold || true
      mv /tmp/ceremony.fold /etc/ceremony/reconcile.conf
    fi
    echo "${key}=${val}" >>/etc/ceremony/reconcile.conf
  done <"$f"
done
shopt -u nullglob
EOF

bash /app/ops/run_mesh.sh /output/ceremony-ledger.json
