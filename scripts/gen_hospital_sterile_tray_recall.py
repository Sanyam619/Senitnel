#!/usr/bin/env python3
"""Generate hospital-sterile-tray-recall-reconciliation task files."""
from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tasks" / "hospital-sterile-tray-recall-reconciliation"
ENV = ROOT / "environment"


def w(rel: str, content: str) -> None:
    if rel.startswith("environment/"):
        p = ENV / rel.removeprefix("environment/")
    else:
        p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


INSTRUCTION = """
Central sterile processing runs a Go batch from `/opt/csp/scripts/run-case.sh`
with `--case <case-name>` and `--root /data/fixtures`. Each case writes
`/data/out/<case>/quarantine_ledger.jsonl` (tray_id, state, reason_code,
source_case, seq), `/data/out/<case>/tray_disposition.json` (version, trays),
and `/data/out/<case>/recall_audit.tsv` (lot_id, trays_blocked, trays_cleared,
exposure_class).

Disposition precedence, notice timing, set inheritance, cycle-window checks,
and audit tally semantics are specified in `/opt/csp/config/disposition_policy.toml`.
A recent deploy no longer enforces that policy for cases `case_c0412` through
`case_c0418` using fixtures under `/data/fixtures`. Ledger, disposition, and
audit outputs for those cases must match the policy file on every run.
"""

DISPOSITION_POLICY = """
# CSP disposition policy (reference contract for ledger and audit outputs)

[[precedence]]
order = ["SNAP_HOLD", "LOT_RECALL", "STERILE_GAP", "CLEAR"]

[reason_codes.SNAP_HOLD]
state = "HOLD"
summary = "Tray id is listed on the quarantine snapshot held_trays for the case."

[reason_codes.LOT_RECALL]
state = "HOLD"
summary = "An implant lot recall notice is active for the tray outbound scan zone."
notice_zone = "notice.zone_id equals latest outbound scan zone_id for the tray"
notice_timing = "notice.effective_ts is at or before the OR case_start_epoch"

[reason_codes.STERILE_GAP]
state = "HOLD"
summary = "Latest outbound scan timestamp is outside the autoclave cycle window for its zone."

[reason_codes.CLEAR]
state = "RELEASE"
summary = "No higher-precedence block applies."

[set_inheritance]
enabled = true
summary = "When set_catalog maps child_tray to parent_tray, a parent LOT_RECALL block applies to the child on the same case."

[audit]
blocked_field = "trays_blocked"
cleared_field = "trays_cleared"
exposure_field = "exposure_class"
exposure_source = "recall_class on the matching lot notice row"
rerun_stable = "Repeated runs on a case must not change quarantine_ledger.jsonl or recall_audit.tsv bytes."
"""

TASK_TOML = """
version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "security"
subcategories = ["tool_specific"]
number_of_milestones = 0
codebase_size = "small"
languages = ["go", "bash"]
tags = ["go", "healthcare", "sterile-processing", "recall", "traceability", "compliance"]
expert_time_estimate_min = 240
junior_time_estimate_min = 480

[verifier]
timeout_sec = 600

[agent]
timeout_sec = 900

[environment]
allow_internet = false
build_timeout_sec = 900
cpus = 2
memory_mb = 4096
storage_mb = 10240
"""

OUTPUT_CONTRACT = """
user_visible_outputs = [
  "/data/out/<case>/quarantine_ledger.jsonl",
  "/data/out/<case>/tray_disposition.json",
  "/data/out/<case>/recall_audit.tsv",
]

internal_harness_files = [
  "/data/fixtures/cases/",
]

[structured_outputs.quarantine_ledger]
target = "/data/out/<case>/quarantine_ledger.jsonl"
format = "jsonl"
instruction_checks = ["tray_id", "state", "reason_code", "source_case", "seq"]

[structured_outputs.tray_disposition]
target = "/data/out/<case>/tray_disposition.json"
format = "json"
instruction_checks = ["version", "trays"]

[structured_outputs.recall_audit]
target = "/data/out/<case>/recall_audit.tsv"
format = "tsv"
instruction_checks = ["lot_id", "trays_blocked", "trays_cleared", "exposure_class"]
"""

GO_MOD = """module csp.local/reconcile

go 1.22
"""

SITE_TOML = """k_skew = 60
k_walk = true
k_audit = 1
k_zone = 0
"""

MAIN_GO = """
package main

import (
\t"fmt"
\t"os"

\t"csp.local/reconcile/internal/core"
)

func main() {
\tif len(os.Args) < 3 {
\t\tfmt.Fprintf(os.Stderr, "usage: cspd <case> <root>\\n")
\t\tos.Exit(2)
\t}
\tif err := core.ExecN(os.Args[1], os.Args[2]); err != nil {
\t\tfmt.Fprintf(os.Stderr, "case failed: %v\\n", err)
\t\tos.Exit(1)
\t}
}
"""

RUN_CASE = """#!/usr/bin/env bash
set -euo pipefail
CASE=""
ROOT="/data/fixtures"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --case) CASE="$2"; shift 2 ;;
    --root) ROOT="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
if [[ -z "$CASE" ]]; then
  echo "usage: run-case.sh --case <name> [--root /data/fixtures]" >&2
  exit 2
fi
/opt/csp/bin/cspd "$CASE" "$ROOT"
"""

BUILD_FIXTURES = r"""#!/usr/bin/env bash
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
"""

GO_FILES: dict[str, str] = {}

GO_FILES["internal/model/types.go"] = """
package model

type LedgerRow struct {
\tTrayID     string `json:"tray_id"`
\tState      string `json:"state"`
\tReasonCode string `json:"reason_code"`
\tSourceCase string `json:"source_case"`
\tSeq        int    `json:"seq"`
}

type TrayRow struct {
\tTrayID     string `json:"tray_id"`
\tState      string `json:"state"`
\tReasonCode string `json:"reason_code"`
\tSourceCase string `json:"source_case"`
}

type AuditRow struct {
\tLotID          string
\tTraysBlocked   int
\tTraysCleared   int
\tExposureClass  string
}
"""

GO_FILES["internal/io/csvr.go"] = """
package io

import (
\t"bufio"
\t"os"
\t"strings"
)

func ReadCSV(path string) ([][]string, error) {
\tf, err := os.Open(path)
\tif err != nil {
\t\treturn nil, err
\t}
\tdefer f.Close()
\tvar rows [][]string
\tscan := bufio.NewScanner(f)
\tfirst := true
\tfor scan.Scan() {
\t\tline := strings.TrimSpace(scan.Text())
\t\tif line == "" {
\t\t\tcontinue
\t\t}
\t\tif first {
\t\t\tfirst = false
\t\t\tcontinue
\t\t}
\t\trows = append(rows, strings.Split(line, ","))
\t}
\treturn rows, scan.Err()
}
"""

