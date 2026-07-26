#!/bin/bash
# Oracle: bring the cache-volume seating desk to the durable end-state.
#
# The shipped desk runs on the surface plane: the preflight refreshes every
# live cache sheet from the pre-cutover working sheet on each pass, drops the
# abort package into the live drop-ins, and removes the apply receipt; the
# generation stage reads the live floor sheets, compares strictly, and never
# applies the sealed window; the window stage never shuts a volume; the fold
# keeps the first value per key; the emitter publishes a draft document from
# the live sheets. Rewrite the five stage helpers with the real multi-authority
# logic, select the durable plane, and let the desk converge.
set -euo pipefail

SV=/var/lib/lvm
SD=/etc/lvm/lvm.conf.d

# --- Live drop-in returns to the site standard --------------------------------
cat >"$SD/90-local.conf" <<'EOF'
tip_policy=durable_authority
bind_order=lexical
abort=none
EOF

# --- Durable apply receipt matching the target generation ---------------------
mkdir -p "$SV/ops/state"
target=$(tr -d '[:space:]' <"$SV/state/gen.target")
cat >"$SV/ops/state/apply.ok" <<EOF
gen=${target}
mode=seal
EOF

# --- Select the durable material plane ---------------------------------------
sed -i 's/^plane *= *"surface"/plane = "durable"/' "$SV/ops/prefer.toml"

