#!/bin/bash
set -euo pipefail

# Reconcile VM storage seating so the ops entrypoint emits a correct report.
# The reconcile engine (/app/bin/virtattach) is sealed and correct; the staging
# helpers under /app/ops staged the wrong live state after the crash. Restage
# them so durable identity, activation, receipts, and selection all agree.

OPS=/app/ops
STAGE=/app/stage
mkdir -p "$STAGE"

# ---------------------------------------------------------------------------
# Durable identity: join the roster with the cutover journal, keep the latest
# entry per in-scope pool up to the sealed generation cap, and write the plan.
# ---------------------------------------------------------------------------
cat > "$OPS/fold_g.sh" <<'EOF'
#!/bin/bash
set -euo pipefail
QEMU_DIR="${QEMU_DIR:-/etc/libvirt/qemu}"
OPS_DIR="${OPS_DIR:-/var/lib/libvirt/ops}"
ROSTER="${SEAT_ROSTER:-$QEMU_DIR/seat.roster}"
PLAN="${SEAT_PLAN:-$OPS_DIR/seating.plan}"
SEAL_FILE="${ATTACH_SEAL:-/etc/libvirt/storage/attach.seal}"
JOURNAL="${CUTOVER_JOURNAL:-$OPS_DIR/cutover.journal}"
mkdir -p "$OPS_DIR"

cap=0
while IFS= read -r line || [[ -n "$line" ]]; do
  line="$(printf '%s' "$line" | tr -d '[:space:]')"
  [[ -z "$line" || "$line" == \#* ]] && continue
  cap="$line"; break
done < "$SEAL_FILE"

declare -A want=()
declare -a order=()
while IFS='|' read -r domain target pool volume || [[ -n "$domain" ]]; do
  [[ -z "$pool" || "$domain" == \#* ]] && continue
  if [[ -z "${want[$pool]:-}" ]]; then order+=("$pool"); fi
  want[$pool]=1
done < "$ROSTER"

declare -A rank=()
declare -A ruuid=()
declare -A rpath=()
while IFS='|' read -r gen seq pool uuid path || [[ -n "$gen" ]]; do
  [[ -z "$gen" || "$gen" == \#* ]] && continue
  [[ -z "${want[$pool]:-}" ]] && continue
  (( gen > cap )) && continue
  r=$(( gen * 100000 + seq ))
  if [[ -z "${rank[$pool]:-}" ]] || (( r > rank[$pool] )); then
    rank[$pool]=$r
    ruuid[$pool]="$uuid"
    rpath[$pool]="$path"
  fi
done < "$JOURNAL"

: > "$PLAN"
for pool in "${order[@]}"; do
  [[ -z "${ruuid[$pool]:-}" ]] && continue
  printf '%s\t%s\t%s\n' "$pool" "${ruuid[$pool]}" "${rpath[$pool]}" >> "$PLAN"
done
EOF

# ---------------------------------------------------------------------------
# Selection: prefer the durable authority (surface definitions have drifted).
# ---------------------------------------------------------------------------
cat > "$OPS/pref_k.sh" <<'EOF'
#!/bin/bash
set -euo pipefail
ATTACH_D="${ATTACH_D:-/etc/libvirt/qemu/attach.d}"
mkdir -p "$ATTACH_D"
printf 'authority=durable\n' > "$ATTACH_D/10-select.conf"
EOF

# ---------------------------------------------------------------------------
# Activation: bring each planned pool up at its durable target path.
# ---------------------------------------------------------------------------
cat > "$STAGE/seat_r.sh" <<'EOF'
#!/bin/bash
set -euo pipefail
OPS_DIR="${OPS_DIR:-/var/lib/libvirt/ops}"
PLAN="${SEAT_PLAN:-$OPS_DIR/seating.plan}"
STATE_ROOT="${POOL_STATE_ROOT:-/var/lib/libvirt/storage}"
[[ -f "$PLAN" ]] || exit 0
while IFS=$'\t' read -r pool uuid path || [[ -n "$pool" ]]; do
  [[ -z "$pool" ]] && continue
  dir="$STATE_ROOT/$pool"
  mkdir -p "$dir"
  { printf 'state=active\n'; printf 'path=%s\n' "$path"; } > "$dir/pool.state"
done < "$PLAN"
EOF

# ---------------------------------------------------------------------------
# Receipts: authorize each roster disk as key=value under the durable identity.
# ---------------------------------------------------------------------------
cat > "$STAGE/mark_c.sh" <<'EOF'
#!/bin/bash
set -euo pipefail
QEMU_DIR="${QEMU_DIR:-/etc/libvirt/qemu}"
OPS_DIR="${OPS_DIR:-/var/lib/libvirt/ops}"
ROSTER="${SEAT_ROSTER:-$QEMU_DIR/seat.roster}"
PLAN="${SEAT_PLAN:-$OPS_DIR/seating.plan}"
RCPT_DIR="$OPS_DIR/receipts"
mkdir -p "$RCPT_DIR"

declare -A pu=()
if [[ -f "$PLAN" ]]; then
  while IFS=$'\t' read -r pool uuid path || [[ -n "$pool" ]]; do
    [[ -z "$pool" ]] && continue
    pu[$pool]="$uuid"
  done < "$PLAN"
fi

while IFS='|' read -r domain target pool volume || [[ -n "$domain" ]]; do
  [[ -z "$pool" || "$domain" == \#* ]] && continue
  uuid="${pu[$pool]:-}"
  out="$RCPT_DIR/${domain}-${target}.receipt"
  { printf 'pool=%s\n' "$pool"
    printf 'uuid=%s\n' "$uuid"
    printf 'volume=%s\n' "$volume"; } > "$out"
done < "$ROSTER"
EOF

# ---------------------------------------------------------------------------
# Lease janitor: clear torn markers left by the crash.
# ---------------------------------------------------------------------------
cat > "$OPS/tidy_v.sh" <<'EOF'
#!/bin/bash
set -euo pipefail
LEASE_DIR="${LEASE_DIR:-/var/run/libvirt}"
mkdir -p "$LEASE_DIR"
rm -f "$LEASE_DIR"/*.part "$LEASE_DIR"/*.lock
EOF

chmod +x "$OPS"/*.sh "$STAGE"/*.sh

# Run the ops entrypoint to emit the reconciled report.
bash /app/ops/run_pool_attach.sh