GO_FILES["internal/io/jsonw.go"] = """
package io

import (
\t"encoding/json"
\t"fmt"
\t"os"
\t"path/filepath"

\t"csp.local/reconcile/internal/model"
)

func WriteLedger(path string, rows []model.LedgerRow) error {
\tif err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
\t\treturn err
\t}
\tf, err := os.Create(path)
\tif err != nil {
\t\treturn err
\t}
\tdefer f.Close()
\tfor _, r := range rows {
\t\tb, _ := json.Marshal(r)
\t\tif _, err := fmt.Fprintf(f, "%s\\n", b); err != nil {
\t\t\treturn err
\t\t}
\t}
\treturn nil
}

func WriteDisposition(path string, trays []model.TrayRow) error {
\tif err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
\t\treturn err
\t}
\tpayload := struct {
\t\tVersion int             `json:"version"`
\t\tTrays   []model.TrayRow `json:"trays"`
\t}{Version: 1, Trays: trays}
\tb, err := json.MarshalIndent(payload, "", "  ")
\tif err != nil {
\t\treturn err
\t}
\treturn os.WriteFile(path, b, 0o644)
}
"""

GO_FILES["internal/io/tsvw.go"] = """
package io

import (
\t"fmt"
\t"os"
\t"path/filepath"
\t"sort"
\t"strings"

\t"csp.local/reconcile/internal/model"
)

func WriteAudit(path string, rows []model.AuditRow) error {
\tif err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
\t\treturn err
\t}
\tsort.Slice(rows, func(i, j int) bool { return rows[i].LotID < rows[j].LotID })
\tlines := []string{"lot_id\\ttrays_blocked\\ttrays_cleared\\texposure_class"}
\tfor _, r := range rows {
\t\tlines = append(lines, fmt.Sprintf("%s\\t%d\\t%d\\t%s",
\t\t\tr.LotID, r.TraysBlocked, r.TraysCleared, r.ExposureClass))
\t}
\treturn os.WriteFile(path, []byte(strings.Join(lines, "\\n")+"\\n"), 0o644)
}
"""

for pkg, fname, body in [
    ("scanfeed", "row.go", """
package scanfeed

type Row struct {
\tTrayID    string
\tTSEpoch   int
\tZoneID    string
\tEventCode string
}
"""),
    ("scanfeed", "reader.go", """
package scanfeed

import (
\t"path/filepath"
\t"strconv"

\tcsv "csp.local/reconcile/internal/io"
)

func Load(dir string) ([]Row, error) {
\trows, err := csv.ReadCSV(filepath.Join(dir, "scan_feed.csv"))
\tif err != nil {
\t\treturn nil, err
\t}
\tvar out []Row
\tfor _, c := range rows {
\t\tts, _ := strconv.Atoi(c[1])
\t\tout = append(out, Row{TrayID: c[0], TSEpoch: ts, ZoneID: c[2], EventCode: c[3]})
\t}
\treturn out, nil
}
"""),
    ("cycleboard", "row.go", """
package cycleboard

type Row struct {
\tLoadID      string
\tZoneID      string
\tCycleStart  int
\tCycleEnd    int
\tChamber     string
}
"""),
    ("cycleboard", "reader.go", """
package cycleboard

import (
\t"path/filepath"
\t"strconv"

\tcsv "csp.local/reconcile/internal/io"
)

func Load(dir string) ([]Row, error) {
\trows, err := csv.ReadCSV(filepath.Join(dir, "cycle_board.csv"))
\tif err != nil {
\t\treturn nil, err
\t}
\tvar out []Row
\tfor _, c := range rows {
\t\tcs, _ := strconv.Atoi(c[2])
\t\tce, _ := strconv.Atoi(c[3])
\t\tout = append(out, Row{LoadID: c[0], ZoneID: c[1], CycleStart: cs, CycleEnd: ce, Chamber: c[4]})
\t}
\treturn out, nil
}
"""),
    ("lotnotice", "row.go", """
package lotnotice

type Row struct {
\tLotID       string
\tZoneID      string
\tEffectiveTS int
\tRecallClass string
}
"""),
    ("lotnotice", "reader.go", """
package lotnotice

import (
\t"path/filepath"
\t"strconv"

\tcsv "csp.local/reconcile/internal/io"
)

func Load(dir string) ([]Row, error) {
\trows, err := csv.ReadCSV(filepath.Join(dir, "lot_notice.csv"))
\tif err != nil {
\t\treturn nil, err
\t}
\tvar out []Row
\tfor _, c := range rows {
\t\teff, _ := strconv.Atoi(c[2])
\t\tout = append(out, Row{LotID: c[0], ZoneID: c[1], EffectiveTS: eff, RecallClass: c[3]})
\t}
\treturn out, nil
}
"""),
    ("ormanifest", "row.go", """
package ormanifest

type Row struct {
\tCaseID          string
\tTrayID          string
\tRoomID          string
\tCaseStartEpoch  int
}
"""),
    ("ormanifest", "reader.go", """
package ormanifest

import (
\t"path/filepath"
\t"strconv"

\tcsv "csp.local/reconcile/internal/io"
)

func Load(dir string) ([]Row, error) {
\trows, err := csv.ReadCSV(filepath.Join(dir, "or_manifest.csv"))
\tif err != nil {
\t\treturn nil, err
\t}
\tvar out []Row
\tfor _, c := range rows {
\t\tcs, _ := strconv.Atoi(c[3])
\t\tout = append(out, Row{CaseID: c[0], TrayID: c[1], RoomID: c[2], CaseStartEpoch: cs})
\t}
\treturn out, nil
}
"""),
    ("setcatalog", "row.go", """
package setcatalog

type Row struct {
\tParentTray string
\tChildTray  string
}
"""),
    ("setcatalog", "reader.go", """
package setcatalog

import (
\t"path/filepath"

\tcsv "csp.local/reconcile/internal/io"
)

func Load(dir string) ([]Row, error) {
\trows, err := csv.ReadCSV(filepath.Join(dir, "set_catalog.csv"))
\tif err != nil {
\t\treturn nil, err
\t}
\tvar out []Row
\tfor _, c := range rows {
\t\tif len(c) < 2 || c[0] == "" {
\t\t\tcontinue
\t\t}
\t\tout = append(out, Row{ParentTray: c[0], ChildTray: c[1]})
\t}
\treturn out, nil
}
"""),
]:
    GO_FILES[f"internal/ingest/{pkg}/{fname}"] = body

