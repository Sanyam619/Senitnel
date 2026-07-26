#!/bin/bash
set -euo pipefail

sheet_z=/app/config/site_policy.conf
live_drop=/etc/keepalived/conf.d/90-local.conf
target_gen=$(tr -d '[:space:]' </var/lib/keepalived/ops/state/generation.target)
cp -f "$sheet_z" "$live_drop"
{
  echo "gen=${target_gen}"
  echo "mode=seal"
} >/var/lib/keepalived/ops/state/cutover.ok

cat >/app/ops/window_c.sh <<'EOF'
#!/bin/bash
set -euo pipefail
abort_d="${ABORT_D:-/var/lib/keepalived/ops/abort.d}"
live_d="${LIVE_D:-/etc/keepalived/conf.d}"
ops_state="${OPS_STATE:-/var/lib/keepalived/ops/state}"
receipt_f="$ops_state/cutover.ok"
target_gen=$(tr -d '[:space:]' <"$ops_state/generation.target")
mkdir -p "$live_d" "$ops_state"
skip=0
if [[ -f "$receipt_f" ]]; then
  got_gen="" got_mode=""
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" ]] && continue
    case "$line" in
      gen=*) got_gen="${line#gen=}" ;;
      mode=*) got_mode="${line#mode=}" ;;
    esac
  done <"$receipt_f"
  if [[ "$got_gen" == "$target_gen" && "$got_mode" == "seal" ]]; then
    skip=1
  fi
fi
if [[ "$skip" -eq 0 ]]; then
  if [[ -f "$abort_d/90-local.conf" ]]; then
    cp -f "$abort_d/90-local.conf" "$live_d/90-local.conf"
  fi
fi
EOF
chmod +x /app/ops/window_c.sh

