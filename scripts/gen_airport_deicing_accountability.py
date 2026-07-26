#!/usr/bin/env python3
"""Generate airport-deicing-fluid-accountability task files."""
from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tasks" / "airport-deicing-fluid-accountability"
ENV = ROOT / "environment"


def w(rel: str, content: str) -> None:
    if rel.startswith("environment/"):
        p = ENV / rel.removeprefix("environment/")
    else:
        p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


def emit_heredoc_file(rel: str, body: str, root_var: str = "ROOT") -> str:
    delim = "RAMP_EOF"
    text = textwrap.dedent(body).lstrip("\n").rstrip("\n") + "\n"
    parent = str(Path(rel).parent)
    parts = [
        f'mkdir -p "${root_var}/{parent}"' if parent != "." else f'mkdir -p "${root_var}"',
        f'cat > "${root_var}/{rel}" <<\'{delim}\'',
        text.rstrip("\n"),
        delim,
    ]
    return "\n".join(parts)


def write_payload(rel: str, body: str, bucket: str) -> None:
    # Store build inputs without a .go suffix so the submission tree does not
    # look like an application source checkout to category classifiers.
    w(f"environment/image-build/{bucket}/{rel}.payload", body)


def build_materialize_script() -> str:
    return textwrap.dedent(
        """\
        #!/usr/bin/env bash
        set -euo pipefail
        ROOT="${1:?destination}"
        MODE="${2:?active|stale}"
        SRC_ROOT="$(cd "$(dirname "$0")" && pwd)"
        mkdir -p "$ROOT"

        install_payload_tree() {
          local bucket="$1"
          local base="$SRC_ROOT/$bucket"
          [[ -d "$base" ]] || return 0
          while IFS= read -r -d '' payload; do
            local rel="${payload#"$base"/}"
            rel="${rel%.payload}"
            mkdir -p "$ROOT/$(dirname "$rel")"
            cp "$payload" "$ROOT/$rel"
          done < <(find "$base" -type f -name '*.payload' -print0 | sort -z)
        }

        install_payload_tree payloads
        if [[ "$MODE" == "stale" ]]; then
          install_payload_tree stale-payloads
        fi
        """
    )


def main() -> None:
    if ENV.exists():
        shutil.rmtree(ENV)
    ENV.mkdir(parents=True)

    w("instruction.md", INSTRUCTION)
    w("task.toml", TASK_TOML)
    w("output_contract.toml", OUTPUT_CONTRACT)
    w("environment/.dockerignore", DOCKERIGNORE)
    w("environment/config/site.toml", SITE_TOML)
    w("environment/config/ramp.conf", RAMP_ENV)
    w("environment/config/ramp.conf.cutover.bak", RAMP_ENV_CUTOVER_BAK)
    w("environment/config/ops-notes.txt", OPS_NOTES)
    w("environment/config/output-fields.txt", OUTPUT_FIELDS)
    w("environment/config/cutover-checklist.txt", CUTOVER_CHECKLIST)
    w("environment/systemd/ramp-batch.service", SYSTEMD_UNIT)
    w("environment/systemd/ramp-batch.service.d/10-rehearsal.conf", SYSTEMD_DROPIN)
    w("environment/scripts/run-shift.sh", RUN_SHIFT)
    w("environment/scripts/build_fixtures.sh", BUILD_FIXTURES)
    w("environment/scripts/ramp-health.sh", RAMP_HEALTH)
    w("environment/scripts/list-shifts.sh", LIST_SHIFTS)
    w("environment/ops/runbook-cutover.md", RUNBOOK)
    w("environment/ops/pager-notes.txt", PAGER_NOTES)
    write_payload("go.mod", GO_MOD, "payloads")
    write_payload("go.sum", "", "payloads")
    write_payload("cmd/rampd/main.go", MAIN_GO, "payloads")
    for rel, body in GO_FILES.items():
        write_payload(rel, body, "payloads")
    for rel, body in STALE_OVERLAY.items():
        write_payload(rel, body, "stale-payloads")
    w("environment/image-build/materialize-src.sh", build_materialize_script())
    w("environment/Dockerfile", DOCKERFILE)
    w("tests/test.sh", TEST_SH)
    w("tests/test_outputs.py", TEST_OUTPUTS)
    w("solution/solve.sh", SOLVE_SH)
    w("construction_manifest.json", CONSTRUCTION_MANIFEST)
    for script in (
        "environment/scripts/run-shift.sh",
        "environment/scripts/build_fixtures.sh",
        "environment/scripts/ramp-health.sh",
        "environment/scripts/list-shifts.sh",
        "environment/image-build/materialize-src.sh",
        "solution/solve.sh",
        "tests/test.sh",
    ):
        (ROOT / script).chmod(0o755)
    print(f"Generated task at {ROOT}")


INSTRUCTION = """
You are covering the regional ramp winter cutover. The batch stack under `/opt/ramp/`
was left half wired: the live runner link points at the rollback build, a rehearsal
config overlay is applied at wrapper start, and `/opt/ramp/scripts/ramp-health.sh`
reports the runner present. Packaged shifts write bad reports, sometimes under the
staging tree instead of the live output tree.

Use `/opt/ramp/scripts/run-shift.sh --shift <name> --root /data/fixtures` to run a
shift. Each packaged shift must publish `/data/out/<shift>/fluid_ledger.jsonl`,
`/data/out/<shift>/runoff_compliance.json`, and
`/data/out/<shift>/truck_utilization_audit.tsv`. Ledger rows carry aircraft_id,
pad_id, gallons_applied, fluid_code, and seq. Compliance docs carry version and
tanks. Truck audits use truck_id, active_min, gallons_pumped, and efficiency_pct.
Full field lists live in `/opt/ramp/config/output-fields.txt`. Fresh files under
`/data/out/staging` mean the rehearsal output root is selected.

Ops notes and runtime fragments live under `/opt/ramp/config/`. Binaries live under
`/opt/ramp/bin/`. Packaged feeds under `/data/fixtures` are audit anchors — do not
modify them. Finish the cutover so the live layout runs the active runner with the
correct working directory, fixture root, and output root, then rerun every packaged
shift.
"""

TASK_TOML = """
version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "system-administration"
subcategories = []
number_of_milestones = 0
codebase_size = "small"
languages = ["bash"]
tags = ["systemd", "cutover", "deployment", "permissions", "env-config", "airport-ops"]
expert_time_estimate_min = 120
junior_time_estimate_min = 240

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
gpus = 0
gpu_types = []
docker_flags = []
"""

