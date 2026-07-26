#!/usr/bin/env bash
set -euo pipefail
BASE=/data/fixtures/days
mkdir -p "$BASE"

write_day() {
  local day="$1"
  local dir="$BASE/$day"
  mkdir -p "$dir"
  case "$day" in
    day_c0901)
      cat >"$dir/quarantine_feed.csv" <<'CSV'
volume_id,severity,collection_lane
VOL-D742,ACTIVE,RARE
CSV
      cat >"$dir/covenant_feed.csv" <<'CSV'
volume_id,auth_id,decision
VOL-D742,SA-9001,GRANT
CSV
      cat >"$dir/exhibit_feed.csv" <<'CSV'
volume_id,status
CSV
      cat >"$dir/rfid_feed.csv" <<'CSV'
volume_id,ts,signal_strength
VOL-D742,100,38
VOL-F881,100,20
CSV
      cat >"$dir/circulation_feed.csv" <<'CSV'
volume_id,branch_id,request_qty,parent_id
VOL-D742,ST-11,40,
VOL-F881,ST-22,30,
CSV
      cat >"$dir/sweep_map.json" <<'JSON'
{"sweep_start_ts":50,"sweep_end_ts":200,"units":["VOL-D742","VOL-F881"]}
JSON
      ;;
    day_c0902)
      cat >"$dir/quarantine_feed.csv" <<'CSV'
volume_id,severity,collection_lane
CSV
      cat >"$dir/covenant_feed.csv" <<'CSV'
volume_id,auth_id,decision
VOL-K220,SA-9002,GRANT
CSV
      cat >"$dir/exhibit_feed.csv" <<'CSV'
volume_id,status
CSV
      cat >"$dir/rfid_feed.csv" <<'CSV'
volume_id,ts,signal_strength
VOL-K220,30,18
VOL-K220,120,19
CSV
      cat >"$dir/circulation_feed.csv" <<'CSV'
volume_id,branch_id,request_qty,parent_id
VOL-K220,ST-33,25,
CSV
      cat >"$dir/sweep_map.json" <<'JSON'
{"sweep_start_ts":100,"sweep_end_ts":200,"units":["VOL-K220"]}
JSON
      ;;
    day_c0903)
      cat >"$dir/quarantine_feed.csv" <<'CSV'
volume_id,severity,collection_lane
CSV
      cat >"$dir/covenant_feed.csv" <<'CSV'
volume_id,auth_id,decision
VOL-T119,SA-9003,GRANT
CSV
      cat >"$dir/exhibit_feed.csv" <<'CSV'
volume_id,status
VOL-T119,CLEARED_FOR_EXHIBIT
CSV
      cat >"$dir/rfid_feed.csv" <<'CSV'
volume_id,ts,signal_strength
VOL-T119,40,45
VOL-T119,150,36
CSV
      cat >"$dir/circulation_feed.csv" <<'CSV'
volume_id,branch_id,request_qty,parent_id
VOL-T119,ST-44,18,
CSV
      cat >"$dir/sweep_map.json" <<'JSON'
{"sweep_start_ts":100,"sweep_end_ts":200,"units":["VOL-T119"]}
JSON
      ;;
    day_c0904)
      cat >"$dir/quarantine_feed.csv" <<'CSV'
volume_id,severity,collection_lane
VOL-P500,ACTIVE,RARE
CSV
      cat >"$dir/covenant_feed.csv" <<'CSV'
volume_id,auth_id,decision
CSV
      cat >"$dir/exhibit_feed.csv" <<'CSV'
volume_id,status
CSV
      cat >"$dir/rfid_feed.csv" <<'CSV'
volume_id,ts,signal_strength
VOL-P500A,110,37
VOL-P500B,110,37
CSV
      cat >"$dir/circulation_feed.csv" <<'CSV'
volume_id,branch_id,request_qty,parent_id
VOL-P500A,ST-55,10,VOL-P500
VOL-P500B,ST-55,10,VOL-P500
CSV
      cat >"$dir/sweep_map.json" <<'JSON'
{"sweep_start_ts":100,"sweep_end_ts":200,"units":["VOL-P500A","VOL-P500B"]}
JSON
      ;;
    day_c0906)
      cat >"$dir/quarantine_feed.csv" <<'CSV'
volume_id,severity,collection_lane
VOL-H901,ACTIVE,RARE
CSV
      cat >"$dir/covenant_feed.csv" <<'CSV'
volume_id,auth_id,decision
VOL-H901,SA-9010,GRANT
CSV
      cat >"$dir/exhibit_feed.csv" <<'CSV'
volume_id,status
CSV
      cat >"$dir/rfid_feed.csv" <<'CSV'
volume_id,ts,signal_strength
VOL-H901,120,39
CSV
      cat >"$dir/circulation_feed.csv" <<'CSV'
volume_id,branch_id,request_qty,parent_id
VOL-H901,ST-66,12,
VOL-H901,ST-77,8,
CSV
      cat >"$dir/sweep_map.json" <<'JSON'
{"sweep_start_ts":100,"sweep_end_ts":200,"units":["VOL-H901"]}
JSON
      ;;
  esac
}

for d in day_c0901 day_c0902 day_c0903 day_c0904 day_c0906; do
  write_day "$d"
done
