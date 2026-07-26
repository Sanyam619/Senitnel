#!/usr/bin/env bash
set -euo pipefail
BASE=/data/fixtures/shifts
mkdir -p "$BASE"

write_shift() {
  local s="$1"
  local d="$BASE/$s"
  mkdir -p "$d"
  case "$s" in
    shift_w1206)
      cat >"$d/pulse_feed.csv" <<'CSV'
unit_id,ts_min,node_id,qty
T1,110,N-A,180
T2,40,N-A,120
CSV
      cat >"$d/stand_board.csv" <<'CSV'
craft_id,node_id,win_start,win_end,code
AC101,N-A,100,160,TYPE1
CSV
      cat >"$d/assay_feed.csv" <<'CSV'
node_id,ts_min,pct
N-A,105,50
CSV
      cat >"$d/cell_band.json" <<'JSON'
{"divert_qty":0,"alt_node":"N-X"}
JSON
      cat >"$d/slot_board.csv" <<'CSV'
craft_id,slot_min
AC101,200
CSV
      cat >"$d/retain_gauge.csv" <<'CSV'
node_id,cap_qty,base_qty
N-P,400,50
N-X,200,20
CSV
      ;;
    shift_w1207)
      cat >"$d/pulse_feed.csv" <<'CSV'
unit_id,ts_min,node_id,qty
T3,250,N-B,500
CSV
      cat >"$d/stand_board.csv" <<'CSV'
craft_id,node_id,win_start,win_end,code
AC202,N-B,200,280,TYPE4
CSV
      cat >"$d/assay_feed.csv" <<'CSV'
node_id,ts_min,pct
N-B,240,40
CSV
      cat >"$d/cell_band.json" <<'JSON'
{"divert_qty":0,"alt_node":"N-X"}
JSON
      cat >"$d/slot_board.csv" <<'CSV'
craft_id,slot_min
AC202,300
CSV
      cat >"$d/retain_gauge.csv" <<'CSV'
node_id,cap_qty,base_qty
N-P,500,50
N-X,200,20
CSV
      ;;
    shift_w1208)
      cat >"$d/pulse_feed.csv" <<'CSV'
unit_id,ts_min,node_id,qty
T4,150,N-C,400
T5,155,N-C,100
CSV
      cat >"$d/stand_board.csv" <<'CSV'
craft_id,node_id,win_start,win_end,code
AC303,N-C,140,180,TYPE1
CSV
      cat >"$d/assay_feed.csv" <<'CSV'
node_id,ts_min,pct
N-C,145,80
CSV
      cat >"$d/cell_band.json" <<'JSON'
{"divert_qty":0,"alt_node":"N-X"}
JSON
      cat >"$d/slot_board.csv" <<'CSV'
craft_id,slot_min
AC303,220
CSV
      cat >"$d/retain_gauge.csv" <<'CSV'
node_id,cap_qty,base_qty
N-P,600,50
N-X,200,20
CSV
      ;;
    shift_w1209)
      cat >"$d/pulse_feed.csv" <<'CSV'
unit_id,ts_min,node_id,qty
T6,300,N-D,1000
CSV
      cat >"$d/stand_board.csv" <<'CSV'
craft_id,node_id,win_start,win_end,code
AC404,N-D,280,340,TYPE1
CSV
      cat >"$d/assay_feed.csv" <<'CSV'
node_id,ts_min,pct
N-D,290,100
CSV
      cat >"$d/cell_band.json" <<'JSON'
{"divert_qty":120,"alt_node":"N-X"}
JSON
      cat >"$d/slot_board.csv" <<'CSV'
craft_id,slot_min
AC404,400
CSV
      cat >"$d/retain_gauge.csv" <<'CSV'
node_id,cap_qty,base_qty
N-P,400,50
N-X,200,20
CSV
      ;;
    shift_w1210)
      cat >"$d/pulse_feed.csv" <<'CSV'
unit_id,ts_min,node_id,qty
T7,500,N-E,600
T8,520,N-E,200
CSV
      cat >"$d/stand_board.csv" <<'CSV'
craft_id,node_id,win_start,win_end,code
AC505,N-E,480,540,TYPE4
AC506,N-E,490,550,TYPE4
CSV
      cat >"$d/assay_feed.csv" <<'CSV'
node_id,ts_min,pct
N-E,505,55
CSV
      cat >"$d/cell_band.json" <<'JSON'
{"divert_qty":80,"alt_node":"N-X"}
JSON
      cat >"$d/slot_board.csv" <<'CSV'
craft_id,slot_min
AC505,600
AC506,610
CSV
      cat >"$d/retain_gauge.csv" <<'CSV'
node_id,cap_qty,base_qty
N-P,500,50
N-X,250,30
CSV
      ;;
    shift_w1211)
      cat >"$d/pulse_feed.csv" <<'CSV'
unit_id,ts_min,node_id,qty
T9,210,N-F,300
CSV
      cat >"$d/stand_board.csv" <<'CSV'
craft_id,node_id,win_start,win_end,code
AC701,N-F,200,220,TYPE1
CSV
      cat >"$d/assay_feed.csv" <<'CSV'
node_id,ts_min,pct
N-F,210,100
CSV
      cat >"$d/cell_band.json" <<'JSON'
{"divert_qty":40,"alt_node":"N-X"}
JSON
      cat >"$d/slot_board.csv" <<'CSV'
craft_id,slot_min
AC701,260
CSV
      cat >"$d/retain_gauge.csv" <<'CSV'
node_id,cap_qty,base_qty
N-P,350,80
N-X,200,25
CSV
      ;;
    shift_w1212)
      cat >"$d/pulse_feed.csv" <<'CSV'
unit_id,ts_min,node_id,qty
T11,165,N-G,240
T12,170,N-G,60
CSV
      cat >"$d/stand_board.csv" <<'CSV'
craft_id,node_id,win_start,win_end,code
AC801,N-G,160,180,TYPE4
CSV
      cat >"$d/assay_feed.csv" <<'CSV'
node_id,ts_min,pct
N-G,165,50
CSV
      cat >"$d/cell_band.json" <<'JSON'
{"divert_qty":0,"alt_node":"N-X"}
JSON
      cat >"$d/slot_board.csv" <<'CSV'
craft_id,slot_min
AC801,240
CSV
      cat >"$d/retain_gauge.csv" <<'CSV'
node_id,cap_qty,base_qty
N-P,500,50
N-X,200,20
CSV
      ;;
  esac
}

for s in shift_w1206 shift_w1207 shift_w1208 shift_w1209 shift_w1210 shift_w1211 shift_w1212; do
  write_shift "$s"
done

(
  cd "$BASE"
  find . -type f ! -name '.fixture_checksums.sha256' -print | sort | while read -r f; do
    sha256sum "${f#./}"
  done >"$BASE/.fixture_checksums.sha256"
)