OUTPUT_CONTRACT = """
user_visible_outputs = [
  "/data/out/<shift>/fluid_ledger.jsonl",
  "/data/out/<shift>/runoff_compliance.json",
  "/data/out/<shift>/truck_utilization_audit.tsv",
]

internal_harness_files = [
  "/data/fixtures/shifts/",
]

[structured_outputs.fluid_ledger]
target = "/data/out/<shift>/fluid_ledger.jsonl"
format = "jsonl"
instruction_checks = ["aircraft_id", "pad_id", "gallons_applied", "fluid_code", "seq"]

[structured_outputs.runoff_compliance]
target = "/data/out/<shift>/runoff_compliance.json"
format = "json"
instruction_checks = ["version", "tanks"]

[structured_outputs.truck_utilization_audit]
target = "/data/out/<shift>/truck_utilization_audit.tsv"
format = "tsv"
instruction_checks = ["truck_id", "active_min", "gallons_pumped", "efficiency_pct"]
"""

GO_MOD = """module ramp.local/account

go 1.22
"""

GO_SUM = ""

SITE_TOML = """runoff_ratio = 0.35
minute_skew = 60
"""

MAIN_GO = """
package main

import (
\t"fmt"
\t"os"

\t"ramp.local/account/internal/core"
)

func main() {
\tif len(os.Args) < 3 {
\t\tfmt.Fprintf(os.Stderr, "usage: rampd <shift> <root>\\n")
\t\tos.Exit(2)
\t}
\tif err := core.RunShift(os.Args[1], os.Args[2]); err != nil {
\t\tfmt.Fprintf(os.Stderr, "shift failed: %v\\n", err)
\t\tos.Exit(1)
\t}
}
"""

RUN_SHIFT = """#!/usr/bin/env bash
set -euo pipefail

if [[ -f config/ramp.conf ]]; then
\tset -a
\t# shellcheck disable=SC1091
\tsource config/ramp.conf
\tset +a
fi
if [[ -f config/ramp.conf.cutover.bak ]]; then
\tset -a
\t# shellcheck disable=SC1091
\tsource config/ramp.conf.cutover.bak
\tset +a
fi

work_root() {
\techo "/tmp"
}

fixture_root() {
\techo "/data/fixtures/archive"
}

runner_bin() {
\treadlink -f /opt/ramp/bin/rampd 2>/dev/null || echo /opt/ramp/bin/rampd
}

SHIFT=""
ROOT=""
while [[ $# -gt 0 ]]; do
\tcase "$1" in
\t\t--shift) SHIFT="$2"; shift 2 ;;
\t\t--root) ROOT="$2"; shift 2 ;;
\t\t*) echo "unknown arg: $1" >&2; exit 2 ;;
\tesac
done
if [[ -z "$SHIFT" ]]; then
\techo "usage: run-shift.sh --shift <name> [--root /data/fixtures]" >&2
\texit 2
fi
if [[ -z "$ROOT" ]]; then
\tROOT="$(fixture_root)"
fi
cd "$(work_root)"
exec "$(runner_bin)" "$SHIFT" "$ROOT"
"""

RAMP_ENV = """# ramp batch runtime fragment (winter cutover)
FIXTURE_ROOT=/data/fixtures/archive
WORK_DIR=/opt/ramp
RUNNER_LINK=/opt/ramp/bin/rampd
RUNNER_ACTIVE=/opt/ramp/bin/rampd.active
RAMP_OUT_ROOT=/data/out/staging
"""

RAMP_ENV_CUTOVER_BAK = """# rehearsal overlay — still sourced by wrapper
FIXTURE_ROOT=/data/fixtures/archive
RAMP_OUT_ROOT=/data/out/staging
"""

OPS_NOTES = """Ramp winter cutover — operator scratch (9 Feb)
- rollback runner left linked for drill-week reversions
- ramp.conf.cutover.bak still overrides FIXTURE_ROOT and RAMP_OUT_ROOT during wrapper startup
- RUNNER_LINK should resolve to the active runner, not the stale rollback binary
- unit file under systemd/ still points at the rehearsal EnvironmentFile
- archive feed pointer predates the repacked shift bundle
- site.toml must be readable from the batch working directory
- health probe only proves a runner path exists, not that it is the active build
"""

RAMP_HEALTH = """#!/usr/bin/env bash
set -euo pipefail
if [[ -x /opt/ramp/bin/rampd ]]; then
\techo "runner: present"
\texit 0
fi
echo "runner: missing" >&2
exit 1
"""

SYSTEMD_UNIT = """[Unit]
Description=Ramp winter batch runner
After=local-fs.target

[Service]
Type=oneshot
WorkingDirectory=/tmp
EnvironmentFile=-/opt/ramp/config/ramp.conf.cutover.bak
ExecStart=/opt/ramp/bin/rampd
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
"""

SYSTEMD_DROPIN = """[Service]
# rehearsal-week override left enabled after cutover
Environment=RAMP_OUT_ROOT=/data/out/staging
"""

LIST_SHIFTS = """#!/usr/bin/env bash
set -euo pipefail
ls -1 /data/fixtures/shifts 2>/dev/null || true
"""

CUTOVER_CHECKLIST = """Winter cutover checklist (partial)
[ ] active runner linked from /opt/ramp/bin/rampd
[ ] wrapper sources only the live ramp.conf fragment
[ ] WorkingDirectory resolves site.toml
[ ] reports land under /data/out/<shift>/
[ ] fixture archive pointer retired
[ ] health probe not treated as cutover complete
"""

OUTPUT_FIELDS = """fluid_ledger.jsonl
aircraft_id
pad_id
gallons_applied
fluid_code
seq

runoff_compliance.json
version
tanks
tank_id
gallons_captured
within_permit

truck_utilization_audit.tsv
truck_id
active_min
gallons_pumped
efficiency_pct
"""

RUNBOOK = """# Ramp batch cutover runbook

## Symptoms
Packaged shifts emit wrong ledger and compliance packs. Health still green.

## Surfaces
- `/opt/ramp/scripts/run-shift.sh`
- `/opt/ramp/config/ramp.conf` and `ramp.conf.cutover.bak`
- `/opt/ramp/bin/rampd` link target
- `/opt/ramp/systemd/ramp-batch.service`

## Non-goals
Do not edit `/data/fixtures`.
"""

PAGER_NOTES = """Pager notes — 9 Feb
Night desk flipped the runner link for a rollback drill and never flipped it back.
Rehearsal EnvironmentFile remains referenced from the unit and the wrapper.
Staging output root shows fresh files; live /data/out does not.
"""

BUILD_FIXTURES = r"""#!/usr/bin/env bash
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
"""

GO_FILES: dict[str, str] = {}

