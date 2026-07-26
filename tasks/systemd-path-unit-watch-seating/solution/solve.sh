#!/bin/bash
set -euo pipefail

STATE=/var/lib/systemd/ops/state
target_gen=$(tr -d '[:space:]' <"$STATE/generation.target")

# Seal the cutover receipt for the current durable target.
{
  echo "gen=${target_gen}"
  echo "mode=seal"
} >"$STATE/cutover.ok"

cat >/app/ops/window_c.sh <<'EOF'
#!/bin/bash
set -euo pipefail
A_X="${ABORT_D:-/var/lib/systemd/ops/abort.d}"
B_Y="${LIVE_D:-/etc/systemd/system}"
OPS_STATE="${OPS_STATE:-/var/lib/systemd/ops/state}"
SITE="${SITE_STD:-/app/config/site_standard.conf}"
receipt="$OPS_STATE/cutover.ok"
target=""
[[ -f "$OPS_STATE/generation.target" ]] && target="$(tr -d '[:space:]' <"$OPS_STATE/generation.target")"
mkdir -p "$B_Y"
match=0
if [[ -f "$receipt" ]]; then
  g=""; m=""
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" ]] && continue
    case "$line" in
      gen=*) g="${line#gen=}" ;;
      mode=*) m="${line#mode=}" ;;
    esac
  done <"$receipt"
  if [[ "$g" == "$target" && "$m" == "seal" ]]; then
    match=1
  fi