GO_FILES["internal/ingest/quarantinesnap/doc.go"] = """
package quarantinesnap
"""

GO_FILES["internal/cfg/load.go"] = """
package cfg

import (
\t"os"
\t"strconv"
\t"strings"
)

var sitePath = "/opt/csp/config/site.toml"

func readKey(key string) (string, bool) {
\tb, err := os.ReadFile(sitePath)
\tif err != nil {
\t\treturn "", false
\t}
\tfor _, line := range strings.Split(string(b), "\\n") {
\t\tline = strings.TrimSpace(line)
\t\tif line == "" || strings.HasPrefix(line, "#") {
\t\t\tcontinue
\t\t}
\t\tparts := strings.SplitN(line, "=", 2)
\t\tif len(parts) != 2 {
\t\t\tcontinue
\t\t}
\t\tif strings.TrimSpace(parts[0]) == key {
\t\t\treturn strings.TrimSpace(parts[1]), true
\t\t}
\t}
\treturn "", false
}

func SkewN() int {
\tv, ok := readKey("cycle_skew")
\tif !ok {
\t\treturn 0
\t}
\tn, err := strconv.Atoi(v)
\tif err != nil {
\t\treturn 0
\t}
\treturn n
}

func WalkN() bool {
\tv, ok := readKey("k_walk")
\tif !ok {
\t\treturn false
\t}
\treturn v == "true"
}

func StrideV() int {
\tv, ok := readKey("k_audit")
\tif !ok {
\t\treturn 1
\t}
\tn, err := strconv.Atoi(v)
\tif err != nil {
\t\treturn 1
\t}
\treturn n
}

func ZoneN() int {
\tv, ok := readKey("k_zone")
\tif !ok {
\t\treturn 0
\t}
\tn, err := strconv.Atoi(v)
\tif err != nil {
\t\treturn 0
\t}
\treturn n
}
"""

GO_FILES["internal/ingest/quarantinesnap/reader.go"] = """
package quarantinesnap

import (
\t"encoding/json"
\t"os"
\t"path/filepath"
)

type Doc struct {
\tVersion   int      `json:"version"`
\tHeldTrays []string `json:"held_trays"`
}

func Load(dir string) (Doc, error) {
\tb, err := os.ReadFile(filepath.Join(dir, "quarantine_snap.json"))
\tif err != nil {
\t\treturn Doc{}, err
\t}
\tvar d Doc
\treturn d, json.Unmarshal(b, &d)
}
"""

GO_FILES["anchor/window.go"] = """
package anchor

func span_ok(ts, start, end int) bool {
\treturn ts >= start && ts <= end
}
"""

GO_FILES["anchor/clockfold.go"] = """
package anchor

import "csp.local/reconcile/internal/cfg"

func edgeClamp(ts int) int {
\treturn ts
}

func skewAdd(ts int) int {
\treturn ts
}

func biasHigh(ts int) int {
\treturn ts
}

func biasLow(ts int) int {
\treturn ts
}

func fold_t(a int, b int, c int) int {
\t_ = b
\t_ = c
\treturn skewAdd(a) + cfg.SkewN()
}

func JoinP(ts, cycleStart, cycleEnd int) bool {
\tt := fold_t(ts, cycleStart, cycleEnd)
\treturn span_ok(t, cycleStart, cycleEnd)
}
"""

GO_FILES["propagate/table.go"] = """
package propagate

func classWeight(class string) float64 {
\tswitch class {
\tcase "CLASS_B":
\t\treturn 1.2
\tdefault:
\t\treturn 1.0
\t}
}
"""

GO_FILES["propagate/normcurve.go"] = """
package propagate

func curve_l(a float64, b int, class string) float64 {
\tif int(a) > b {
\t\treturn classWeight("CLASS_A")
\t}
\treturn 0.0
}

func signal_l(effectiveTS, caseStart int, class string) bool {
\treturn curve_l(float64(effectiveTS), caseStart, class) > 0
}
"""

GO_FILES["gate/permit.go"] = """
package gate

func Headroom(blocked, cleared int) int {
\treturn blocked - cleared
}

func ZoneSweep(active bool) bool {
\treturn active
}
"""

GO_FILES["gate/drainmux.go"] = """
package gate

func lane_h(blocked, extra float64) float64 {
\treturn blocked + extra
}

func twin_h(extra float64) float64 {
\treturn extra
}

func mux_h(a float64, b float64, c float64) (float64, float64) {
\t_ = c
\treturn lane_h(a, b), twin_h(b)
}

func mux_q(flag_a bool, flag_b bool) (bool, bool) {
\tblocked, _ := mux_h(0, 0, 0)
\t_ = blocked
\tif flag_a {
\t\treturn true, flag_b
\t}
\treturn flag_b, false
}
"""

GO_FILES["internal/core/wiresets.go"] = """
package core

import "csp.local/reconcile/internal/ingest/setcatalog"

func WireSets(sets []setcatalog.Row) map[string]string {
\t_ = sets
\treturn map[string]string{}
}
"""

GO_FILES["propagate/zonefold.go"] = """
package propagate

func normZone(z string) string {
\tif z == "" {
\t\treturn z
\t}
\treturn z + "_"
}
"""

GO_FILES["propagate/zonepick.go"] = """
package propagate

import "csp.local/reconcile/internal/ingest/lotnotice"

func FetchZ(lots []lotnotice.Row, zone string, caseStart int) (lotnotice.Row, bool) {
\tnz := normZone(zone)
\tfor _, l := range lots {
\t\tif l.ZoneID != nz {
\t\t\tcontinue
\t\t}
\t\tif signal_l(l.EffectiveTS, caseStart, l.RecallClass) {
\t\t\treturn l, true
\t\t}
\t}
\treturn lotnotice.Row{}, false
}
"""

GO_FILES["internal/broker/walkgate.go"] = """
package broker

import "csp.local/reconcile/internal/cfg"

func EnableWalk() bool {
\tif cfg.WalkN() {
\t\treturn false
\t}
\treturn true
}
"""

