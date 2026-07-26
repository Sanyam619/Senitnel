#!/usr/bin/env bash
set -euo pipefail
ROOT="${APP_ROOT:-/app}"
J="$ROOT/data/banks/kv_m.dat"
BANKS="$ROOT/data/banks"

live_epoch=3
durable_epoch=7
durable_sealed=1

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
  esac
done < "$J"

sealed_json=false
if [ "$durable_sealed" = "1" ]; then
  sealed_json=true
fi

cat > "$BANKS/tip_live.json" <<EOF
{
  "epoch": ${live_epoch},
  "sealed": false,
  "label": "live"
}
EOF

cat > "$BANKS/tip_durable.json" <<EOF
{
  "epoch": ${durable_epoch},
  "sealed": ${sealed_json},
  "label": "durable"
}
EOF

cp -f "$BANKS/scales_e3.bin" "$BANKS/scales_active.bin"
echo "bank_materialize_ok live=${live_epoch} durable=${durable_epoch} scale=e3"