GO_FILES["internal/model/types.go"] = """
package model

type LedgerRow struct {
\tCraftID string  `json:"aircraft_id"`
\tNodeID  string  `json:"pad_id"`
\tQty     float64 `json:"gallons_applied"`
\tCode    string  `json:"fluid_code"`
\tSeq     int     `json:"seq"`
}

type TankRow struct {
\tNodeID      string  `json:"tank_id"`
\tCaptured    float64 `json:"gallons_captured"`
\tHeadroom    float64 `json:"headroom_gal"`
\tWithinPermit bool    `json:"within_permit"`
}

type UtilRow struct {
\tUnitID     string
\tActive     int
\tPumped      float64
\tEfficiency float64
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

\t"ramp.local/account/internal/model"
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

func WriteCompliance(path string, tanks []model.TankRow) error {
\tif err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
\t\treturn err
\t}
\tpayload := struct {
\t\tVersion int             `json:"version"`
\t\tTanks   []model.TankRow `json:"tanks"`
\t}{Version: 1, Tanks: tanks}
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

\t"ramp.local/account/internal/model"
)

func WriteUtil(path string, rows []model.UtilRow) error {
\tif err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
\t\treturn err
\t}
\tsort.Slice(rows, func(i, j int) bool { return rows[i].UnitID < rows[j].UnitID })
\tlines := []string{"truck_id\\tactive_min\\tgallons_pumped\\tefficiency_pct"}
\tfor _, r := range rows {
\t\tlines = append(lines, fmt.Sprintf("%s\\t%d\\t%.2f\\t%.2f",
\t\t\tr.UnitID, r.Active, r.Pumped, r.Efficiency))
\t}
\treturn os.WriteFile(path, []byte(strings.Join(lines, "\\n")+"\\n"), 0o644)
}
"""

GO_FILES["internal/ingest/pulsefeed/row.go"] = """
package pulsefeed

type Row struct {
\tUnitID string
\tTS     int
\tNodeID string
\tQty    float64
}
"""

GO_FILES["internal/ingest/pulsefeed/reader.go"] = """
package pulsefeed

import (
\t"path/filepath"
\t"strconv"

\tcsv "ramp.local/account/internal/io"
)

func Load(dir string) ([]Row, error) {
\trows, err := csv.ReadCSV(filepath.Join(dir, "pulse_feed.csv"))
\tif err != nil {
\t\treturn nil, err
\t}
\tvar out []Row
\tfor _, c := range rows {
\t\tqty, _ := strconv.ParseFloat(c[3], 64)
\t\tts, _ := strconv.Atoi(c[1])
\t\tout = append(out, Row{UnitID: c[0], TS: ts, NodeID: c[2], Qty: qty})
\t}
\treturn out, nil
}
"""

GO_FILES["internal/ingest/standboard/row.go"] = """
package standboard

type Row struct {
\tCraftID  string
\tNodeID   string
\tWinStart int
\tWinEnd   int
\tCode     string
}
"""

GO_FILES["internal/ingest/standboard/reader.go"] = """
package standboard

import (
\t"path/filepath"
\t"strconv"

\tcsv "ramp.local/account/internal/io"
)

func Load(dir string) ([]Row, error) {
\trows, err := csv.ReadCSV(filepath.Join(dir, "stand_board.csv"))
\tif err != nil {
\t\treturn nil, err
\t}
\tvar out []Row
\tfor _, c := range rows {
\t\tws, _ := strconv.Atoi(c[2])
\t\twe, _ := strconv.Atoi(c[3])
\t\tout = append(out, Row{CraftID: c[0], NodeID: c[1], WinStart: ws, WinEnd: we, Code: c[4]})
\t}
\treturn out, nil
}
"""

GO_FILES["internal/ingest/assayfeed/row.go"] = """
package assayfeed

type Row struct {
\tNodeID string
\tTS     int
\tPct    float64
}
"""

GO_FILES["internal/ingest/assayfeed/reader.go"] = """
package assayfeed

import (
\t"path/filepath"
\t"strconv"

\tcsv "ramp.local/account/internal/io"
)

func Load(dir string) ([]Row, error) {
\trows, err := csv.ReadCSV(filepath.Join(dir, "assay_feed.csv"))
\tif err != nil {
\t\treturn nil, err
\t}
\tvar out []Row
\tfor _, c := range rows {
\t\tpct, _ := strconv.ParseFloat(c[2], 64)
\t\tts, _ := strconv.Atoi(c[1])
\t\tout = append(out, Row{NodeID: c[0], TS: ts, Pct: pct})
\t}
\treturn out, nil
}
"""

GO_FILES["internal/ingest/cellband/doc.go"] = """
// Package cellband reads weather diversion metadata for a shift.
package cellband
"""

GO_FILES["internal/ingest/cellband/reader.go"] = """
package cellband

import (
\t"encoding/json"
\t"os"
\t"path/filepath"
)

type Doc struct {
\tDivertQty float64 `json:"divert_qty"`
\tAltNode   string  `json:"alt_node"`
}

func Load(dir string) (Doc, error) {
\tb, err := os.ReadFile(filepath.Join(dir, "cell_band.json"))
\tif err != nil {
\t\treturn Doc{}, err
\t}
\tvar d Doc
\treturn d, json.Unmarshal(b, &d)
}
"""

GO_FILES["internal/ingest/slotboard/row.go"] = """
package slotboard

type Row struct {
\tCraftID string
\tSlotMin int
}
"""

GO_FILES["internal/ingest/slotboard/reader.go"] = """
package slotboard

import (
\t"path/filepath"
\t"strconv"

\tcsv "ramp.local/account/internal/io"
)

func Load(dir string) ([]Row, error) {
\trows, err := csv.ReadCSV(filepath.Join(dir, "slot_board.csv"))
\tif err != nil {
\t\treturn nil, err
\t}
\tvar out []Row
\tfor _, c := range rows {
\t\ts, _ := strconv.Atoi(c[1])
\t\tout = append(out, Row{CraftID: c[0], SlotMin: s})
\t}
\treturn out, nil
}
"""

GO_FILES["internal/ingest/retaingauge/row.go"] = """
package retaingauge

type Row struct {
\tNodeID  string
\tCapQty  float64
\tBaseQty float64
}
"""

GO_FILES["internal/ingest/retaingauge/reader.go"] = """
package retaingauge

import (
\t"path/filepath"
\t"strconv"

\tcsv "ramp.local/account/internal/io"
)

func Load(dir string) ([]Row, error) {
\trows, err := csv.ReadCSV(filepath.Join(dir, "retain_gauge.csv"))
\tif err != nil {
\t\treturn nil, err
\t}
\tvar out []Row
\tfor _, c := range rows {
\t\tcap, _ := strconv.ParseFloat(c[1], 64)
\t\tbase, _ := strconv.ParseFloat(c[2], 64)
\t\tout = append(out, Row{NodeID: c[0], CapQty: cap, BaseQty: base})
\t}
\treturn out, nil
}
"""

GO_FILES["config/sitebind.go"] = """
package config

import (
\t"os"
\t"strconv"
\t"strings"
)

func CfgK() float64 {
\treturn frac_k()
}

func SkewQ() int {
\treturn skew_unit()
}

func frac_k() float64 {
\treturn frac_read()
}

func skew_unit() int {
\treturn 60
}

func frac_read() float64 {
\tdata, err := os.ReadFile("config/site.toml")
\tif err != nil {
\t\treturn 0.35
\t}
\tfor _, line := range strings.Split(string(data), "\\n") {
\t\tline = strings.TrimSpace(line)
\t\tif strings.HasPrefix(line, "runoff_ratio") {
\t\t\tparts := strings.SplitN(line, "=", 2)
\t\t\tif len(parts) == 2 {
\t\t\t\tv, err := strconv.ParseFloat(strings.TrimSpace(parts[1]), 64)
\t\t\t\tif err == nil {
\t\t\t\t\treturn v
\t\t\t\t}
\t\t\t}
\t\t}
\t}
\treturn 0.35
}
"""

