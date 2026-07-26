#!/usr/bin/env bash
set -euo pipefail

cd /app

cp -f /app/x7/want.dat /app/x7/slot_s.dat

cat > /app/data/banks/kv_m.dat <<'EOF'
# bank tip journal — last matching keys win when materializing active INT8 scales
live_epoch=3
durable_epoch=7
durable_sealed=1
active_scale=e7
EOF

cat > /app/config/profiles/99-z.toml <<'EOF'
hot = 1
gen = 2
note = "gen2"
lane_prefer = "mask"
EOF

cat > /app/x7/mesh_m.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
ROOT="${APP_ROOT:-/app}"
J="$ROOT/data/banks/kv_m.dat"
BANKS="$ROOT/data/banks"

live_epoch=3
durable_epoch=7
durable_sealed=1
active_scale=e3

while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    ''|\#*) continue ;;
  esac
  key=${line%%=*}
  val=${line#*=}
  case "$key" in
    live_epoch) live_epoch=$val ;;
    durable_epoch) durable_epoch=$val ;;
    durable_sealed) durable_sealed=$val ;;
    active_scale) active_scale=$val ;;
  esac
done < "$J"

sealed_json=false
if [ "$durable_sealed" = "1" ]; then
  sealed_json=true
fi

cat > "$BANKS/tip_live.json" <<INNER
{
  "epoch": ${live_epoch},
  "sealed": false,
  "label": "live"
}
INNER

cat > "$BANKS/tip_durable.json" <<INNER
{
  "epoch": ${durable_epoch},
  "sealed": ${sealed_json},
  "label": "durable"
}
INNER

case "$active_scale" in
  e7) src="$BANKS/scales_e7.bin" ;;
  e3) src="$BANKS/scales_e3.bin" ;;
  *) src="$BANKS/scales_e3.bin" ;;
esac
if [ ! -f "$src" ]; then
  echo "missing scale blob: $src" >&2
  exit 1
fi
hdr=$(od -An -N1 -tu1 "$src" | tr -d ' ')
if [ "$hdr" != "$durable_epoch" ]; then
  echo "scale header ${hdr} != durable epoch ${durable_epoch}" >&2
  exit 1
fi
cp -f "$src" "$BANKS/scales_active.bin"
echo "bank_materialize_ok live=${live_epoch} durable=${durable_epoch} scale=${active_scale}"
EOF

cat > /app/eval/rebind_checkpoint.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
ROOT="${APP_ROOT:-/app}"
DUR="$ROOT/data/banks/tip_durable.json"
PACK="$ROOT/data/checkpoints/resume_pack.json"
STAMP="$ROOT/data/checkpoints/rebase.stamp"

epoch=$(python3 -c "import json; print(json.load(open('$DUR'))['epoch'])")
cat > "$PACK" <<INNER
{
  "epoch": ${epoch},
  "label": "rebased"
}
INNER
date -u +%Y%m%dT%H%M%SZ > "$STAMP"
echo "checkpoint_rebind_ok epoch=${epoch}"
EOF

chmod +x /app/x7/mesh_m.sh /app/eval/rebind_checkpoint.sh /app/eval/run_eval.sh

# Rebuild kernels + runtime after score path / tip-bind changes.
/app/scripts/build_all.sh

/app/eval/run_eval.sh

test -f /output/eval-ledger.json
python3 - <<'PY'
import json
from pathlib import Path
p = json.loads(Path("/output/eval-ledger.json").read_text())
assert p.get("version") == 1
assert p.get("bank_epoch") == 7
by = {r["id"]: r for r in p["scenarios"]}
assert by["cold_a"]["top1"] == by["resume_a"]["top1"] == 0.91
assert by["cold_b"]["top1"] == by["resume_b"]["top1"] == 0.87
assert by["mix_c"]["lane"] == "k2" and by["mix_c"]["mode"] == "mixed"
assert by["mix_c"]["top1"] == 0.84
assert by["mix_d"]["top1"] == 0.89
print("oracle_ledger_ok")
PY
echo "oracle_eval_ok"
