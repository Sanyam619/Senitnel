#!/bin/bash
set -euo pipefail

site_sheet=/app/config/site_standard.conf
live_drop=/etc/consul.d/conf.d/90-local.hcl
target_gen=$(tr -d '[:space:]' </var/lib/consul/ops/state/generation.target)
cp -f "$site_sheet" "$live_drop"
{
  echo "gen=${target_gen}"
  echo "mode=seal"
} >/var/lib/consul/ops/state/cutover.ok

cat >/app/ops/arc_k.sh <<'EOF'
#!/bin/bash
set -euo pipefail
roll_d="${ROLL_D:-/var/lib/consul/ops/abort.d}"
sheet_d="${SHEET_D:-/etc/consul.d/conf.d}"
state_d="${STATE_D:-/var/lib/consul/ops/state}"
receipt="$state_d/cutover.ok"
target_gen=0
[[ -f "$state_d/generation.target" ]] &&
  target_gen="$(tr -d '[:space:]' <"$state_d/generation.target")"
mkdir -p "$sheet_d" "$state_d"
sealed=0
if [[ -f "$receipt" ]]; then
  got_gen=""
  got_mode=""
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | tr -d '[:space:]')"
    [[ -z "$line" ]] && continue
    case "$line" in
      gen=*) got_gen="${line#gen=}" ;;
      mode=*) got_mode="${line#mode=}" ;;
    esac
  done <"$receipt"
  if [[ "$got_gen" == "$target_gen" && "$got_mode" == "seal" ]]; then
    sealed=1
  fi
fi
if [[ "$sealed" -eq 0 ]]; then
  if [[ -f "$roll_d/90-local.hcl" ]]; then
    cp -f "$roll_d/90-local.hcl" "$sheet_d/90-local.hcl"
  fi
fi
EOF
chmod +x /app/ops/arc_k.sh