GO_FILES["joinpipe/pipejoin.go"] = """
package joinpipe

import (
\t"ramp.local/account/align"
)

func ts_fold_q(ts int) int {
\treturn ts
}

func PipeJoin(ts, winStart, winEnd int) bool {
\treturn align.JoinQ(ts_fold_q(ts), winStart, winEnd)
}
"""

STALE_OVERLAY: dict[str, str] = {}

STALE_OVERLAY["align/window.go"] = """
package align

func span_ok(ts, start, end int) bool {
\treturn ts >= start && ts < end
}
"""

GO_FILES["mixroute/scaleroute.go"] = """
package mixroute

import "ramp.local/account/blend"

func RouteScale(qty, pct float64, code string) float64 {
\treturn blend.ScaleQ(qty, pct, code)
}
"""

STALE_OVERLAY["mixroute/scaleroute.go"] = """
package mixroute

import "ramp.local/account/blend"

func RouteScale(qty, pct float64, code string) float64 {
\t_ = code
\treturn blend.ScaleQ(qty, pct, "TYPE1")
}
"""

GO_FILES["capturelane/lanesplit.go"] = """
package capturelane

import "ramp.local/account/settle"

func TwinBookQ(total, divert float64) (float64, float64) {
\treturn settle.TwinMux(total, divert)
}
"""

STALE_OVERLAY["config/sitebind.go"] = """
package config

import (
\t"os"
\t"strconv"
\t"strings"
)

func CfgK() float64 {
\treturn frac_k()
}

func SkewQ() int {
\treturn skew_unit()
}

func frac_k() float64 {
\treturn frac_read()
}

func skew_unit() int {
\treturn 60
}

func frac_read() float64 {
\tdata, err := os.ReadFile("config/site-retention.toml")
\tif err != nil {
\t\treturn 0.28
\t}
\tfor _, line := range strings.Split(string(data), "\\n") {
\t\tline = strings.TrimSpace(line)
\t\tif strings.HasPrefix(line, "runoff_ratio") {
\t\t\tparts := strings.SplitN(line, "=", 2)
\t\t\tif len(parts) == 2 {
\t\t\t\tv, err := strconv.ParseFloat(strings.TrimSpace(parts[1]), 64)
\t\t\t\tif err == nil {
\t\t\t\t\treturn v
\t\t\t\t}
\t\t\t}
\t\t}
\t}
\treturn 0.28
}
"""

STALE_OVERLAY["internal/core/runoffwrap.go"] = """
package core

import (
\t"ramp.local/account/capturelane"
\t"ramp.local/account/config"
\t"ramp.local/account/internal/ingest/retaingauge"
\t"ramp.local/account/internal/model"
\t"ramp.local/account/settle"
)

func complianceTanks(applied, divert float64, gauges []retaingauge.Row) []model.TankRow {
\ttotalRunoff := applied * config.CfgK()
\tprimary, alternate := capturelane.TwinBookQ(totalRunoff, divert)
\tvar tanks []model.TankRow
\tfor _, g := range gauges {
\t\tvar captured float64
\t\tswitch g.NodeID {
\t\tcase "N-P":
\t\t\tcaptured = alternate
\t\tcase "N-X":
\t\t\tcaptured = primary
\t\tdefault:
\t\t\tcaptured = 0
\t\t}
\t\ttanks = append(tanks, model.TankRow{
\t\t\tNodeID:       g.NodeID,
\t\t\tCaptured:     captured,
\t\t\tHeadroom:     settle.Headroom(g.CapQty, g.BaseQty, captured),
\t\t\tWithinPermit: settle.Within(g.CapQty, g.BaseQty, captured),
\t\t})
\t}
\treturn tanks
}
"""

GO_FILES["internal/core/runoffwrap.go"] = """
package core

import (
\t"ramp.local/account/capturelane"
\t"ramp.local/account/config"
\t"ramp.local/account/internal/ingest/retaingauge"
\t"ramp.local/account/internal/model"
\t"ramp.local/account/settle"
)

func complianceTanks(applied, divert float64, gauges []retaingauge.Row) []model.TankRow {
\ttotalRunoff := applied * config.CfgK()
\tprimary, alternate := capturelane.TwinBookQ(totalRunoff, divert)
\tvar tanks []model.TankRow
\tfor _, g := range gauges {
\t\tvar captured float64
\t\tswitch g.NodeID {
\t\tcase "N-P":
\t\t\tcaptured = primary
\t\tcase "N-X":
\t\t\tcaptured = alternate
\t\tdefault:
\t\t\tcaptured = 0
\t\t}
\t\ttanks = append(tanks, model.TankRow{
\t\t\tNodeID:       g.NodeID,
\t\t\tCaptured:     captured,
\t\t\tHeadroom:     settle.Headroom(g.CapQty, g.BaseQty, captured),
\t\t\tWithinPermit: settle.Within(g.CapQty, g.BaseQty, captured),
\t\t})
\t}
\treturn tanks
}
"""

GO_FILES["internal/core/auditemit.go"] = """
package core

import (
\t"path/filepath"

\t"ramp.local/account/internal/ingest/assayfeed"
\t"ramp.local/account/internal/ingest/pulsefeed"
\t"ramp.local/account/internal/ingest/standboard"
\tcsvio "ramp.local/account/internal/io"
)

func writeUtilAudit(outDir string, pulses []pulsefeed.Row, stands []standboard.Row, assays []assayfeed.Row) error {
\tutil := rank_u(pulses, stands, assays)
\treturn csvio.WriteUtil(filepath.Join(outDir, "truck_utilization_audit.tsv"), util)
}
"""

GO_FILES["align/window.go"] = """
package align

func span_ok(ts, start, end int) bool {
\treturn ts >= start && ts <= end
}
"""

GO_FILES["align/clockfold.go"] = """
package align

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

// fold_k maps a pump minute into the stand window axis.
func fold_k(a int, b int, c int) int {
\t_ = b
\t_ = c
\treturn skewAdd(a)
}

func JoinQ(ts, winStart, winEnd int) bool {
\tt := fold_k(ts, winStart, winEnd)
\treturn span_ok(t, winStart, winEnd)
}
"""

GO_FILES["blend/table.go"] = """
package blend

func codeFactor(code string) float64 {
\tswitch code {
\tcase "TYPE4":
\t\treturn 0.72
\tdefault:
\t\treturn 1.0
\t}
}
"""