# --- Stage 1: preflight gate --------------------------------------------------
cat >/app/ops/kelp_n.sh <<'EOS'
#!/bin/bash
set -euo pipefail
kelp_n() {
  local sx="${SHEET_D:-/etc/lvm/cache.d}"
  local sd="${DROPIN_D:-/etc/lvm/lvm.conf.d}"
  local sv="${LVM_ROOT:-/var/lib/lvm}"
  local plane aim rg rmode ok=0 row a b c
  mkdir -p "$sx" "$sd" "$sv/ops/state"
  plane=$(sed -n 's/^plane *= *"\([a-z]*\)".*/\1/p' "$sv/ops/prefer.toml" | head -n1)
  aim=$(tr -d '[:space:]' <"$sv/state/gen.target")
  if [[ "$plane" == "durable" && -f "$sv/ops/state/apply.ok" ]]; then
    rg=$(sed -n 's/^gen=\([0-9]*\)$/\1/p' "$sv/ops/state/apply.ok" | head -n1)
    rmode=$(sed -n 's/^mode=\(.*\)$/\1/p' "$sv/ops/state/apply.ok" | head -n1)
    if [[ "$rg" == "$aim" && "$rmode" == "seal" ]]; then
      ok=1
    fi
  fi
  if [[ "$ok" -eq 1 ]]; then
    python3 - "$sv/ops/journal.jsonl" "$sv/ops/pool.map" "$aim" "$sx" <<'PY'
import json
import sys
from pathlib import Path

journal, poolmap, aim_s, sheet_d = sys.argv[1:]
aim = int(aim_s)
row = {}
for line in Path(journal).read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    cand = json.loads(line)
    if (
        cand.get("kind") == "cutover"
        and int(cand.get("gen", -1)) == aim
        and cand.get("mode") == "seal"
    ):
        row = cand
ident = {}
for line in Path(poolmap).read_text().splitlines():
    line = line.split("#", 1)[0].strip()
    if "=" in line:
        left, right = line.split("=", 1)
        ident[left.strip()] = right.strip()
target = Path(sheet_d)
target.mkdir(parents=True, exist_ok=True)
for name, mode in sorted(row.get("modes", {}).items()):
    (target / (name + ".conf")).write_text(
        "# %s cache sheet (live)\ncache_mode = %s\npool_uuid = %s\n"
        % (name, mode, ident.get(name, ""))
    )
PY
  else
    while IFS= read -r row || [[ -n "${row:-}" ]]; do
      [[ -z "${row:-}" || "$row" =~ ^# ]] && continue
      a=$(sed -n 's/.*lv=\([a-z]*\).*/\1/p' <<<"$row")
      b=$(sed -n 's/.*mode=\([a-z]*\).*/\1/p' <<<"$row")
      c=$(sed -n 's/.*pool=\([a-z0-9-]*\).*/\1/p' <<<"$row")
      [[ -z "${a:-}" ]] && continue
      printf '# %s cache sheet (live)\ncache_mode = %s\npool_uuid = %s\n' \
        "$a" "$b" "$c" >"$sx/${a}.conf"
    done <"$sv/ops/surface.modes"
    if [[ -f "$sv/ops/abort.d/90-local.conf" ]]; then
      cp -f "$sv/ops/abort.d/90-local.conf" "$sd/90-local.conf"
    fi
    rm -f "$sv/ops/state/apply.ok"
  fi
}
kelp_n
EOS

# --- Stage 2: sealed window apply --------------------------------------------
cat >/app/ops/axle_r.sh <<'EOS'
#!/bin/bash
set -euo pipefail
axle_r() {
  local sv="${LVM_ROOT:-/var/lib/lvm}"
  local rl="${ROSTER:-/etc/lvm/roster.list}"
  local aim
  aim=$(tr -d '[:space:]' <"$sv/state/gen.target")
  mkdir -p "$sv/state"
  python3 - "$sv/ops/journal.jsonl" "$sv/state" "$aim" "$rl" "$sv/floors" <<'PY'
import json
import sys
from pathlib import Path

journal, state_s, aim_s, roster, floor_s = sys.argv[1:]
state = Path(state_s)
floor_d = Path(floor_s)
aim = int(aim_s)
row = {}
for line in Path(journal).read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    cand = json.loads(line)
    if (
        cand.get("kind") == "cutover"
        and int(cand.get("gen", -1)) == aim
        and cand.get("mode") == "seal"
    ):
        row = cand
tips = {k: int(v) for k, v in row.get("tips", {}).items()}
modes = dict(row.get("modes", {}))
names = [
    ln.strip()
    for ln in Path(roster).read_text().splitlines()
    if ln.strip() and not ln.strip().startswith("#")
]
for name in names:
    tip = int(tips.get(name, 0))
    (state / ("tip_" + name + ".gen")).write_text("%d\n" % tip)
    (state / ("pub_" + name + ".gen")).write_text("%d\n" % tip)
    (state / ("tip_mode_" + name)).write_text(modes.get(name, "") + "\n")
    fp = floor_d / (name + ".floor")
    bar = int(fp.read_text().strip()) if fp.exists() else 0
    (state / ("elig_" + name)).write_text("1\n" if tip >= bar else "0\n")
(state / "gen.live").write_text("%d\n" % aim)
PY
}
axle_r
EOS

# --- Stage 3: drop-in fold ----------------------------------------------------
cat >/app/rim/mesh_p.sh <<'EOS'
#!/bin/bash
set -euo pipefail
mesh_p() {
  local pd="${DROPIN_D:-/etc/lvm/lvm.conf.d}"
  local out="${EFF_POLICY:-/etc/lvm/effective.conf}"
  local f line a b
  mkdir -p "$(dirname "$out")"
  declare -A kv=()
  shopt -s nullglob
  for f in $(ls -1 "$pd"/*.conf 2>/dev/null | LC_ALL=C sort); do
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ -z "$line" ]] && continue
      [[ "$line" != *=* ]] && continue
      a="${line%%=*}"
      b="${line#*=}"
      kv["$a"]="$b"
    done <"$f"
  done
  shopt -u nullglob
  {
    for a in $(printf '%s\n' "${!kv[@]}" | LC_ALL=C sort); do
      printf '%s=%s\n' "$a" "${kv[$a]}"
    done
  } >"$out"
}
mesh_p
EOS

# --- Stage 4: maintenance windows --------------------------------------------
cat >/app/bag/skim_w.sh <<'EOS'
#!/bin/bash
set -euo pipefail
skim_w() {
  local sv="${LVM_ROOT:-/var/lib/lvm}"
  local hd="$sv/holds"
  local st="$sv/state"
  local now f a b line
  now=$(tr -d '[:space:]' <"$st/clock.epoch")
  mkdir -p "$st"
  : >"$st/holds.tsv"
  shopt -s nullglob
  for f in $(ls -1 "$hd"/*.hold 2>/dev/null | LC_ALL=C sort); do
    [[ -f "$f" ]] || continue
    a=$(basename "$f" .hold)
    b=0
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ "$line" == until_epoch=* ]] && b="${line#until_epoch=}"
    done <"$f"
    printf '%s\t%s\n' "$a" "$b" >>"$st/holds.tsv"
    if (( b > now )); then
      printf '1\n' >"$st/hold_block_${a}"
    else
      printf '0\n' >"$st/hold_block_${a}"
    fi
  done
  shopt -u nullglob
}
skim_w
EOS

# --- Stage 5: canonical emit --------------------------------------------------
cat >/app/deck/emit_j.sh <<'EOS'
#!/bin/bash
set -euo pipefail
exec /app/bin/cacheseat
EOS

chmod 755 /app/ops/kelp_n.sh /app/ops/axle_r.sh /app/rim/mesh_p.sh \
  /app/bag/skim_w.sh /app/deck/emit_j.sh

# --- Converge and verify ------------------------------------------------------
bash /app/ops/run_lvmcache_seat.sh
cp /output/lvmcache-seat.json /tmp/pass1.json
bash /app/ops/run_lvmcache_seat.sh

if ! cmp -s /tmp/pass1.json /output/lvmcache-seat.json; then
  echo "oracle: passes differ" >&2
  exit 1
fi
if ! grep -q '"seat_ok": true' /output/lvmcache-seat.json; then
  echo "oracle: desk did not settle" >&2
  exit 1
fi
if ! grep -q '^gen=' "$SV/ops/state/apply.ok"; then
  echo "oracle: receipt missing" >&2
  exit 1
fi
rm -f /tmp/pass1.json
echo "oracle: desk seated"