GO_FILES["internal/broker/relayhop.go"] = """
package broker

func HopRelay(active bool, depth int) bool {
\tif depth < 0 {
\t\treturn active
\t}
\treturn active && depth > 0
}
"""

GO_FILES["gate/holdpick.go"] = """
package gate

import (
\t"csp.local/reconcile/internal/ingest/lotnotice"
\t"csp.local/reconcile/propagate"
)

func ApplyQ(trayZone string, caseStart int, lots []lotnotice.Row, latchWide bool) bool {
\t_, flag_b := propagate.FetchZ(lots, trayZone, caseStart)
\tlatchA := latchWide && trayZone != ""
\thold, _ := mux_q(latchA, flag_b)
\treturn hold
}
"""

GO_FILES["internal/policy/relay.go"] = """
package policy

import (
\t"csp.local/reconcile/gate"
\t"csp.local/reconcile/internal/ingest/lotnotice"
)

func RelayQ(trayZone string, caseStart int, lots []lotnotice.Row, latchWide bool) bool {
\treturn gate.ApplyQ(trayZone, caseStart, lots, latchWide)
}
"""

GO_FILES["internal/core/linkgate.go"] = """
package core

import (
\t"csp.local/reconcile/internal/broker"
\t"csp.local/reconcile/internal/ingest/cycleboard"
\t"csp.local/reconcile/internal/ingest/lotnotice"
\t"csp.local/reconcile/internal/ingest/scanfeed"
)

func link_q(parent string, caseStart int, scans []scanfeed.Row, lots []lotnotice.Row, cycles []cycleboard.Row) bool {
\tif !broker.EnableWalk() {
\t\treturn false
\t}
\t_ = parent
\t_ = caseStart
\t_ = scans
\t_ = lots
\t_ = cycles
\treturn false
}
"""

GO_FILES["internal/core/rowgate.go"] = """
package core

import (
\t"csp.local/reconcile/internal/ingest/cycleboard"
\t"csp.local/reconcile/internal/ingest/lotnotice"
\t"csp.local/reconcile/internal/ingest/scanfeed"
\t"csp.local/reconcile/internal/policy"
)

func DecideQ(
\torowTray string,
\tcaseStart int,
\tzone string,
\thasScan bool,
\tscan scanfeed.Row,
\tscans []scanfeed.Row,
\tlots []lotnotice.Row,
\tcycles []cycleboard.Row,
\tchildOf map[string]string,
\tlatchWide bool,
\theldSnap map[string]struct{},
) (string, string) {
\tif _, snapHold := heldSnap[orowTray]; snapHold {
\t\treturn "HOLD", "SNAP_HOLD"
\t}
\tif parent, hasParent := childOf[orowTray]; hasParent && link_q(parent, caseStart, scans, lots, cycles) {
\t\treturn "HOLD", "LOT_RECALL"
\t}
\tif policy.RelayQ(zone, caseStart, lots, latchWide) {
\t\treturn "HOLD", "LOT_RECALL"
\t}
\tif hasScan && !sterileOK(scan, cycles) {
\t\treturn "HOLD", "STERILE_GAP"
\t}
\treturn "RELEASE", "CLEAR"
}
"""

GO_FILES["internal/core/stage.go"] = """
package core

import (
\t"csp.local/reconcile/anchor"
\t"csp.local/reconcile/internal/ingest/cycleboard"
\t"csp.local/reconcile/internal/ingest/scanfeed"
)

func latestScan(scans []scanfeed.Row, tray string, before int) (scanfeed.Row, bool) {
\tvar best scanfeed.Row
\tfound := false
\tfor _, s := range scans {
\t\tif s.TrayID != tray || s.EventCode != "OUTBOUND" {
\t\t\tcontinue
\t\t}
\t\tif s.TSEpoch > before {
\t\t\tcontinue
\t\t}
\t\tif !found || s.TSEpoch > best.TSEpoch {
\t\t\tbest = s
\t\t\tfound = true
\t\t}
\t}
\treturn best, found
}

func sterileOK(scan scanfeed.Row, cycles []cycleboard.Row) bool {
\tfor _, cy := range cycles {
\t\tif cy.ZoneID != scan.ZoneID {
\t\t\tcontinue
\t\t}
\t\tif anchor.JoinP(scan.TSEpoch, cy.CycleStart, cy.CycleEnd) {
\t\t\treturn true
\t\t}
\t}
\treturn false
}
"""

GO_FILES["internal/core/orchestrator.go"] = """
package core

import (
\t"path/filepath"

\t"csp.local/reconcile/internal/ingest/cycleboard"
\t"csp.local/reconcile/internal/ingest/lotnotice"
\t"csp.local/reconcile/internal/ingest/ormanifest"
\t"csp.local/reconcile/internal/ingest/quarantinesnap"
\t"csp.local/reconcile/internal/ingest/scanfeed"
\t"csp.local/reconcile/internal/ingest/setcatalog"
\t"csp.local/reconcile/propagate"
\tcsvio "csp.local/reconcile/internal/io"
\t"csp.local/reconcile/internal/model"
)

func ExecN(caseName, root string) error {
\tinDir := filepath.Join(root, "cases", caseName)
\toutDir := filepath.Join("/data/out", caseName)
\tscans, err := scanfeed.Load(inDir)
\tif err != nil {
\t\treturn err
\t}
\tcycles, err := cycleboard.Load(inDir)
\tif err != nil {
\t\treturn err
\t}
\tlots, err := lotnotice.Load(inDir)
\tif err != nil {
\t\treturn err
\t}
\torRows, err := ormanifest.Load(inDir)
\tif err != nil {
\t\treturn err
\t}
\tsets, err := setcatalog.Load(inDir)
\tif err != nil {
\t\treturn err
\t}
\tsnap, err := quarantinesnap.Load(inDir)
\tif err != nil {
\t\treturn err
\t}

\tchildOf := WireSets(sets)

\theldSnap := map[string]struct{}{}
\tfor _, t := range snap.HeldTrays {
\t\theldSnap[t] = struct{}{}
\t}

\tlatchWide := len(lots) > 0

\tvar ledger []model.LedgerRow
\tvar trays []model.TrayRow
\tseq := 1
\tblockedByLot := map[string]int{}
\tclearedByLot := map[string]int{}

\tfor _, orow := range orRows {
\t\tscan, hasScan := latestScan(scans, orow.TrayID, orow.CaseStartEpoch)
\t\tzone := ""
\t\tif hasScan {
\t\t\tzone = scan.ZoneID
\t\t}

\t\tstate, reason := DecideQ(
\t\t\torow.TrayID,
\t\t\torow.CaseStartEpoch,
\t\t\tzone,
\t\t\thasScan,
\t\t\tscan,
\t\t\tscans,
\t\t\tlots,
\t\t\tcycles,
\t\t\tchildOf,
\t\t\tlatchWide,
\t\t\theldSnap,
\t\t)

\t\tledger = append(ledger, model.LedgerRow{
\t\t\tTrayID:     orow.TrayID,
\t\t\tState:      state,
\t\t\tReasonCode: reason,
\t\t\tSourceCase: orow.CaseID,
\t\t\tSeq:        seq,
\t\t})
\t\ttrays = append(trays, model.TrayRow{
\t\t\tTrayID:     orow.TrayID,
\t\t\tState:      state,
\t\t\tReasonCode: reason,
\t\t\tSourceCase: orow.CaseID,
\t\t})
\t\tseq++

\t\tif lot, ok := propagate.FetchZ(lots, zone, orow.CaseStartEpoch); ok {
\t\t\tnote_q(blockedByLot, clearedByLot, lot.LotID, state)
\t\t}
\t}

\taudit := rollup_v(orRows, blockedByLot, clearedByLot, lots)

\tif err := csvio.WriteLedger(filepath.Join(outDir, "quarantine_ledger.jsonl"), ledger); err != nil {
\t\treturn err
\t}
\tif err := csvio.WriteDisposition(filepath.Join(outDir, "tray_disposition.json"), trays); err != nil {
\t\treturn err
\t}
\tif err := csvio.WriteAudit(filepath.Join(outDir, "recall_audit.tsv"), audit); err != nil {
\t\treturn err
\t}
\treturn nil
}
"""

