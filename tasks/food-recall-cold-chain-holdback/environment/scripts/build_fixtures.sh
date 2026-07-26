#!/usr/bin/env bash
set -euo pipefail
BASE=/data/fixtures/days
mkdir -p "$BASE"

write_day() {
  local day="$1"
  local dir="$BASE/$day"
  mkdir -p "$dir"
  case "$day" in
    day_r0412)
      cat >"$dir/notice_feed.csv" <<'CSV'
unit_id,severity,sku_lane
LOT-D742,ACTIVE,DAIRY
CSV
      cat >"$dir/signoff_feed.csv" <<'CSV'
unit_id,auth_id,decision
LOT-D742,SA-9001,GRANT
CSV
      cat >"$dir/review_feed.csv" <<'CSV'
unit_id,status
CSV
      cat >"$dir/probe_feed.csv" <<'CSV'
unit_id,ts_c,probe_c
LOT-D742,100,38
LOT-F881,100,20
CSV
      cat >"$dir/dock_feed.csv" <<'CSV'
unit_id,store_id,qty_cases,parent_id
LOT-D742,ST-11,40,
LOT-F881,ST-22,30,
CSV
      cat >"$dir/route_map.json" <<'JSON'
{"hook_ts":50,"dock_ts":200,"units":["LOT-D742","LOT-F881"]}
JSON
      ;;
    day_r0413)
      cat >"$dir/notice_feed.csv" <<'CSV'
unit_id,severity,sku_lane
CSV
      cat >"$dir/signoff_feed.csv" <<'CSV'
unit_id,auth_id,decision
LOT-K220,SA-9002,GRANT
CSV
      cat >"$dir/review_feed.csv" <<'CSV'
unit_id,status
CSV
      cat >"$dir/probe_feed.csv" <<'CSV'
unit_id,ts_c,probe_c
LOT-K220,30,18
LOT-K220,120,19
CSV
      cat >"$dir/dock_feed.csv" <<'CSV'
unit_id,store_id,qty_cases,parent_id
LOT-K220,ST-33,25,
CSV
      cat >"$dir/route_map.json" <<'JSON'
{"hook_ts":100,"dock_ts":200,"units":["LOT-K220"]}
JSON
      ;;
    day_r0414)
      cat >"$dir/notice_feed.csv" <<'CSV'
unit_id,severity,sku_lane
CSV
      cat >"$dir/signoff_feed.csv" <<'CSV'
unit_id,auth_id,decision
LOT-T119,SA-9003,GRANT
CSV
      cat >"$dir/review_feed.csv" <<'CSV'
unit_id,status
LOT-T119,CLEARED_WITH_SIGNOFF
CSV
      cat >"$dir/probe_feed.csv" <<'CSV'
unit_id,ts_c,probe_c
LOT-T119,40,45
LOT-T119,150,36
CSV
      cat >"$dir/dock_feed.csv" <<'CSV'
unit_id,store_id,qty_cases,parent_id
LOT-T119,ST-44,18,
CSV
      cat >"$dir/route_map.json" <<'JSON'
{"hook_ts":100,"dock_ts":200,"units":["LOT-T119"]}
JSON
      ;;
    day_r0415)
      cat >"$dir/notice_feed.csv" <<'CSV'
unit_id,severity,sku_lane
LOT-P500,ACTIVE,DAIRY
CSV
      cat >"$dir/signoff_feed.csv" <<'CSV'
unit_id,auth_id,decision
CSV
      cat >"$dir/review_feed.csv" <<'CSV'
unit_id,status
CSV
      cat >"$dir/probe_feed.csv" <<'CSV'
unit_id,ts_c,probe_c
LOT-P500A,110,37
LOT-P500B,110,37
CSV
      cat >"$dir/dock_feed.csv" <<'CSV'
unit_id,store_id,qty_cases,parent_id
LOT-P500A,ST-55,10,LOT-P500
LOT-P500B,ST-55,10,LOT-P500
CSV
      cat >"$dir/route_map.json" <<'JSON'
{"hook_ts":100,"dock_ts":200,"units":["LOT-P500A","LOT-P500B"]}
JSON
      ;;
    day_r0416)
      cat >"$dir/notice_feed.csv" <<'CSV'
unit_id,severity,sku_lane
LOT-H901,ACTIVE,DAIRY
CSV
      cat >"$dir/signoff_feed.csv" <<'CSV'
unit_id,auth_id,decision
LOT-H901,SA-9010,GRANT
CSV
      cat >"$dir/review_feed.csv" <<'CSV'
unit_id,status
CSV
      cat >"$dir/probe_feed.csv" <<'CSV'
unit_id,ts_c,probe_c
LOT-H901,120,39
CSV
      cat >"$dir/dock_feed.csv" <<'CSV'
unit_id,store_id,qty_cases,parent_id
LOT-H901,ST-66,12,
LOT-H901,ST-77,8,
CSV
      cat >"$dir/route_map.json" <<'JSON'
{"hook_ts":100,"dock_ts":200,"units":["LOT-H901"]}
JSON
      ;;
  esac
}

for d in day_r0412 day_r0413 day_r0414 day_r0415 day_r0416; do
  write_day "$d"
done