fi
shopt -s nullglob
for unit_d in "$A_X"/*.path.d; do
  [[ -d "$unit_d" ]] || continue
  base="$(basename "$unit_d")"
  mkdir -p "$B_Y/$base"
  if [[ "$match" -eq 1 ]]; then
    cp -f "$SITE" "$B_Y/$base/90-local.conf"
  else
    for f in "$unit_d"/*.conf; do
      cp -f "$f" "$B_Y/$base/$(basename "$f")"
    done
  fi
done
shopt -u nullglob
EOF
chmod +x /app/ops/window_c.sh

cat >/app/ops/fold_d.sh <<'EOF'
#!/bin/bash
set -euo pipefail
ETC="${SYS_ETC:-/etc/systemd/system}"
META_D="${META_D:-/app/data/pathunits}"
EXTRA_M="${EXTRA_D:-/var/lib/systemd/ops/extra}"
OUT="${FOLD_TSV:-/var/lib/systemd/ops/live/fold.tsv}"
mkdir -p "$(dirname "$OUT")"
: >"$OUT"

read_unit_id() {
  local m="$1" id=""
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ "$line" == id=* ]] && id="${line#id=}"
  done <"$m"
  printf '%s' "$id"
}

fold_one() {
  local unit="$1"
  local exists="" changed="" dne="" section="" line k v f
  local files=()
  local base="$ETC/${unit}.path"
  [[ -f "$base" ]] && files+=("$base")
  if [[ -d "$ETC/${unit}.path.d" ]]; then
    while IFS= read -r f; do
      files+=("$f")
    done < <(find "$ETC/${unit}.path.d" -maxdepth 1 -name '*.conf' -type f | LC_ALL=C sort)
  fi
  for f in "${files[@]}"; do
    while IFS= read -r line || [[ -n "${line:-}" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ -z "$line" ]] && continue
      if [[ "$line" == \[*\] ]]; then
        section="$line"
        continue
      fi
      [[ "$section" == "[Path]" ]] || continue
      [[ "$line" != *=* ]] && continue
      k="${line%%=*}"; v="${line#*=}"
      case "$k" in
        PathExists) exists="$v" ;;
        PathChanged) changed="$v" ;;
        DirectoryNotEmpty) dne="$v" ;;
      esac
    done <"$f"
  done
  printf '%s\t%s\t%s\t%s\n' "$unit" "${exists:--}" "${changed:--}" "${dne:--}" >>"$OUT"
}

shopt -s nullglob
for root in "$META_D" "$EXTRA_M"; do
  [[ -d "$root" ]] || continue
  for m in "$root"/*.meta; do
    unit="$(read_unit_id "$m")"
    [[ -n "$unit" ]] || continue
    fold_one "$unit"
  done
done
shopt -u nullglob
EOF
chmod +x /app/ops/fold_d.sh

cat >/app/ops/tip_q.sh <<'EOF'
#!/bin/bash
set -euo pipefail
J="${PREFER_J:-/var/lib/systemd/ops/prefer.jsonl}"
OUT="${TIP_TSV:-/var/lib/systemd/ops/live/tip.tsv}"
GL="${GEN_LIVE:-/var/lib/systemd/ops/state/generation.live}"
mkdir -p "$(dirname "$OUT")" "$(dirname "$GL")"
: >"$OUT"

if [[ ! -f "$J" ]]; then
  printf '0\n' >"$GL"
  exit 0
fi

picked="$(jq -c -s '
  map(select(.kind=="batch" and .sealed==true and .complete==true))
  | sort_by(.gen)
  | .[-1] // empty
' "$J")"
if [[ -z "$picked" || "$picked" == "null" ]]; then
  printf '0\n' >"$GL"
  exit 0
fi
gen="$(jq -r '.gen // 0' <<<"$picked")"
printf '%s\n' "$gen" >"$GL"

jq -r '
  .rows[]? |
  [
    .id,
    (if (.exists // "") == "" then "-" else .exists end),
    (if (.changed // "") == "" then "-" else .changed end),
    (.tip | tostring)
  ] | @tsv
' <<<"$picked" >>"$OUT"
EOF
chmod +x /app/ops/tip_q.sh

cat >/app/ops/gate_h.sh <<'EOF'
#!/bin/bash
set -euo pipefail
OPS="${SYS_OPS:-/var/lib/systemd/ops}"
FOLD="${FOLD_TSV:-$OPS/live/fold.tsv}"
TIP="${TIP_TSV:-$OPS/live/tip.tsv}"
OUT="${ARM_TSV:-$OPS/live/arm.tsv}"
mkdir -p "$(dirname "$OUT")"
: >"$OUT"
[[ -f "$FOLD" ]] || exit 0

declare -A t_ex=() t_ch=() t_tip=()
if [[ -f "$TIP" ]]; then
  while IFS=$'\t' read -r u ex ch tp || [[ -n "${u:-}" ]]; do
    [[ -z "${u:-}" ]] && continue
    [[ "$ex" == "-" ]] && ex=""
    [[ "$ch" == "-" ]] && ch=""
    t_ex["$u"]="$ex"; t_ch["$u"]="$ch"; t_tip["$u"]="$tp"
  done <"$TIP"
fi

read_int() {
  local f="$1"
  if [[ -f "$f" ]]; then tr -d '[:space:]' <"$f"; else printf '0'; fi
}

while IFS=$'\t' read -r unit ex ch dne || [[ -n "${unit:-}" ]]; do
  [[ -z "${unit:-}" ]] && continue
  [[ "$ex" == "-" ]] && ex=""
  [[ "$ch" == "-" ]] && ch=""
  [[ "$dne" == "-" ]] && dne=""
  floor="$(read_int "$OPS/floors/$unit.floor")"
  wg="$(read_int "$OPS/watchgen/$unit.gen")"
  tip="${t_tip[$unit]:-0}"
  [[ -n "${tip//[0-9-]/}" ]] && tip=0
  armed=0
  if [[ "$ex" == "${t_ex[$unit]:-}" && "$ch" == "${t_ch[$unit]:-}" \
        && "$tip" -ge "$floor" && "$wg" -ge "$floor" \
        && -z "$dne" ]]; then
    armed=1
  fi
  printf '%s\t%s\n' "$unit" "$armed" >>"$OUT"
done <"$FOLD"
EOF
chmod +x /app/ops/gate_h.sh

cat >/app/ops/hist_r.sh <<'EOF'
#!/bin/bash
set -euo pipefail
J="${TRIGGER_J:-/var/lib/systemd/ops/triggers.jsonl}"
OUT="${TRIG_TSV:-/var/lib/systemd/ops/live/trig.tsv}"
mkdir -p "$(dirname "$OUT")"
: >"$OUT"
[[ -f "$J" ]] || exit 0

declare -A fire_unit=() fire_epoch=()
while IFS= read -r line || [[ -n "${line:-}" ]]; do
  [[ -z "${line:-}" ]] && continue
  kind="$(jq -r '.kind // empty' <<<"$line")"
  if [[ "$kind" == "fire" ]]; then
    eid="$(jq -r '.eid' <<<"$line")"
    fire_unit["$eid"]="$(jq -r '.unit' <<<"$line")"
    fire_epoch["$eid"]="$(jq -r '.epoch' <<<"$line")"
  elif [[ "$kind" == "retract" ]]; then
    eid="$(jq -r '.eid' <<<"$line")"
    unset "fire_unit[$eid]" 2>/dev/null || true
    unset "fire_epoch[$eid]" 2>/dev/null || true
  fi
done <"$J"

declare -A last=()
for eid in "${!fire_unit[@]}"; do
  u="${fire_unit[$eid]}"
  ep="${fire_epoch[$eid]}"
  if [[ -z "${last[$u]:-}" || "$ep" -gt "${last[$u]}" ]]; then
    last["$u"]="$ep"
  fi
done

for u in $(printf '%s\n' "${!last[@]}" | LC_ALL=C sort); do
  printf '%s\t%s\t%s\n' "$u" "${last[$u]}" "1" >>"$OUT"
done
EOF
chmod +x /app/ops/hist_r.sh

/app/ops/run_path_seat.sh
/app/ops/run_path_seat.sh