GO_FILES["internal/core/tally.go"] = """
package core

func note_q(blocked, cleared map[string]int, lotID, state string) {
\tif state == "HOLD" {
\t\tblocked[lotID]++
\t} else {
\t\tcleared[lotID]++
\t}
}
"""

GO_FILES["internal/core/rollup.go"] = """
package core

import (
\t"csp.local/reconcile/internal/cfg"
\t"csp.local/reconcile/internal/ingest/lotnotice"
\t"csp.local/reconcile/internal/ingest/ormanifest"
\t"csp.local/reconcile/internal/model"
)

func rollup_v(orRows []ormanifest.Row, blocked, cleared map[string]int, lots []lotnotice.Row) []model.AuditRow {
\tvar out []model.AuditRow
\tstride := cfg.StrideV()
\tfor _, lot := range lots {
\t\tb := blocked[lot.LotID]
\t\tc := cleared[lot.LotID]
\t\tfor range orRows {
\t\t\tif b > 0 {
\t\t\t\tb += stride
\t\t\t}
\t\t}
\t\tout = append(out, model.AuditRow{
\t\t\tLotID:         lot.LotID,
\t\t\tTraysBlocked:  b,
\t\t\tTraysCleared:  c,
\t\t\tExposureClass: lot.RecallClass,
\t\t})
\t}
\treturn out
}
"""

GO_FILES["internal/decoy/rangefold.go"] = """
package decoy

import "fmt"

func FoldLabel(start, end int) string {
\treturn fmt.Sprintf("%d-%d", start+3, end-3)
}
"""

GO_FILES["internal/decoy/propagateproxy.go"] = """
package decoy

func ProxyScale(ts float64, class string) float64 {
\tif class == "ARCH" {
\t\treturn ts * 0.01
\t}
\treturn ts
}
"""

GO_FILES["anchor/biaschain.go"] = """
package anchor

func ChainHigh(ts int) int {
\treturn biasHigh(edgeClamp(ts))
}

func ChainLow(ts int) int {
\treturn biasLow(skewAdd(ts))
}
"""

GO_FILES["internal/decoy/muxshadow.go"] = """
package decoy

func ShadowMux(a, b bool) (bool, bool) {
\treturn a && b, a || b
}
"""

GO_FILES["propagate/curvepick.go"] = """
package propagate

func PickCurve(ts int, start int, class string) float64 {
\treturn curve_l(float64(ts), start, class)
}
"""

GO_FILES["internal/decoy/cycleproxy.go"] = """
package decoy

func ProxySpan(start, end int) int {
\treturn end - start + 7
}
"""

GO_FILES["internal/shadow/zonealias.go"] = """
package shadow

func AliasZone(z string, alias int) string {
\tif alias <= 0 {
\t\treturn z
\t}
\treturn z
}
"""

GO_FILES["internal/shadow/rollupproxy.go"] = """
package shadow

func ProxyRollup(n int, stride int) int {
\treturn n * stride
}
"""

GO_FILES["internal/shadow/walkstub.go"] = """
package shadow

func StubWalk(enabled bool) bool {
\treturn !enabled
}
"""

GO_FILES["internal/core/casectx.go"] = """
package core

import (
\t"csp.local/reconcile/internal/ingest/cycleboard"
\t"csp.local/reconcile/internal/ingest/lotnotice"
\t"csp.local/reconcile/internal/ingest/ormanifest"
\t"csp.local/reconcile/internal/ingest/quarantinesnap"
\t"csp.local/reconcile/internal/ingest/scanfeed"
\t"csp.local/reconcile/internal/ingest/setcatalog"
)

type CaseCtx struct {
\tCaseName string
\tRoot     string
\tScans    []scanfeed.Row
\tCycles   []cycleboard.Row
\tLots     []lotnotice.Row
\tORRows   []ormanifest.Row
\tSets     []setcatalog.Row
\tSnap     quarantinesnap.Doc
}
"""

DOCKERIGNORE = """\
.git
.gitignore
**/__pycache__/
**/*.pyc
**/.pytest_cache/
**/.mypy_cache/
**/.ruff_cache/
**/node_modules/
**/target/
**/dist/
**/build/
**/bin/
**/.venv/
**/venv/
.env
*.log
solution/
tests/
"""

