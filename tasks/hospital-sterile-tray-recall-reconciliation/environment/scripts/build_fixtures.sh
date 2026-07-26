#!/usr/bin/env bash
set -euo pipefail
BASE=/data/fixtures/cases
mkdir -p "$BASE"

write_case() {
  local c="$1"
  local d="$BASE/$c"
  mkdir -p "$d"
  case "$c" in
    case_c0412)
      cat >"$d/scan_feed.csv" <<'CSV'
tray_id,ts_epoch,zone_id,event_code
T-101,110,Z-A,OUTBOUND
CSV
      cat >"$d/cycle_board.csv" <<'CSV'
load_id,zone_id,cycle_start,cycle_end,chamber
LOAD-1,Z-A,100,160,CH-1
CSV
      cat >"$d/lot_notice.csv" <<'CSV'
lot_id,zone_id,effective_ts,recall_class
L-R1,Z-A,105,CLASS_A
CSV
      cat >"$d/or_manifest.csv" <<'CSV'
case_id,tray_id,room_id,case_start_epoch
CASE-1,T-101,OR-3,150
CSV
      cat >"$d/set_catalog.csv" <<'CSV'
parent_tray,child_tray
CSV
      cat >"$d/quarantine_snap.json" <<'JSON'
{"version":1,"held_trays":[]}
JSON
      ;;
    case_c0413)
      cat >"$d/scan_feed.csv" <<'CSV'
tray_id,ts_epoch,zone_id,event_code
T-200,210,Z-B,OUTBOUND
CSV
      cat >"$d/cycle_board.csv" <<'CSV'
load_id,zone_id,cycle_start,cycle_end,chamber
LOAD-2,Z-B,180,240,CH-2
CSV
      cat >"$d/lot_notice.csv" <<'CSV'
lot_id,zone_id,effective_ts,recall_class
L-RX,Z-C,100,CLASS_A
CSV
      cat >"$d/or_manifest.csv" <<'CSV'
case_id,tray_id,room_id,case_start_epoch
CASE-2,T-200,OR-1,220
CSV
      cat >"$d/set_catalog.csv" <<'CSV'
parent_tray,child_tray
CSV
      cat >"$d/quarantine_snap.json" <<'JSON'
{"version":1,"held_trays":[]}
JSON
      ;;
    case_c0414)
      cat >"$d/scan_feed.csv" <<'CSV'
tray_id,ts_epoch,zone_id,event_code
T-300,145,Z-C,OUTBOUND
CSV
      cat >"$d/cycle_board.csv" <<'CSV'
load_id,zone_id,cycle_start,cycle_end,chamber
LOAD-3,Z-C,100,140,CH-1
CSV
      cat >"$d/lot_notice.csv" <<'CSV'
lot_id,zone_id,effective_ts,recall_class
CSV
      cat >"$d/or_manifest.csv" <<'CSV'
case_id,tray_id,room_id,case_start_epoch
CASE-3,T-300,OR-2,200
CSV
      cat >"$d/set_catalog.csv" <<'CSV'
parent_tray,child_tray
CSV
      cat >"$d/quarantine_snap.json" <<'JSON'
{"version":1,"held_trays":[]}
JSON
      ;;
    case_c0415)
      cat >"$d/scan_feed.csv" <<'CSV'
tray_id,ts_epoch,zone_id,event_code
T-401,120,Z-D,OUTBOUND
CSV
      cat >"$d/cycle_board.csv" <<'CSV'
load_id,zone_id,cycle_start,cycle_end,chamber
LOAD-4,Z-D,100,180,CH-3
CSV
      cat >"$d/lot_notice.csv" <<'CSV'
lot_id,zone_id,effective_ts,recall_class
L-R2,Z-D,100,CLASS_B
CSV
      cat >"$d/or_manifest.csv" <<'CSV'
case_id,tray_id,room_id,case_start_epoch
CASE-4,T-402,OR-4,160
CSV
      cat >"$d/set_catalog.csv" <<'CSV'
parent_tray,child_tray
T-401,T-402
CSV
      cat >"$d/quarantine_snap.json" <<'JSON'
{"version":1,"held_trays":[]}
JSON
      ;;
    case_c0416)
      cat >"$d/scan_feed.csv" <<'CSV'
tray_id,ts_epoch,zone_id,event_code
T-501,300,Z-E,OUTBOUND
T-502,305,Z-E,OUTBOUND
CSV
      cat >"$d/cycle_board.csv" <<'CSV'
load_id,zone_id,cycle_start,cycle_end,chamber
LOAD-5,Z-E,280,340,CH-2
CSV
      cat >"$d/lot_notice.csv" <<'CSV'
lot_id,zone_id,effective_ts,recall_class
L-R3,Z-E,290,CLASS_A
CSV
      cat >"$d/or_manifest.csv" <<'CSV'
case_id,tray_id,room_id,case_start_epoch
CASE-5,T-501,OR-5,320
CASE-5,T-502,OR-5,320
CSV
      cat >"$d/set_catalog.csv" <<'CSV'
parent_tray,child_tray
CSV
      cat >"$d/quarantine_snap.json" <<'JSON'
{"version":1,"held_trays":[]}
JSON
      ;;
    case_c0417)
      cat >"$d/scan_feed.csv" <<'CSV'
tray_id,ts_epoch,zone_id,event_code
T-601,400,Z-F,OUTBOUND
CSV
      cat >"$d/cycle_board.csv" <<'CSV'
load_id,zone_id,cycle_start,cycle_end,chamber
LOAD-6,Z-F,380,420,CH-1
CSV
      cat >"$d/lot_notice.csv" <<'CSV'
lot_id,zone_id,effective_ts,recall_class
L-R4,Z-F,390,CLASS_B
CSV
      cat >"$d/or_manifest.csv" <<'CSV'
case_id,tray_id,room_id,case_start_epoch
CASE-6,T-601,OR-6,410
CSV
      cat >"$d/set_catalog.csv" <<'CSV'
parent_tray,child_tray
CSV
      cat >"$d/quarantine_snap.json" <<'JSON'
{"version":1,"held_trays":["T-601"]}
JSON
      ;;
    case_c0418)
      cat >"$d/scan_feed.csv" <<'CSV'
tray_id,ts_epoch,zone_id,event_code
T-701,112,Z-H,OUTBOUND
CSV
      cat >"$d/cycle_board.csv" <<'CSV'
load_id,zone_id,cycle_start,cycle_end,chamber
LOAD-8,Z-H,100,140,CH-3
CSV
      cat >"$d/lot_notice.csv" <<'CSV'
lot_id,zone_id,effective_ts,recall_class
L-R5,Z-H,125,CLASS_B
CSV
      cat >"$d/or_manifest.csv" <<'CSV'
case_id,tray_id,room_id,case_start_epoch
CASE-8,T-701,OR-8,120
CSV
      cat >"$d/set_catalog.csv" <<'CSV'
parent_tray,child_tray
CSV
      cat >"$d/quarantine_snap.json" <<'JSON'
{"version":1,"held_trays":[]}
JSON
      ;;
  esac
}

for c in case_c0412 case_c0413 case_c0414 case_c0415 case_c0416 case_c0417 case_c0418; do
  write_case "$c"
done