cat >/app/ops/weld_n.sh <<'EOF'
#!/bin/bash
set -euo pipefail
sheet_d="${SHEET_D:-/etc/consul.d/conf.d}"
out_f="${BIND_TSV:-/var/lib/consul/ops/live/bind.tsv}"
mkdir -p "$(dirname "$out_f")"
: >"$out_f"
declare -A seat=() held=()
for f in $(ls -1 "$sheet_d"/*.hcl 2>/dev/null | LC_ALL=C sort); do
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" ]] && continue
    mode="plain"
    if [[ "$line" == pin\ * ]]; then
      line="${line#pin }"
      mode="hold"
    elif [[ "$line" == drop\ * ]]; then
      line="${line#drop }"
      mode="clear"
    fi
    if [[ "$mode" == "clear" ]]; then
      key="$(echo "$line" | tr -d '[:space:]')"
      [[ "$key" == *.node ]] || continue
      nm="${key%.node}"
      [[ -n "${held[$nm]:-}" ]] && continue
      unset "seat[$nm]"
      continue
    fi
    [[ "$line" != *=* ]] && continue
    key="$(echo "${line%%=*}" | tr -d '[:space:]')"
    val="$(echo "${line#*=}" | tr -d '[:space:]')"
    [[ "$key" == *.node ]] || continue
    nm="${key%.node}"
    [[ -n "${held[$nm]:-}" ]] && continue
    seat["$nm"]="$val"
    if [[ "$mode" == "hold" ]]; then
      held["$nm"]=1
    fi
  done <"$f"
done
{
  for nm in $(printf '%s\n' "${!seat[@]}" | LC_ALL=C sort); do
    printf '%s\t%s\n' "$nm" "${seat[$nm]}"
  done
} >"$out_f"
EOF
chmod +x /app/ops/weld_n.sh

cat >/app/ops/crest_v.sh <<'EOF'
#!/bin/bash
set -euo pipefail
roster_f="${ROSTER_J:-/var/lib/consul/ops/roster.jsonl}"
drop_f="${SUPERSEDED:-/var/lib/consul/ops/superseded.list}"
out_f="${TIP_TSV:-/var/lib/consul/ops/live/tip.tsv}"
gen_f="${GEN_LIVE:-/var/lib/consul/ops/state/generation.live}"
mkdir -p "$(dirname "$out_f")" "$(dirname "$gen_f")"
: >"$out_f"
if [[ ! -f "$roster_f" ]]; then
  printf '0\n' >"$gen_f"
  exit 0
fi
gone='[]'
if [[ -f "$drop_f" ]]; then
  cleaned="$(sed 's/#.*//' "$drop_f" | tr -d '[:blank:]')"
  gone="$(printf '%s' "$cleaned" | jq -R -s 'split("\n") | map(select(length > 0))')"
fi
picked="$(jq -c -s --argjson gone "$gone" '
  map(select(.kind == "batch" and .sealed == true and .complete == true))
  | map(select(. as $b | ($gone | index($b.id)) == null))
  | sort_by(.gen)
  | .[-1] // empty
' "$roster_f")"
if [[ -z "$picked" || "$picked" == "null" ]]; then
  printf '0\n' >"$gen_f"
  exit 0
fi
printf '%s\n' "$(jq -r '.gen // 0' <<<"$picked")" >"$gen_f"
jq -r '.rows[]? | [.name, .node, (.gen | tonumber)] | @tsv' <<<"$picked" \
  | LC_ALL=C sort -t$'\t' -k1,1 >"$out_f"
EOF
chmod +x /app/ops/crest_v.sh

cat >/app/ops/lean_d.sh <<'EOF'
#!/bin/bash
set -euo pipefail
pref_f="${PREFER_J:-/var/lib/consul/ops/prefer.jsonl}"
gen_f="${GEN_LIVE:-/var/lib/consul/ops/state/generation.live}"
out_f="${ACTS_TSV:-/var/lib/consul/ops/live/acts.tsv}"
mkdir -p "$(dirname "$out_f")"
: >"$out_f"
[[ -f "$pref_f" ]] || exit 0
live_gen=0
[[ -f "$gen_f" ]] && live_gen="$(tr -d '[:space:]' <"$gen_f")"
[[ -n "$live_gen" ]] || live_gen=0
picked="$(jq -c -s --argjson g "$live_gen" '
  map(select(.kind == "batch" and .gen == $g and .sealed == true and .complete == true))
  | sort_by(.gen)
  | .[-1] // empty
' "$pref_f")"
if [[ -z "$picked" || "$picked" == "null" ]]; then
  exit 0
fi
jq -r '.rows[]? | [.source, .destination, .action] | @tsv' <<<"$picked" \
  | LC_ALL=C sort -t$'\t' -k1,1 -k2,2 >"$out_f"
EOF
chmod +x /app/ops/lean_d.sh

cat >/app/ops/ripple_q.sh <<'EOF'
#!/bin/bash
set -euo pipefail
journal_f="${INTENTS_J:-/var/lib/consul/ops/intents.jsonl}"
out_f="${CMT_TSV:-/var/lib/consul/ops/live/cmt.tsv}"
mkdir -p "$(dirname "$out_f")"
: >"$out_f"
[[ -f "$journal_f" ]] || exit 0
jq -r -s '
  reduce .[] as $row ({held: {}};
    if $row.kind == "commit" then .held[$row.eid] = $row
    elif $row.kind == "retract" then del(.held[$row.eid])
    else . end
  )
  | .held
  | to_entries
  | map(.value)
  | sort_by(.source, .destination, .eid)
  | .[]
  | [.source, .destination, .eid, .epoch]
  | @tsv
' "$journal_f" >"$out_f"
EOF
chmod +x /app/ops/ripple_q.sh

cat >/app/ops/sift_m.sh <<'EOF'
#!/bin/bash
set -euo pipefail
tip_f="${TIP_TSV:-/var/lib/consul/ops/live/tip.tsv}"
bind_f="${BIND_TSV:-/var/lib/consul/ops/live/bind.tsv}"
floor_d="${FLOOR_D:-/var/lib/consul/ops/floors}"
def_d="${DEF_D:-/app/data/consul}"
ex_d="${EX_D:-/var/lib/consul/ops/extra}"
out_f="${REG_TSV:-/var/lib/consul/ops/live/reg.tsv}"
mkdir -p "$(dirname "$out_f")"
: >"$out_f"
declare -A shipped=() seated=() tnode=() tgen=() names=()
shopt -s nullglob
for root in "$def_d" "$ex_d"; do
  [[ -d "$root" ]] || continue
  for f in "$root"/*.json; do
    nm="$(jq -r '.service.name // empty' "$f")"
    [[ -n "$nm" ]] || continue
    shipped["$nm"]="$(jq -r '.service.node // ""' "$f")"
    names["$nm"]=1
  done
done
shopt -u nullglob
if [[ -f "$bind_f" ]]; then
  while IFS=$'\t' read -r a b _rest || [[ -n "${a:-}" ]]; do
    [[ -z "${a:-}" ]] && continue
    seated["$a"]="$b"
    names["$a"]=1
  done <"$bind_f"
fi
if [[ -f "$tip_f" ]]; then
  while IFS=$'\t' read -r a b c _rest || [[ -n "${a:-}" ]]; do
    [[ -z "${a:-}" ]] && continue
    tnode["$a"]="$b"
    tgen["$a"]="$c"
    names["$a"]=1
  done <"$tip_f"
fi
{
  for nm in $(printf '%s\n' "${!names[@]}" | LC_ALL=C sort); do
    here="${seated[$nm]:-${shipped[$nm]:-}}"
    floor=0
    if [[ -f "$floor_d/${nm}.floor" ]]; then
      floor="$(tr -d '[:space:]' <"$floor_d/${nm}.floor")"
    fi
    g="${tgen[$nm]:-0}"
    ok=0
    if [[ -n "${tnode[$nm]:-}" && "$here" == "${tnode[$nm]}" && "$g" -ge "$floor" ]]; then
      ok=1
    fi
    printf '%s\t%s\t%s\n' "$nm" "$ok" "${tnode[$nm]:-}"
  done
} >"$out_f"
EOF
chmod +x /app/ops/sift_m.sh

cat >/app/ops/stamp_y.sh <<'EOF'
#!/bin/bash
set -euo pipefail
def_d="${DEF_D:-/app/data/consul}"
ex_d="${EX_D:-/var/lib/consul/ops/extra}"
map_f="${TOKEN_MAP:-/etc/consul.d/runtime/token.map}"
state_d="${STATE_D:-/var/lib/consul/ops/state}"
mkdir -p "$(dirname "$map_f")" "$state_d"
shopt -s nullglob
{
  for root in "$def_d" "$ex_d"; do
    [[ -d "$root" ]] || continue
    for f in "$root"/*.json; do
      nm="$(jq -r '.service.name // empty' "$f")"
      [[ -n "$nm" ]] || continue
      printf '%s passing\n' "$nm"
    done
  done
} | LC_ALL=C sort >"$map_f"
shopt -u nullglob
target_gen=0
[[ -f "$state_d/generation.target" ]] &&
  target_gen="$(tr -d '[:space:]' <"$state_d/generation.target")"
{
  printf 'gen=%s\n' "$target_gen"
  printf 'mode=seal\n'
} >"$state_d/cutover.ok"
EOF
chmod +x /app/ops/stamp_y.sh

/app/ops/run_consul_seat.sh
/app/ops/run_consul_seat.sh