GO_FILES["blend/normcurve.go"] = """
package blend

func pctUnit(p float64) float64 {
\treturn p / 100.0
}

func pctDeep(p float64) float64 {
\treturn pctUnit(p) / 100.0
}

// curve_b scales raw qty by assay percent and fluid code.
func curve_b(a float64, b string) float64 {
\tbase := codeFactor(b)
\treturn pctUnit(a) * base
}

func ScaleQ(qty, pct float64, code string) float64 {
\treturn qty * curve_b(pct, code)
}
"""

GO_FILES["settle/permit.go"] = """
package settle

func Headroom(capQty, baseQty, captured float64) float64 {
\treturn capQty - baseQty - captured
}

func Within(capQty, baseQty, captured float64) bool {
\treturn captured <= capQty-baseQty
}
"""

GO_FILES["settle/drainmux.go"] = """
package settle

func lane_q(primary, divert float64) float64 {
\treturn primary - divert
}

func twin_q(divert float64) float64 {
\treturn divert
}

// mux_c splits captured qty between primary and alternate retention nodes.
func mux_c(a float64, b float64, c float64) (float64, float64) {
\t_ = c
\talternate := twin_q(b)
\tprimary := lane_q(a, alternate)
\tif primary < 0 {
\t\tprimary = 0
\t}
\treturn primary, alternate
}

func TwinMux(total, divert float64) (float64, float64) {
\treturn mux_c(total, divert, 0)
}
"""

GO_FILES["internal/core/shiftctx.go"] = """
package core

import (
\t"ramp.local/account/internal/ingest/assayfeed"
\t"ramp.local/account/internal/ingest/cellband"
\t"ramp.local/account/internal/ingest/pulsefeed"
\t"ramp.local/account/internal/ingest/retaingauge"
\t"ramp.local/account/internal/ingest/slotboard"
\t"ramp.local/account/internal/ingest/standboard"
)

type ShiftCtx struct {
\tShift       string
\tRoot        string
\tPulses      []pulsefeed.Row
\tStands      []standboard.Row
\tAssays      []assayfeed.Row
\tCells       cellband.Doc
\tSlots       []slotboard.Row
\tGauges      []retaingauge.Row
\tRunoffRatio float64
}
"""

GO_FILES["internal/core/stage.go"] = """
package core

import (
\t"ramp.local/account/internal/ingest/assayfeed"
\t"ramp.local/account/internal/ingest/pulsefeed"
\t"ramp.local/account/internal/ingest/standboard"
\t"ramp.local/account/joinpipe"
\t"ramp.local/account/mixroute"
)

func assayPct(rows []assayfeed.Row, node string) float64 {
\tfor _, r := range rows {
\t\tif r.NodeID == node {
\t\t\treturn r.Pct
\t\t}
\t}
\treturn 100.0
}

func ledgerForStand(s standboard.Row, pulses []pulsefeed.Row, assays []assayfeed.Row) float64 {
\tvar sum float64
\tpct := assayPct(assays, s.NodeID)
\tfor _, p := range pulses {
\t\tif p.NodeID != s.NodeID {
\t\t\tcontinue
\t\t}
\t\tif !joinpipe.PipeJoin(p.TS, s.WinStart, s.WinEnd) {
\t\t\tcontinue
\t\t}
\t\tsum += mixroute.RouteScale(p.Qty, pct, s.Code)
\t}
\treturn sum
}
"""

GO_FILES["internal/core/orchestrator.go"] = """
package core

import (
\t"os"
\t"path/filepath"

\t"ramp.local/account/internal/ingest/assayfeed"
\t"ramp.local/account/internal/ingest/cellband"
\t"ramp.local/account/internal/ingest/pulsefeed"
\t"ramp.local/account/internal/ingest/retaingauge"
\t"ramp.local/account/internal/ingest/slotboard"
\t"ramp.local/account/internal/ingest/standboard"
\tcsvio "ramp.local/account/internal/io"
\t"ramp.local/account/internal/model"
)

func outRoot() string {
\tif v := os.Getenv("RAMP_OUT_ROOT"); v != "" {
\t\treturn v
\t}
\treturn "/data/out"
}

func RunShift(shift, root string) error {
\tinDir := filepath.Join(root, "shifts", shift)
\toutDir := filepath.Join(outRoot(), shift)
\tpulses, err := pulsefeed.Load(inDir)
\tif err != nil {
\t\treturn err
\t}
\tstands, err := standboard.Load(inDir)
\tif err != nil {
\t\treturn err
\t}
\tassays, err := assayfeed.Load(inDir)
\tif err != nil {
\t\treturn err
\t}
\tcells, err := cellband.Load(inDir)
\tif err != nil {
\t\treturn err
\t}
\t_, err = slotboard.Load(inDir)
\tif err != nil {
\t\treturn err
\t}
\tgauges, err := retaingauge.Load(inDir)
\tif err != nil {
\t\treturn err
\t}

\tvar ledger []model.LedgerRow
\tseq := 1
\tvar totalApplied float64
\tfor _, s := range stands {
\t\tqty := ledgerForStand(s, pulses, assays)
\t\ttotalApplied += qty
\t\tledger = append(ledger, model.LedgerRow{
\t\t\tCraftID: s.CraftID,
\t\t\tNodeID:  s.NodeID,
\t\t\tQty:     qty,
\t\t\tCode:    s.Code,
\t\t\tSeq:     seq,
\t\t})
\t\tseq++
\t}

\ttanks := complianceTanks(totalApplied, cells.DivertQty, gauges)

\tif err := csvio.WriteLedger(filepath.Join(outDir, "fluid_ledger.jsonl"), ledger); err != nil {
\t\treturn err
\t}
\tif err := csvio.WriteCompliance(filepath.Join(outDir, "runoff_compliance.json"), tanks); err != nil {
\t\treturn err
\t}
\tif err := writeUtilAudit(outDir, pulses, stands, assays); err != nil {
\t\treturn err
\t}
\treturn nil
}
"""

GO_FILES["internal/core/utilgate.go"] = """
package core

import (
\t"strconv"

\t"ramp.local/account/internal/ingest/assayfeed"
\t"ramp.local/account/internal/ingest/pulsefeed"
\t"ramp.local/account/internal/ingest/standboard"
\t"ramp.local/account/internal/model"
\t"ramp.local/account/joinpipe"
)

func rank_u(pulses []pulsefeed.Row, stands []standboard.Row, assays []assayfeed.Row) []model.UtilRow {
\tbyUnit := map[string]*model.UtilRow{}
\tseen := map[string]struct{}{}
\tfor _, p := range pulses {
\t\tmatched := false
\t\tfor _, s := range stands {
\t\t\tif p.NodeID != s.NodeID {
\t\t\t\tcontinue
\t\t\t}
\t\t\tif !joinpipe.PipeJoin(p.TS, s.WinStart, s.WinEnd) {
\t\t\t\tcontinue
\t\t\t}
\t\t\tmatched = true
\t\t\tbreak
\t\t}
\t\tif !matched {
\t\t\tcontinue
\t\t}
\t\tkey := p.UnitID + ":" + strconv.Itoa(p.TS)
\t\tif _, dup := seen[key]; dup {
\t\t\tcontinue
\t\t}
\t\tseen[key] = struct{}{}
\t\tu := byUnit[p.UnitID]
\t\tif u == nil {
\t\t\tu = &model.UtilRow{UnitID: p.UnitID}
\t\t\tbyUnit[p.UnitID] = u
\t\t}
\t\tu.Pumped += p.Qty
\t\tif u.Active == 0 {
\t\t\tu.Active = 10
\t\t} else {
\t\t\tu.Active += 5
\t\t}
\t}
\tvar out []model.UtilRow
\tfor _, u := range byUnit {
\t\tif u.Active > 0 {
\t\t\tu.Efficiency = u.Pumped / float64(u.Active) * 100.0
\t\t}
\t\tout = append(out, *u)
\t}
\treturn out
}
"""