DOCKERFILE = """
# syntax=docker/dockerfile:1

# Builder: compile the CSP binary.
FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY cmd ./cmd
COPY anchor ./anchor
COPY propagate ./propagate
COPY gate ./gate
COPY internal ./internal
RUN go build -trimpath -buildvcs=false -o /build/cspd ./cmd/cspd

# Runtime: canonical Go image (agent rebuild + verifier session tools).
FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        asciinema \\
        bash \\
        ca-certificates \\
        procps \\
        python3 \\
        python3-pip \\
        tmux \\
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \\
    pytest==8.4.1 \\
    pytest-json-ctrf==0.3.5

ENV TERM=xterm-256color \\
    GOPATH=/go \\
    GOCACHE=/tmp/go-cache
RUN mkdir -p /go /tmp/go-cache

COPY --from=builder /build/cspd /opt/csp/bin/cspd
COPY go.mod go.sum /opt/csp/
COPY cmd /opt/csp/cmd
COPY anchor /opt/csp/anchor
COPY propagate /opt/csp/propagate
COPY gate /opt/csp/gate
COPY internal /opt/csp/internal
COPY config /opt/csp/config
COPY --chmod=0755 scripts /opt/csp/scripts
RUN /opt/csp/scripts/build_fixtures.sh

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux kill-session -t _smoke

WORKDIR /opt/csp
"""

TEST_SH = """#!/bin/bash

# Verifier dependencies are installed in environment/Dockerfile.
# Add task-specific verifier-only Python packages there, not here.

mkdir -p /logs/verifier

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
    echo 0 > /logs/verifier/reward.txt
    exit 1
fi

python3 -m pytest -o cache_dir=/tmp/pytest_cache \\
  --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA

if [ $? -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
"""

TEST_OUTPUTS = '''
"""Verifier tests for hospital sterile tray recall reconciliation outcomes."""

import json
import subprocess
from pathlib import Path

ROOT = Path("/data/fixtures")
OUT = Path("/data/out")
RUN = ["/opt/csp/scripts/run-case.sh"]


def _run(case: str) -> None:
    out_dir = OUT / case
    if out_dir.exists():
        for p in out_dir.iterdir():
            p.unlink()
    subprocess.check_call(RUN + ["--case", case, "--root", str(ROOT)])


def _ledger(case: str) -> list[dict]:
    rows = []
    path = OUT / case / "quarantine_ledger.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _tray_state(case: str, tray: str) -> dict:
    for row in _ledger(case):
        if row["tray_id"] == tray:
            return row
    raise AssertionError(f"missing tray {tray} on {case}")


def _disposition(case: str) -> dict:
    return json.loads((OUT / case / "tray_disposition.json").read_text(encoding="utf-8"))


def _audit_rows(case: str) -> list[dict[str, str]]:
    lines = (OUT / case / "recall_audit.tsv").read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\\t")
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        if line.strip():
            rows.append(dict(zip(header, line.split("\\t"), strict=True)))
    return rows


def _lot_blocked(case: str, lot: str) -> int:
    for row in _audit_rows(case):
        if row["lot_id"] == lot:
            return int(row["trays_blocked"])
    raise AssertionError(f"missing lot {lot} on {case}")


def test_v01_post_notice_tray():
    """Recalled lot trays on post-notice cases enter HOLD with LOT_RECALL."""
    _run("case_c0412")
    row = _tray_state("case_c0412", "T-101")
    assert row["state"] == "HOLD"
    assert row["reason_code"] == "LOT_RECALL"


def test_v02_zone_clear_tray():
    """Trays from zones without active recall stay RELEASE."""
    _run("case_c0413")
    row = _tray_state("case_c0413", "T-200")
    assert row["state"] == "RELEASE"
    assert row["reason_code"] == "CLEAR"


def test_v03_cycle_window_tray():
    """Scans after cycle end produce STERILE_GAP holds."""
    _run("case_c0414")
    row = _tray_state("case_c0414", "T-300")
    assert row["state"] == "HOLD"
    assert row["reason_code"] == "STERILE_GAP"


def test_v04_split_set_tray():
    """Child trays inherit parent recall holds on split sets."""
    _run("case_c0415")
    row = _tray_state("case_c0415", "T-402")
    assert row["state"] == "HOLD"
    assert row["reason_code"] == "LOT_RECALL"


def test_v05_rerun_stable():
    """Repeated runs keep ledger and audit bytes stable."""
    _run("case_c0416")
    ledger_a = (OUT / "case_c0416" / "quarantine_ledger.jsonl").read_bytes()
    audit_a = (OUT / "case_c0416" / "recall_audit.tsv").read_bytes()
    _run("case_c0416")
    ledger_b = (OUT / "case_c0416" / "quarantine_ledger.jsonl").read_bytes()
    audit_b = (OUT / "case_c0416" / "recall_audit.tsv").read_bytes()
    assert ledger_a == ledger_b
    assert audit_a == audit_b


def test_v06_audit_blocked_count():
    """Recall audit blocked counts match held trays per lot without inflation."""
    _run("case_c0416")
    assert _lot_blocked("case_c0416", "L-R3") == 2


def test_v07_ledger_contract():
    """Ledger rows expose every field named in the output contract."""
    _run("case_c0412")
    row = _ledger("case_c0412")[0]
    for key in ("tray_id", "state", "reason_code", "source_case", "seq"):
        assert key in row


def test_v08_disposition_contract():
    """Disposition report exposes version and tray entries."""
    _run("case_c0412")
    doc = _disposition("case_c0412")
    assert doc["version"] == 1
    assert isinstance(doc["trays"], list)
    assert doc["trays"]


def test_v09_audit_contract():
    """Recall audit rows expose every column named in the output contract."""
    _run("case_c0412")
    header = (OUT / "case_c0412" / "recall_audit.tsv").read_text(encoding="utf-8").splitlines()[0].split("\\t")
    for key in ("lot_id", "trays_blocked", "trays_cleared", "exposure_class"):
        assert key in header
    for row in _audit_rows("case_c0412"):
        if row["lot_id"] == "L-R1":
            assert row["exposure_class"] == "CLASS_A"


def test_v10_dual_tray_case():
    """Dual-tray case holds both trays while audit clears stay zero."""
    _run("case_c0416")
    assert _tray_state("case_c0416", "T-501")["state"] == "HOLD"
    assert _tray_state("case_c0416", "T-502")["state"] == "HOLD"
    for row in _audit_rows("case_c0416"):
        if row["lot_id"] == "L-R3":
            assert int(row["trays_cleared"]) == 0


def test_v11_snap_hold_tray():
    """Snapshot-held trays stay on HOLD regardless of lot signals."""
    _run("case_c0417")
    row = _tray_state("case_c0417", "T-601")
    assert row["state"] == "HOLD"
    assert row["reason_code"] == "SNAP_HOLD"


def test_v12_notice_timing_tray():
    """Notices effective after case start must not block release."""
    _run("case_c0418")
    row = _tray_state("case_c0418", "T-701")
    assert row["state"] == "RELEASE"
    assert row["reason_code"] == "CLEAR"
'''

