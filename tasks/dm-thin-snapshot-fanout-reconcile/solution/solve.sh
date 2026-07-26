#!/bin/bash
set -euo pipefail

cat > /app/ops/fold_k.sh <<'EOF'
#!/bin/bash
set -euo pipefail
ROOT="${POOL_ROOT:-/var/lib/pool}"
SEAL="${POOL_SEAL:-/etc/pool/pool.seal}"
ROSTER="${DRILL_ROSTER:-/etc/pool/drill.roster}"
WAL="$ROOT/journal/act.wal"
RUNTIME="$ROOT/meta/runtime.tsv"
ACT="$ROOT/meta/activation.toml"
mkdir -p "$ROOT/meta"

cap=0
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  cap="$line"
  break
done <"$SEAL"

declare -A allow=()
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  allow["$line"]=1
done <"$ROSTER"

declare -A latest_line=()
declare -a order_keys=()
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  IFS='|' read -r gen seq drill tip origin kind epoch floor <<<"$line"
  [[ "$gen" -gt "$cap" ]] && continue
  [[ -z "${allow[$drill]+x}" ]] && continue
  if [[ -z "${latest_line[$drill]+x}" ]]; then
    order_keys+=("$drill")
  fi
  latest_line[$drill]="$drill|$tip|$origin|$kind|$epoch|$floor"
done <"$WAL"

: >"$RUNTIME"
: >"$ACT"
printf '%s\n' "# activation tips" "[tips]" >>"$ACT"
order=0
for drill in "${order_keys[@]}"; do
  order=$((order + 1))
  IFS='|' read -r d tip origin kind epoch floor <<<"${latest_line[$drill]}"
  printf '%d\t%s\t%s\t%s\t%s\t%s\t%s\n' "$order" "$d" "$tip" "$origin" "$kind" "$epoch" "$floor" >>"$RUNTIME"
  printf '%s = "%s"\n' "$d" "$tip" >>"$ACT"
done
EOF
chmod +x /app/ops/fold_k.sh

cat > /app/ops/pref_a.sh <<'EOF'
#!/bin/bash
set -euo pipefail
ROOT="${POOL_ROOT:-/var/lib/pool}"
RUNTIME="$ROOT/meta/runtime.tsv"
PREF_D="${POOL_PREF_D:-/etc/pool/pref.d}"
[[ -f "$RUNTIME" ]] || exit 0
mode="equality-inclusive"
if [[ -d "$PREF_D" ]]; then
  while IFS= read -r f; do
    [[ -f "$f" ]] || continue
    if grep -q 'mode=equality-inclusive' "$f" 2>/dev/null; then
      mode="equality-inclusive"
    fi
    if grep -q 'mode=strict-gt' "$f" 2>/dev/null; then
      mode="strict-gt"
    fi
  done < <(find "$PREF_D" -type f | sort)
fi
if [[ "$mode" != "equality-inclusive" ]]; then
  echo "pref_a: mode=$mode" >&2
  exit 1
fi
: >"$ROOT/meta/pref.armed"
EOF
chmod +x /app/ops/pref_a.sh

cat > /etc/pool/pref.d/10-floor.conf <<'EOF'
mode=equality-inclusive
EOF

cat > /app/ops/skim_x.sh <<'EOF'
#!/bin/bash
set -euo pipefail
ROOT="${POOL_ROOT:-/var/lib/pool}"
STAGE="${ORIGIN_ROOT:-/var/lib/pool/origin_stage}"
mkdir -p "$STAGE"
for src in "$ROOT"/origins/*.bin; do
  [[ -e "$src" ]] || continue
  cp -f "$src" "$STAGE/$(basename "$src")"
done
EOF
chmod +x /app/ops/skim_x.sh

cat > /app/ops/hold_m.sh <<'EOF'
#!/bin/bash
set -euo pipefail
ROOT="${POOL_ROOT:-/var/lib/pool}"
LEASE="${LEASE_DIR:-/var/run/pool}"
mkdir -p "$LEASE"
rm -f "$ROOT"/origins/*.lease "$LEASE"/*.part
EOF
chmod +x /app/ops/hold_m.sh

cat > /app/ops/emit_h.sh <<'EOF'
#!/bin/bash
set -euo pipefail
ROOT="${POOL_ROOT:-/var/lib/pool}"
SEAL="${POOL_SEAL:-/etc/pool/pool.seal}"
mkdir -p "$ROOT/meta"
cap=0
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  cap="$line"
  break
done <"$SEAL"
echo "$cap" >"$ROOT/meta/seal_gen.arm"
EOF
chmod +x /app/ops/emit_h.sh

/app/ops/run_materialize.sh