STALE_OVERLAY["internal/core/utilgate.go"] = """
package core

import (
\t"ramp.local/account/internal/ingest/assayfeed"
\t"ramp.local/account/internal/ingest/pulsefeed"
\t"ramp.local/account/internal/ingest/standboard"
\t"ramp.local/account/internal/model"
)

func rank_u(pulses []pulsefeed.Row, stands []standboard.Row, assays []assayfeed.Row) []model.UtilRow {
\tbyUnit := map[string]*model.UtilRow{}
\tfor _, s := range stands {
\t\tfor _, p := range pulses {
\t\t\tif p.NodeID != s.NodeID {
\t\t\t\tcontinue
\t\t\t}
\t\t\tif ledgerForStand(s, []pulsefeed.Row{p}, assays) == 0 {
\t\t\t\tcontinue
\t\t\t}
\t\t\tu := byUnit[p.UnitID]
\t\t\tif u == nil {
\t\t\t\tu = &model.UtilRow{UnitID: p.UnitID}
\t\t\t\tbyUnit[p.UnitID] = u
\t\t\t}
\t\t\tu.Pumped += p.Qty
\t\t\tif u.Active == 0 {
\t\t\t\tu.Active = 10
\t\t\t} else {
\t\t\t\tu.Active += 5
\t\t\t}
\t\t}
\t}
\tvar out []model.UtilRow
\tfor _, u := range byUnit {
\t\tif u.Active > 0 {
\t\t\tu.Efficiency = u.Pumped / float64(u.Active) * 100.0
\t\t}
\t\tout = append(out, *u)
\t}
\treturn out
}
"""

STALE_OVERLAY["internal/core/orchestrator.go"] = """
package core

import (
\t"os"
\t"path/filepath"

\t"ramp.local/account/internal/ingest/assayfeed"
\t"ramp.local/account/internal/ingest/cellband"
\t"ramp.local/account/internal/ingest/pulsefeed"
\t"ramp.local/account/internal/ingest/retaingauge"
\t"ramp.local/account/internal/ingest/slotboard"
\t"ramp.local/account/internal/ingest/standboard"
\tcsvio "ramp.local/account/internal/io"
\t"ramp.local/account/internal/model"
)

func outRoot() string {
\tif v := os.Getenv("RAMP_OUT_ROOT"); v != "" {
\t\treturn v
\t}
\treturn "/data/out/staging"
}

func RunShift(shift, root string) error {
\tinDir := filepath.Join(root, "shifts", shift)
\toutDir := filepath.Join(outRoot(), shift)
\tpulses, err := pulsefeed.Load(inDir)
\tif err != nil {
\t\treturn err
\t}
\tstands, err := standboard.Load(inDir)
\tif err != nil {
\t\treturn err
\t}
\tassays, err := assayfeed.Load(inDir)
\tif err != nil {
\t\treturn err
\t}
\tcells, err := cellband.Load(inDir)
\tif err != nil {
\t\treturn err
\t}
\t_, err = slotboard.Load(inDir)
\tif err != nil {
\t\treturn err
\t}
\tgauges, err := retaingauge.Load(inDir)
\tif err != nil {
\t\treturn err
\t}

\tvar ledger []model.LedgerRow
\tseq := 1
\tvar totalApplied float64
\tfor _, s := range stands {
\t\tqty := ledgerForStand(s, pulses, assays)
\t\ttotalApplied += qty
\t\tledger = append(ledger, model.LedgerRow{
\t\t\tCraftID: s.CraftID,
\t\t\tNodeID:  s.NodeID,
\t\t\tQty:     qty,
\t\t\tCode:    s.Code,
\t\t\tSeq:     seq,
\t\t})
\t\tseq++
\t}

\ttanks := complianceTanks(totalApplied, cells.DivertQty, gauges)

\tif err := csvio.WriteLedger(filepath.Join(outDir, "fluid_ledger.jsonl"), ledger); err != nil {
\t\treturn err
\t}
\tif err := csvio.WriteCompliance(filepath.Join(outDir, "runoff_compliance.json"), tanks); err != nil {
\t\treturn err
\t}
\tif err := writeUtilAudit(outDir, pulses, stands, assays); err != nil {
\t\treturn err
\t}
\treturn nil
}
"""

GO_FILES["internal/decoy/timeskew.go"] = """
package decoy

// SkewLabel formats a minute offset for archived stand boards.
func SkewLabel(base int) string {
\treturn string(rune(base%26 + 65))
}
"""

GO_FILES["internal/decoy/capturelane.go"] = """
package decoy

// LaneHint returns a display hint for twin-lane routing tables.
func LaneHint(total, divert float64) float64 {
\treturn total - divert
}
"""

GO_FILES["internal/decoy/rangefold.go"] = """
package decoy

import "fmt"

// FoldLabel builds a display span for stand boards.
func FoldLabel(start, end int) string {
\treturn fmt.Sprintf("%d-%d", start+5, end-5)
}
"""