SOLVE_SH = r'''#!/usr/bin/env bash
set -euo pipefail

cd /opt/csp

cat > anchor/clockfold.go <<'EOF'
package anchor

func edgeClamp(ts int) int {
	return ts
}

func skewAdd(ts int) int {
	return ts
}

func biasHigh(ts int) int {
	return ts
}

func biasLow(ts int) int {
	return ts
}

func fold_t(a int, b int, c int) int {
	_ = b
	_ = c
	return a
}

func JoinP(ts, cycleStart, cycleEnd int) bool {
	t := fold_t(ts, cycleStart, cycleEnd)
	if t < cycleStart {
		return false
	}
	if t > cycleEnd {
		return false
	}
	return span_ok(t, cycleStart, cycleEnd)
}
EOF

cat > propagate/normcurve.go <<'EOF'
package propagate

func curve_l(a float64, b int, class string) float64 {
	if int(a) <= b {
		return classWeight(class)
	}
	return 0.0
}

func signal_l(effectiveTS, caseStart int, class string) bool {
	if effectiveTS > caseStart {
		return false
	}
	return curve_l(float64(effectiveTS), caseStart, class) > 0
}
EOF

cat > gate/drainmux.go <<'EOF'
package gate

func lane_h(blocked, extra float64) float64 {
	return blocked
}

func twin_h(extra float64) float64 {
	return extra
}

func mux_h(a float64, b float64, c float64) (float64, float64) {
	_ = c
	return a, b
}

func mux_q(flag_a bool, flag_b bool) (bool, bool) {
	_ = flag_a
	return flag_b, false
}
EOF

cat > gate/holdpick.go <<'EOF'
package gate

import (
	"csp.local/reconcile/internal/ingest/lotnotice"
	"csp.local/reconcile/propagate"
)

func ApplyQ(trayZone string, caseStart int, lots []lotnotice.Row, latchWide bool) bool {
	_, flag_b := propagate.FetchZ(lots, trayZone, caseStart)
	hold, _ := mux_q(false, flag_b)
	return hold
}
EOF

cat > internal/core/wiresets.go <<'EOF'
package core

import "csp.local/reconcile/internal/ingest/setcatalog"

func WireSets(sets []setcatalog.Row) map[string]string {
	childOf := map[string]string{}
	for _, s := range sets {
		childOf[s.ChildTray] = s.ParentTray
	}
	return childOf
}
EOF

cat > propagate/zonefold.go <<'EOF'
package propagate

func normZone(z string) string {
	return z
}
EOF

cat > internal/broker/walkgate.go <<'EOF'
package broker

import "csp.local/reconcile/internal/cfg"

func EnableWalk() bool {
	return cfg.WalkN()
}
EOF

cat > internal/core/linkgate.go <<'EOF'
package core

import (
	"csp.local/reconcile/internal/broker"
	"csp.local/reconcile/internal/ingest/cycleboard"
	"csp.local/reconcile/internal/ingest/lotnotice"
	"csp.local/reconcile/internal/ingest/scanfeed"
	"csp.local/reconcile/propagate"
)

func link_q(parent string, caseStart int, scans []scanfeed.Row, lots []lotnotice.Row, cycles []cycleboard.Row) bool {
	if !broker.EnableWalk() {
		return false
	}
	scan, ok := latestScan(scans, parent, caseStart)
	if !ok {
		return false
	}
	_, active := propagate.FetchZ(lots, scan.ZoneID, caseStart)
	return active
}
EOF

sed -i 's/readKey("cycle_skew")/readKey("k_skew")/' internal/cfg/load.go
sed -i '/latchWide := len(lots) > 0/d' internal/core/orchestrator.go
sed -i 's/\tlatchWide,/\tfalse,/' internal/core/orchestrator.go

cat > internal/core/rollup.go <<'EOF'
package core

import (
	"csp.local/reconcile/internal/ingest/lotnotice"
	"csp.local/reconcile/internal/ingest/ormanifest"
	"csp.local/reconcile/internal/model"
)

func rollup_v(orRows []ormanifest.Row, blocked, cleared map[string]int, lots []lotnotice.Row) []model.AuditRow {
	var out []model.AuditRow
	for _, lot := range lots {
		out = append(out, model.AuditRow{
			LotID:         lot.LotID,
			TraysBlocked:  blocked[lot.LotID],
			TraysCleared:  cleared[lot.LotID],
			ExposureClass: lot.RecallClass,
		})
	}
	return out
}
EOF

go build -o /opt/csp/bin/cspd ./cmd/cspd

for case in case_c0412 case_c0413 case_c0414 case_c0415 case_c0416 case_c0417 case_c0418; do
  /opt/csp/scripts/run-case.sh --case "$case" --root /data/fixtures
done
'''