cat >/app/ops/fold_w.sh <<'EOF'
#!/bin/bash
set -euo pipefail
conf_d="${PREF_D:-/etc/keepalived/conf.d}"
out_f="${EFF_PRIO:-/var/lib/keepalived/ops/live/prio.tsv}"
mkdir -p "$(dirname "$out_f")"
declare -A z=()
shopt -s nullglob
for f in $(ls -1 "$conf_d"/*.conf 2>/dev/null | sort); do
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" ]] && continue
    op="set"
    if [[ "$line" == replace\ * ]]; then
      line="${line#replace }"
      op="set"
    elif [[ "$line" == delta\ * ]]; then
      line="${line#delta }"
      op="delta"
    fi
    [[ "$line" != *=* ]] && continue
    raw="${line%%=*}"; v="${line#*=}"
    if [[ "$raw" == *.prio ]]; then
      k="${raw%.prio}"
    else
      k="$raw"
    fi
    # skip non-priority keys (bind_order, tip_policy, …)
    [[ "$raw" == *.prio || "$op" == "delta" ]] || continue
    if [[ "$op" == "delta" ]]; then
      cur="${z[$k]:-0}"
      z["$k"]=$((cur + v))
    else
      z["$k"]="$v"
    fi
  done <"$f"
done
shopt -u nullglob
{
  for n in $(printf '%s\n' "${!z[@]}" | sort); do
    printf '%s\t%s\n' "$n" "${z[$n]}"
  done
} >"$out_f"
EOF
chmod +x /app/ops/fold_w.sh

cat >/app/ops/tip_q.sh <<'EOF'
#!/bin/bash
set -euo pipefail
journal_f="${PREFER_J:-/var/lib/keepalived/ops/prefer.jsonl}"
peer_d="${PEER_D:-/app/data/vrrp}"
extra_d="${EXTRA_D:-/var/lib/keepalived/ops/extra}"
out_f="${CAND_TSV:-/var/lib/keepalived/ops/live/cand.tsv}"
gen_live="${GEN_LIVE:-/var/lib/keepalived/ops/state/generation.live}"
mkdir -p "$(dirname "$out_f")" "$(dirname "$gen_live")"
: >"$out_f"

declare -A peer_vrid=() peer_vip=()
shopt -s nullglob
for root in "$peer_d" "$extra_d"; do
  [[ -d "$root" ]] || continue
  for f in "$root"/*.conf; do
    id=""; vrid=""; vip=""
    while IFS= read -r line || [[ -n "${line:-}" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ -z "$line" || "$line" != *=* ]] && continue
      k="${line%%=*}"; v="${line#*=}"
      case "$k" in
        id) id="$v" ;;
        vrid) vrid="$v" ;;
        vip) vip="$v" ;;
      esac
    done <"$f"
    [[ -n "$id" ]] || continue
    peer_vrid["$id"]="$vrid"
    peer_vip["$id"]="$vip"
  done
done
shopt -u nullglob

if [[ ! -f "$journal_f" ]]; then
  printf '0\n' >"$gen_live"
  exit 0
fi

picked="$(jq -c -s '
  map(select(.kind=="batch" and .sealed==true and .complete==true))
  | sort_by(.gen)
  | .[-1] // empty
' "$journal_f")"
if [[ -z "$picked" || "$picked" == "null" ]]; then
  printf '0\n' >"$gen_live"
  exit 0
fi
gen="$(jq -r '.gen // 0' <<<"$picked")"
printf '%s\n' "$gen" >"$gen_live"

while IFS=$'\t' read -r pid tip rank || [[ -n "${pid:-}" ]]; do
  [[ -z "${pid:-}" ]] && continue
  printf '%s\t%s\t%s\t%s\t%s\n' \
    "$pid" "$tip" "$rank" "${peer_vrid[$pid]:-0}" "${peer_vip[$pid]:-}" >>"$out_f"
done < <(jq -r '.rows[]? | [.id, (.tip|tonumber), (.rank|tonumber)] | @tsv' <<<"$picked")
EOF
chmod +x /app/ops/tip_q.sh

cat >/app/ops/track_m.sh <<'EOF'
#!/bin/bash
set -euo pipefail
prio_in="${EFF_PRIO:-/var/lib/keepalived/ops/live/prio.tsv}"
track_dir="${track_dir:-/var/lib/keepalived/ops/track}"
out_f="${EFF_PRIO:-/var/lib/keepalived/ops/live/prio.tsv}"
mkdir -p "$(dirname "$out_f")"
declare -A z=()
if [[ -f "$prio_in" ]]; then
  while IFS=$'\t' read -r name v || [[ -n "${name:-}" ]]; do
    [[ -z "${name:-}" ]] && continue
    z["$name"]="$v"
  done <"$prio_in"
fi
shopt -s nullglob
for f in "$track_dir"/*.wt; do
  [[ -f "$f" ]] || continue
  base="$(basename "$f" .wt)"
  status_f="$track_dir/${base}.status"
  status="DOWN"
  [[ -f "$status_f" ]] && status="$(tr -d '[:space:]' <"$status_f")"
  [[ "$status" == "UP" ]] || continue
  delta=0
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" || "$line" != *=* ]] && continue
    k="${line%%=*}"; v="${line#*=}"
    if [[ "$k" == "delta" ]]; then
      delta="$v"
    fi
  done <"$f"
  cur="${z[$base]:-0}"
  z["$base"]=$((cur + delta))
done
shopt -u nullglob
{
  for n in $(printf '%s\n' "${!z[@]}" | sort); do
    printf '%s\t%s\n' "$n" "${z[$n]}"
  done
} >"$out_f"
EOF
chmod +x /app/ops/track_m.sh

cat >/app/ops/hold_m.sh <<'EOF'
#!/bin/bash
set -euo pipefail
cand_f="${CAND_TSV:-/var/lib/keepalived/ops/live/cand.tsv}"
hold_d="${HOLD_D:-/var/lib/keepalived/ops/holds}"
floor_d="${FLOOR_D:-/var/lib/keepalived/ops/floors}"
netif_d="${NETIF_D:-/var/lib/keepalived/ops/netif}"
clock_f="${CLOCK_F:-/var/lib/keepalived/ops/state/clock.epoch}"
out_f="${ELIG_TSV:-/var/lib/keepalived/ops/live/elig.tsv}"
mkdir -p "$(dirname "$out_f")"
clock=0
[[ -f "$clock_f" ]] && clock="$(tr -d '[:space:]' <"$clock_f")"
: >"$out_f"
[[ -f "$cand_f" ]] || exit 0
while IFS=$'\t' read -r name tip rank vrid vip || [[ -n "${name:-}" ]]; do
  [[ -z "${name:-}" ]] && continue
  until=0
  if [[ -f "$hold_d/${name}.hold" ]]; then
    until="$(grep -E '^until=' "$hold_d/${name}.hold" | head -n1 | cut -d= -f2- | tr -d '[:space:]')"
    until="${until:-0}"
  fi
  held=0
  if [[ "$until" -gt "$clock" ]]; then
    held=1
  fi
  floor=0
  if [[ -f "$floor_d/${name}.floor" ]]; then
    floor="$(tr -d '[:space:]' <"$floor_d/${name}.floor")"
  fi
  netif=0
  if [[ -f "$netif_d/${name}.gen" ]]; then
    netif="$(tr -d '[:space:]' <"$netif_d/${name}.gen")"
  fi
  eligible=1
  if [[ "$held" -eq 1 ]]; then
    eligible=0
  fi
  if [[ "$tip" -lt "$floor" ]]; then
    eligible=0
  fi
  if [[ "$netif" -lt "$floor" ]]; then
    eligible=0
  fi
  printf '%s\t%s\t%s\t%s\t%s\n' "$name" "$eligible" "$held" "$tip" "$floor" >>"$out_f"
done <"$cand_f"
EOF
chmod +x /app/ops/hold_m.sh

cat >/app/ops/hist_r.sh <<'EOF'
#!/bin/bash
set -euo pipefail
journal_f="${TRANS_J:-/var/lib/keepalived/ops/transitions.jsonl}"
out_f="${MOVES_TSV:-/var/lib/keepalived/ops/live/moves.tsv}"
mkdir -p "$(dirname "$out_f")"
: >"$out_f"
[[ -f "$journal_f" ]] || exit 0

jq -r -s '
  reduce .[] as $row ({a:{}};
    if $row.kind == "move" then
      .a[$row.eid] = $row
    elif $row.kind == "retract" then
      del(.a[$row.eid])
    else . end
  )
  | .a
  | to_entries
  | map(.value)
  | sort_by(.vrid, .epoch, .eid)
  | .[]
  | [.vrid, .epoch, .from, .to, .eid]
  | @tsv
' "$journal_f" >"$out_f"
EOF
chmod +x /app/ops/hist_r.sh

/app/ops/run_vrrp_seat.sh
/app/ops/run_vrrp_seat.sh