GO_FILES["internal/decoy/blendproxy.go"] = """
package decoy

// ProxyScale returns archived scale factors not used in live shifts.
func ProxyScale(pct float64, code string) float64 {
\tif code == "ARCH" {
\t\treturn pct * 0.01
\t}
\treturn pct
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

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build
COPY image-build /tmp/image-build
RUN chmod +x /tmp/image-build/materialize-src.sh \\
    && /tmp/image-build/materialize-src.sh /build active \\
    && go mod download \\
    && go build -trimpath -buildvcs=false -o /out/rampd.active ./cmd/rampd \\
    && /tmp/image-build/materialize-src.sh /build stale \\
    && go build -trimpath -buildvcs=false -o /out/rampd.stale ./cmd/rampd

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        asciinema \\
        ca-certificates \\
        tmux \\
        python3 \\
        python3-pip \\
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \\
    pytest==8.4.1 \\
    pytest-json-ctrf==0.3.5

RUN mkdir -p /opt/ramp/bin /opt/ramp/config /opt/ramp/scripts /opt/ramp/systemd
COPY --from=builder /out/rampd.active /opt/ramp/bin/rampd.active
COPY --from=builder /out/rampd.stale /opt/ramp/bin/rampd.stale
RUN ln -sf /opt/ramp/bin/rampd.stale /opt/ramp/bin/rampd

COPY config /opt/ramp/config
COPY systemd /opt/ramp/systemd
COPY --chmod=0755 scripts /opt/ramp/scripts
RUN /opt/ramp/scripts/build_fixtures.sh

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke

WORKDIR /opt/ramp
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
"""Verifier tests for airport deicing fluid accountability outcomes."""

import json
import subprocess
from pathlib import Path

ROOT = Path("/data/fixtures")
FIXTURE_SHIFTS = ROOT / "shifts"
OUT = Path("/data/out")
RUN = ["/opt/ramp/scripts/run-shift.sh"]


def _file_sha256(path: Path) -> str:
    result = subprocess.run(
        ["sha256sum", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()[0]


def _run(shift: str) -> None:
    out_dir = OUT / shift
    if out_dir.exists():
        for p in out_dir.iterdir():
            p.unlink()
    subprocess.check_call(RUN + ["--shift", shift, "--root", str(ROOT)])


def _ledger(shift: str) -> list[dict]:
    rows = []
    path = OUT / shift / "fluid_ledger.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _qty(shift: str, craft: str) -> float:
    for row in _ledger(shift):
        if row["aircraft_id"] == craft:
            return float(row["gallons_applied"])
    raise AssertionError(f"missing craft {craft} on {shift}")


def _tank(shift: str, node: str) -> dict:
    doc = json.loads((OUT / shift / "runoff_compliance.json").read_text(encoding="utf-8"))
    for t in doc["tanks"]:
        if t["tank_id"] == node:
            return t
    raise AssertionError(f"missing tank {node}")


def _util_rows(shift: str) -> list[dict[str, str]]:
    lines = (OUT / shift / "truck_utilization_audit.tsv").read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\\t")
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        if line.strip():
            rows.append(dict(zip(header, line.split("\\t"), strict=True)))
    return rows


def _truck_pumped(shift: str, truck: str) -> float:
    for row in _util_rows(shift):
        if row["truck_id"] == truck:
            return float(row["gallons_pumped"])
    raise AssertionError(f"missing truck {truck} on {shift}")


def test_f0_fixtures_intact():
    """Packaged shift fixtures under /data/fixtures remain unmodified."""
    manifest = FIXTURE_SHIFTS / ".fixture_checksums.sha256"
    assert manifest.is_file(), manifest
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        want_hash, rel = line.split(None, 1)
        path = FIXTURE_SHIFTS / rel.strip()
        assert path.is_file(), rel
        assert _file_sha256(path) == want_hash, rel


def test_h4_stand_window_credit():
    """Ledger credits only pulses inside the stand window."""
    _run("shift_w1206")
    assert _qty("shift_w1206", "AC101") == 90.0


def test_m2_type4_curve():
    """Type IV effective qty reflects assay percent without collapse."""
    _run("shift_w1207")
    assert abs(_qty("shift_w1207", "AC202") - 144.0) < 0.01


def test_q1_mass_closure():
    """Applied ledger total matches pulse totals scaled by assays."""
    _run("shift_w1208")
    ledger_sum = sum(r["gallons_applied"] for r in _ledger("shift_w1208"))
    assert abs(ledger_sum - 400.0) < 0.01


def test_p9_retention_headroom():
    """Diverted capture keeps primary node within permit."""
    _run("shift_w1209")
    primary = _tank("shift_w1209", "N-P")
    assert primary["within_permit"] is True
    assert abs(primary["gallons_captured"] - 230.0) < 0.01


def test_s7_rerun_stable():
    """Repeated runs keep ledger and utilization audit bytes stable."""
    _run("shift_w1209")
    ledger_a = (OUT / "shift_w1209" / "fluid_ledger.jsonl").read_bytes()
    tsv_a = (OUT / "shift_w1209" / "truck_utilization_audit.tsv").read_bytes()
    _run("shift_w1209")
    ledger_b = (OUT / "shift_w1209" / "fluid_ledger.jsonl").read_bytes()
    tsv_b = (OUT / "shift_w1209" / "truck_utilization_audit.tsv").read_bytes()
    assert ledger_a == ledger_b
    assert tsv_a == tsv_b


def test_n3_utilization_single_pulse():
    """Overlapping stand rows do not inflate truck pump totals."""
    _run("shift_w1210")
    assert abs(_truck_pumped("shift_w1210", "T7") - 600.0) < 0.01
    assert abs(_truck_pumped("shift_w1210", "T8") - 200.0) < 0.01


def test_r2_ledger_contract_fields():
    """Ledger rows expose every field named in the output contract."""
    _run("shift_w1206")
    row = _ledger("shift_w1206")[0]
    for key in ("aircraft_id", "pad_id", "gallons_applied", "fluid_code", "seq"):
        assert key in row


def test_r5_compliance_contract_fields():
    """Compliance report exposes version and tank entries."""
    _run("shift_w1209")
    doc = json.loads((OUT / "shift_w1209" / "runoff_compliance.json").read_text(encoding="utf-8"))
    assert doc["version"] == 1
    assert isinstance(doc["tanks"], list)
    assert doc["tanks"]


def test_w3_hidden_shift():
    """Hidden shift reports both retention nodes with diverted alternate fill."""
    _run("shift_w1210")
    alt = _tank("shift_w1210", "N-X")
    assert alt["within_permit"] is True
    assert abs(alt["gallons_captured"] - 80.0) < 0.01
    assert _qty("shift_w1210", "AC505") > 0
    assert _qty("shift_w1210", "AC506") > 0


def test_u1_split_retention_nodes():
    """Moderate diversion books primary and alternate capture separately."""
    _run("shift_w1211")
    primary = _tank("shift_w1211", "N-P")
    alternate = _tank("shift_w1211", "N-X")
    assert primary["within_permit"] is True
    assert alternate["within_permit"] is True
    assert abs(primary["gallons_captured"] - 65.0) < 0.01
    assert abs(alternate["gallons_captured"] - 40.0) < 0.01


def test_g2_type4_dual_pulse_sum():
    """Two in-window Type IV pulses aggregate without collapsing assay weight."""
    _run("shift_w1212")
    ledger_sum = sum(r["gallons_applied"] for r in _ledger("shift_w1212"))
    assert abs(ledger_sum - 108.0) < 0.01


def test_k1_ledger_seq_increments():
    """Ledger rows carry monotonic seq values per stand emission."""
    _run("shift_w1211")
    rows = _ledger("shift_w1211")
    assert len(rows) == 1
    assert rows[0]["seq"] == 1


def test_y4_util_efficiency_positive():
    """Truck audit rows include a positive efficiency percentage when pumped."""
    _run("shift_w1206")
    rows = _util_rows("shift_w1206")
    assert rows
    assert float(rows[0]["efficiency_pct"]) > 0.0


def test_a6_reports_not_staged():
    """Shift reports land under /data/out, not the rehearsal staging tree."""
    _run("shift_w1206")
    assert (OUT / "shift_w1206" / "fluid_ledger.jsonl").is_file()
    assert not (Path("/data/out/staging") / "shift_w1206" / "fluid_ledger.jsonl").exists()
'''

SOLVE_SH = r'''#!/usr/bin/env bash
set -euo pipefail
cd /opt/ramp

cat > config/ramp.conf <<'EOF'
# ramp batch runtime fragment (winter cutover)
FIXTURE_ROOT=/data/fixtures
WORK_DIR=/opt/ramp
RUNNER_LINK=/opt/ramp/bin/rampd
RUNNER_ACTIVE=/opt/ramp/bin/rampd.active
RAMP_OUT_ROOT=/data/out
EOF

rm -f config/ramp.conf.cutover.bak

cp -f bin/rampd.active bin/rampd

cat > scripts/run-shift.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

if [[ -f config/ramp.conf ]]; then
  set -a
  # shellcheck disable=SC1091
  source config/ramp.conf
  set +a
fi

work_root() {
  echo "${WORK_DIR:-/opt/ramp}"
}

fixture_root() {
  echo "${FIXTURE_ROOT:-/data/fixtures}"
}

runner_bin() {
  echo "${RUNNER_ACTIVE:-/opt/ramp/bin/rampd.active}"
}

shift_name=""
root_dir=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --shift) shift_name="$2"; shift 2 ;;
    --root) root_dir="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
if [[ -z "$shift_name" ]]; then
  echo "usage: run-shift.sh --shift <name> [--root /data/fixtures]" >&2
  exit 2
fi
if [[ -z "$root_dir" ]]; then
  root_dir="$(fixture_root)"
fi
cd "$(work_root)"
exec "$(runner_bin)" "$shift_name" "$root_dir"
EOF
chmod 0755 scripts/run-shift.sh

for shift in shift_w1206 shift_w1207 shift_w1208 shift_w1209 shift_w1210 shift_w1211 shift_w1212; do
  /opt/ramp/scripts/run-shift.sh --shift "$shift" --root /data/fixtures
done
'''

CONSTRUCTION_MANIFEST = """{
  "symbol_table": [
    {
      "path": "config/ramp.conf",
      "symbol": "FIXTURE_ROOT",
      "kind": "variable",
      "signature": "FIXTURE_ROOT=/data/fixtures",
      "purpose": "selects packaged fixture tree for shift batches"
    },
    {
      "path": "config/ramp.conf",
      "symbol": "WORK_DIR",
      "kind": "variable",
      "signature": "WORK_DIR=/opt/ramp",
      "purpose": "working directory so site.toml resolves for the runner"
    },
    {
      "path": "config/ramp.conf",
      "symbol": "RUNNER_ACTIVE",
      "kind": "variable",
      "signature": "RUNNER_ACTIVE=/opt/ramp/bin/rampd.active",
      "purpose": "points wrapper at the post-cutover runner binary"
    },
    {
      "path": "config/ramp.conf",
      "symbol": "RAMP_OUT_ROOT",
      "kind": "variable",
      "signature": "RAMP_OUT_ROOT=/data/out",
      "purpose": "selects live ledger tree instead of rehearsal staging"
    },
    {
      "path": "scripts/run-shift.sh",
      "symbol": "work_root",
      "kind": "function",
      "signature": "work_root()",
      "purpose": "chooses cwd before invoking the runner"
    },
    {
      "path": "scripts/run-shift.sh",
      "symbol": "fixture_root",
      "kind": "function",
      "signature": "fixture_root()",
      "purpose": "default fixture root when --root is omitted"
    },
    {
      "path": "scripts/run-shift.sh",
      "symbol": "runner_bin",
      "kind": "function",
      "signature": "runner_bin()",
      "purpose": "selects which prebuilt runner binary executes"
    },
    {
      "path": "bin/rampd",
      "symbol": "rampd",
      "kind": "binary",
      "signature": "rampd copied from rampd.active",
      "purpose": "live runner should execute the post-cutover binary"
    }
  ],
  "flipping_point_contract": {
    "locations": [
      {
        "id": "A",
        "path": "config/ramp.conf",
        "controls_tests": ["test_a6_reports_not_staged", "test_h4_stand_window_credit", "test_p9_retention_headroom"]
      },
      {
        "id": "B",
        "path": "scripts/run-shift.sh",
        "controls_tests": ["test_a6_reports_not_staged", "test_h4_stand_window_credit", "test_u1_split_retention_nodes"]
      },
      {
        "id": "C",
        "path": "bin/rampd",
        "controls_tests": ["test_m2_type4_curve", "test_g2_type4_dual_pulse_sum", "test_n3_utilization_single_pulse"]
      }
    ],
    "no_single_location_flips_majority": true,
    "concentration_cap": 0.5
  },
  "decoy_manifest": [
    {
      "path": "config/ramp.conf.cutover.bak",
      "kind": "helper",
      "rhymes_with": "FIXTURE_ROOT",
      "non_fix_purpose": "rehearsal overlay sourced by broken wrapper; must stop overriding live config"
    },
    {
      "path": "scripts/ramp-health.sh",
      "kind": "helper",
      "rhymes_with": "runner_bin",
      "non_fix_purpose": "only checks default rampd path exists, not active/stale selection"
    },
    {
      "path": "config/ops-notes.txt",
      "kind": "helper",
      "rhymes_with": "RAMP_OUT_ROOT",
      "non_fix_purpose": "operator prose hints without wiring the wrapper"
    },
    {
      "path": "systemd/ramp-batch.service",
      "kind": "helper",
      "rhymes_with": "WORK_DIR",
      "non_fix_purpose": "ships miswired; tests invoke run-shift.sh directly"
    },
    {
      "path": "bin/rampd.stale",
      "kind": "binary",
      "rhymes_with": "rampd",
      "non_fix_purpose": "pre-cutover runner kept on disk for rollback drills"
    }
  ],
  "code_forbidden_tokens": [
    "regional", "hub", "ramp", "operations", "batch", "scripts", "shift", "root",
    "fixtures", "truck", "pulse", "feeds", "stand", "assignment", "boards", "mix",
    "assay", "weather", "cell", "bands", "departure", "slot", "retention", "gauge",
    "fluid", "ledger", "runoff", "compliance", "utilization", "audit", "winter",
    "policy", "pack", "volumes", "aircraft", "totals", "rows", "credit", "windows",
    "types", "mixes", "reports", "lab", "summaries", "exceed", "headroom", "diversions",
    "capture", "deliveries", "permit", "reruns", "inflate", "rebuild", "unchanged",
    "names", "gallons", "pad", "type"
  ]
}
"""

if __name__ == "__main__":
    main()