CONSTRUCTION_MANIFEST = """{
  "symbol_table": [
    {"path": "internal/cfg/load.go", "symbol": "SkewN", "kind": "function", "signature": "func SkewN() int", "purpose": "reads skew offset from site config"},
    {"path": "internal/cfg/load.go", "symbol": "StrideV", "kind": "function", "signature": "func StrideV() int", "purpose": "reads rollup stride from site config"},
    {"path": "anchor/clockfold.go", "symbol": "fold_t", "kind": "function", "signature": "func fold_t(a int, b int, c int) int", "purpose": "epoch fold before window join"},
    {"path": "anchor/clockfold.go", "symbol": "JoinP", "kind": "function", "signature": "func JoinP(ts, cycleStart, cycleEnd int) bool", "purpose": "membership in cycle window"},
    {"path": "propagate/normcurve.go", "symbol": "curve_l", "kind": "function", "signature": "func curve_l(a float64, b int, class string) float64", "purpose": "notice weight curve"},
    {"path": "propagate/normcurve.go", "symbol": "signal_l", "kind": "function", "signature": "func signal_l(effectiveTS, caseStart int, class string) bool", "purpose": "notice active gate"},
    {"path": "propagate/zonefold.go", "symbol": "normZone", "kind": "function", "signature": "func normZone(z string) string", "purpose": "zone id normalization"},
    {"path": "gate/drainmux.go", "symbol": "mux_h", "kind": "function", "signature": "func mux_h(a float64, b float64, c float64) (float64, float64)", "purpose": "lane pressure split"},
    {"path": "gate/drainmux.go", "symbol": "mux_q", "kind": "function", "signature": "func mux_q(flag_a bool, flag_b bool) (bool, bool)", "purpose": "twin-lane mux entry"},
    {"path": "gate/holdpick.go", "symbol": "ApplyQ", "kind": "function", "signature": "func ApplyQ(trayZone string, caseStart int, lots []lotnotice.Row, latchWide bool) bool", "purpose": "zone hold pick"},
    {"path": "internal/broker/walkgate.go", "symbol": "EnableWalk", "kind": "function", "signature": "func EnableWalk() bool", "purpose": "set-walk feature gate"},
    {"path": "internal/core/wiresets.go", "symbol": "WireSets", "kind": "function", "signature": "func WireSets(sets []setcatalog.Row) map[string]string", "purpose": "parent-child wiring table"},
    {"path": "internal/core/linkgate.go", "symbol": "link_q", "kind": "function", "signature": "func link_q(parent string, caseStart int, scans []scanfeed.Row, lots []lotnotice.Row, cycles []cycleboard.Row) bool", "purpose": "parent edge walk"},
    {"path": "internal/core/rollup.go", "symbol": "rollup_v", "kind": "function", "signature": "func rollup_v(orRows []ormanifest.Row, blocked, cleared map[string]int, lots []lotnotice.Row) []model.AuditRow", "purpose": "per-lot audit rollup"}
  ],
  "flipping_point_contract": {
    "locations": [
      {"id": "G", "path": "internal/cfg/load.go", "controls_tests": ["test_v03_cycle_window_tray"]},
      {"id": "A", "path": "anchor/clockfold.go", "controls_tests": ["test_v03_cycle_window_tray"]},
      {"id": "B", "path": "propagate/normcurve.go", "controls_tests": ["test_v01_post_notice_tray", "test_v12_notice_timing_tray"]},
      {"id": "H", "path": "propagate/zonefold.go", "controls_tests": ["test_v01_post_notice_tray", "test_v02_zone_clear_tray", "test_v10_dual_tray_case"]},
      {"id": "I", "path": "internal/broker/walkgate.go", "controls_tests": ["test_v04_split_set_tray"]},
      {"id": "F", "path": "internal/core/linkgate.go", "controls_tests": ["test_v04_split_set_tray"]},
      {"id": "E", "path": "internal/core/wiresets.go", "controls_tests": ["test_v04_split_set_tray"]},
      {"id": "C", "path": "gate/drainmux.go", "controls_tests": ["test_v02_zone_clear_tray", "test_v10_dual_tray_case"]},
      {"id": "D", "path": "internal/core/rollup.go", "controls_tests": ["test_v06_audit_blocked_count", "test_v05_rerun_stable"]}
    ],
    "no_single_location_flips_majority": true,
    "concentration_cap": 0.5
  },
  "decoy_manifest": [
    {"path": "internal/decoy/rangefold.go", "kind": "helper", "rhymes_with": "fold_t", "non_fix_purpose": "display span labels"},
    {"path": "internal/decoy/propagateproxy.go", "kind": "helper", "rhymes_with": "curve_l", "non_fix_purpose": "archived proxy table"},
    {"path": "internal/decoy/muxshadow.go", "kind": "helper", "rhymes_with": "mux_q", "non_fix_purpose": "shadow mux for dashboards"},
    {"path": "propagate/curvepick.go", "kind": "helper", "rhymes_with": "curve_l", "non_fix_purpose": "unused curve picker"},
    {"path": "anchor/biaschain.go", "kind": "helper", "rhymes_with": "fold_t", "non_fix_purpose": "bias chain for reports"},
    {"path": "internal/shadow/zonealias.go", "kind": "helper", "rhymes_with": "normZone", "non_fix_purpose": "zone alias table"},
    {"path": "internal/shadow/rollupproxy.go", "kind": "helper", "rhymes_with": "rollup_v", "non_fix_purpose": "dashboard rollup proxy"},
    {"path": "internal/shadow/walkstub.go", "kind": "helper", "rhymes_with": "EnableWalk", "non_fix_purpose": "walk stub for reports"}
  ],
  "code_forbidden_tokens": [
    "central", "sterile", "processing", "batch", "scripts", "case", "root", "fixtures",
    "tray", "scan", "feeds", "autoclave", "cycle", "boards", "implant", "lot", "notices",
    "operating", "room", "manifests", "quarantine", "snapshots", "ledger", "disposition",
    "recall", "audit", "workflow", "update", "trays", "recalled", "lots", "releasable",
    "cases", "notice", "timestamp", "clean", "unaffected", "blocked", "events", "cleared",
    "completed", "load", "closed", "child", "parent", "split", "set", "reruns", "inflate",
    "counts", "rebuild", "unchanged", "names", "state", "reason", "source", "seq", "version",
    "exposure", "class", "hold", "release", "clear", "gap", "signoff", "deploy", "qa",
    "production", "project", "signoff", "untouched"
  ]
}
"""


def main() -> None:
    stale = ROOT / "environment" / "internal" / "core" / "rankgate.go"
    if stale.exists():
        stale.unlink()
    w("instruction.md", INSTRUCTION)
    w("task.toml", TASK_TOML)
    w("output_contract.toml", OUTPUT_CONTRACT)
    w("environment/.dockerignore", DOCKERIGNORE)
    w("environment/go.mod", GO_MOD)
    w("environment/go.sum", "")
    w("environment/config/site.toml", SITE_TOML)
    w("environment/config/disposition_policy.toml", DISPOSITION_POLICY)
    w("environment/cmd/cspd/main.go", MAIN_GO)
    w("environment/scripts/run-case.sh", RUN_CASE)
    w("environment/scripts/build_fixtures.sh", BUILD_FIXTURES)
    for rel, body in GO_FILES.items():
        w(f"environment/{rel}", body)
    w("environment/Dockerfile", DOCKERFILE)
    w("tests/test.sh", TEST_SH)
    w("tests/test_outputs.py", TEST_OUTPUTS)
    w("solution/solve.sh", SOLVE_SH)
    w("construction_manifest.json", CONSTRUCTION_MANIFEST)
    for script in (
        "environment/scripts/run-case.sh",
        "environment/scripts/build_fixtures.sh",
        "solution/solve.sh",
        "tests/test.sh",
    ):
        (ROOT / script).chmod(0o755)
    print(f"Generated task at {ROOT}")


if __name__ == "__main__":
    main()
