#!/bin/bash
set -euo pipefail

# Repair cutover helpers, then run the ops entrypoint.
# Prebuilt /app/bin tools stay authoritative; do not replace them.

cat > /app/ops/fold_u.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
fold_u() {
  rewrite() {
    local f="$1"
    [[ -f "$f" ]] || return 0
    if grep -q 'PrivateMounts=yes' "$f" 2>/dev/null; then
      sed -i 's/PrivateMounts=yes/PrivateMounts=no/g' "$f"
    fi
    if ! grep -q 'PrivateMounts=no' "$f" 2>/dev/null; then
      printf '\nPrivateMounts=no\n' >>"$f"
    fi
  }
  rewrite /etc/ingest/units/live.service
  shopt -s nullglob
  for f in /etc/ingest/units/live.d/*.conf; do
    rewrite "$f"
  done
}
fold_u
EOF
chmod +x /app/ops/fold_u.sh

cat > /app/ops/lease_w.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
lease_w() {
  cap=0
  while read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    cap="$line"
    break
  done </etc/ingest/fleet.seal

  best_gen=-1
  best_seq=-1
  epoch=""
  prefix=""
  mode=""
  while read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    gen=${line%%|*}
    rest=${line#*|}
    seq=${rest%%|*}
    rest=${rest#*|}
    ep=${rest%%|*}
    rest=${rest#*|}
    pref=${rest%%|*}
    md=${rest#*|}
    [[ "$gen" -gt "$cap" ]] && continue
    if [[ "$gen" -gt "$best_gen" || ( "$gen" -eq "$best_gen" && "$seq" -gt "$best_seq" ) ]]; then
      best_gen="$gen"
      best_seq="$seq"
      epoch="$ep"
      prefix="$pref"
      mode="$md"
    fi
  done </var/lib/ingest/journal/act.wal

  [[ -n "$epoch" && -n "$prefix" && "$mode" == "seal" ]] || {
    echo "lease_w: no sealed tip under cap" >&2
    exit 1
  }
  mkdir -p /var/lib/ingest/leases /var/lib/ingest/journal
  echo -n "$epoch" > /var/lib/ingest/leases/durable
  echo -n "$epoch" > /var/lib/ingest/leases/live
  echo -n "$prefix" > /var/lib/ingest/journal/prefix
  echo -n "seal:${epoch}:${prefix}" > /var/lib/ingest/journal/seal
  echo -n "seal" > /var/lib/ingest/journal/cutover.mode
}
lease_w
EOF
chmod +x /app/ops/lease_w.sh

cat > /app/mesh/skim_v.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
skim_v() {
  :
}
skim_v
EOF
chmod +x /app/mesh/skim_v.sh

cat > /app/mesh/pref_q.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
pref_q() {
  mode=rollback
  shopt -s nullglob
  for f in $(ls /etc/ingest/pref.d/*.conf 2>/dev/null | sort); do
    if grep -q 'cutover=seal' "$f" 2>/dev/null; then
      mode=seal
    elif grep -q 'cutover=rollback' "$f" 2>/dev/null; then
      mode=rollback
    fi
  done
  mkdir -p /var/lib/ingest/meta
  echo -n "$mode" > /var/lib/ingest/meta/pref.armed
  [[ "$mode" == "seal" ]] || { echo "pref_q: not seal-bound" >&2; exit 1; }
}
pref_q
EOF
chmod +x /app/mesh/pref_q.sh

cat > /app/seat/seat_m.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
seat_m() {
  mkdir -p /var/lib/ingest/mnt/broker/ten /var/lib/ingest/mnt/host/ten /var/lib/ingest/identity
  while read -r name || [[ -n "$name" ]]; do
    [[ -z "$name" || "$name" == \#* ]] && continue
    src="/var/lib/ingest/mnt/host/ten/$name"
    dst="/var/lib/ingest/mnt/broker/ten/$name"
    if [[ -f "$src" ]]; then
      cp -f "$src" "$dst"
      rm -f "$src"
    elif [[ ! -f "$dst" ]]; then
      echo -n "marker:$name" >"$dst"
    fi
  done </etc/ingest/tenant.roster
  echo -n "broker" > /var/lib/ingest/identity/mnt_ns
}
seat_m
EOF
chmod +x /app/seat/seat_m.sh

cat > /app/arm/arm_h.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
arm_h() {
  epoch=$(cat /var/lib/ingest/leases/durable)
  prefix=$(cat /var/lib/ingest/journal/prefix)
  mkdir -p /var/lib/ingest/meta
  echo -n "$epoch" > /var/lib/ingest/meta/seal_gen.arm
  echo -n "seal:${epoch}:${prefix}" > /var/lib/ingest/meta/cutover.ok
}
arm_h
EOF
chmod +x /app/arm/arm_h.sh

cat > /app/rim/hold_r.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
hold_r() {
  mkdir -p /etc/ingest/units/abort.d
  seal=$(cat /var/lib/ingest/journal/seal 2>/dev/null || true)
  ok=$(cat /var/lib/ingest/meta/cutover.ok 2>/dev/null || true)
  if [[ -n "$seal" && "$ok" == "$seal" ]]; then
    cat > /etc/ingest/units/abort.d/90-isolate.conf <<'INNER'
[Service]
PrivateMounts=no
INNER
  else
    cat > /etc/ingest/units/abort.d/90-isolate.conf <<'INNER'
[Service]
PrivateMounts=yes
INNER
    exit 1
  fi
}
hold_r
EOF
chmod +x /app/rim/hold_r.sh

rm -f /output/lease-cutover.json
/app/ops/run_cutover.sh

epoch=$(cat /var/lib/ingest/leases/durable)
prefix=$(cat /var/lib/ingest/journal/prefix)
test "$(cat /var/lib/ingest/journal/seal)" = "seal:$epoch:$prefix"
test "$(cat /var/lib/ingest/meta/cutover.ok)" = "seal:$epoch:$prefix"
test "$(cat /var/lib/ingest/meta/pref.armed)" = "seal"
test "$(cat /var/lib/ingest/preflight/last_run)" = "stable"
test -f /output/lease-cutover.json
echo "cutover complete"
