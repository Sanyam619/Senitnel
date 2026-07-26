#!/usr/bin/env python3
"""One-shot generator for tasks/raft-snapshot-fork-reconcile (authoring tool, not shipped)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / ".tmp-col-ref"
TASK = ROOT / "tasks" / "raft-snapshot-fork-reconcile"
REPORT_NAME = "fork-report.json"


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def copy_ref_tree() -> None:
    if TASK.exists():
        shutil.rmtree(TASK)
    for sub in ("environment", "solution", "tests"):
        shutil.copytree(REF / sub, TASK / sub)


def patch_metadata() -> None:
    w(
        TASK / "task.toml",
        """version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "system-administration"
subcategories = ["tool_specific"]
number_of_milestones = 0
codebase_size = "small"
languages = ["go", "rust"]
tags = ["distributed-log", "operational-recovery", "manifest", "wal", "go-rust", "replay"]
expert_time_estimate_min = 90
junior_time_estimate_min = 240

[verifier]
timeout_sec = 450

[agent]
timeout_sec = 900

[environment]
allow_internet = false
build_timeout_sec = 900
cpus = 2
memory_mb = 4096
storage_mb = 10240
""",
    )

    w(
        TASK / "instruction.md",
        """After a control-plane crash, point lookups and range scans on the events namespace under `/app/data` disagree with what the on-disk journal chain says should be visible. Metrics was not part of the fork.

Recovery is operational: edit operator tables under `/app/config/l7/`, Go sources under `/app/lane/`, and rebuild `/app/bin/lane`. Run `/app/bin/ctl` for recovery operations. See `/app/ops/runbooks/ctl_usage.md` for subcommands and operator table fields. Do not patch the prebuilt Rust ctl sources.

When events queries line up again, emit `/output/fork-report.json` (via `ctl report` or `lane emit`). Include integer `restored_generation` (positive, not above `ceiling_gen` from `ctl status`), and `events` / `metrics` objects each with integer `visible_segments` and hex `sidecar_digest` matching the on-disk sidecar for that namespace under `/app/data/sidecars/`. Range scans at your probe timestamp should list the same keys in sorted order with matching payloads as `/app/bin/ctl query`.
""",
    )

    w(
        TASK / "output_contract.toml",
        f"""user_visible_outputs = [
  "/output/{REPORT_NAME}",
  "/app/bin/ctl",
  "/app/bin/lane",
]

internal_harness_files = [
  "/app/store",
  "/app/lane/internal",
]

[structured_outputs.fork_report]
target = "/output/{REPORT_NAME}"
format = "json"
instruction_checks = [
  "restored_generation",
  "events",
  "metrics",
  "visible_segments",
  "sidecar_digest",
]
""",
    )


def write_go_lane() -> None:
    lane = TASK / "environment" / "lane"
    w(
        lane / "go.mod",
        """module lab.local/raft_fork_lane

go 1.22
""",
    )
    w(lane / "go.sum", "")
    w(
        lane / "pkg" / "frame" / "row.go",
        """package frame

type JournalRow struct {
\tGen     uint64   `json:"gen"`
\tNs      string   `json:"ns"`
\tStripes []uint64 `json:"stripes"`
}

type NamespaceBlock struct {
\tVisibleSegments uint64 `json:"visible_segments"`
\tSidecarDigest  string `json:"sidecar_digest"`
}

type SummaryDoc struct {
\tRestoredGeneration uint64                    `json:"restored_generation"`
\tEvents             NamespaceBlock            `json:"events"`
\tMetrics             NamespaceBlock            `json:"metrics"`
}
""",
    )
    w(
        lane / "internal" / "m7" / "branch.go",
        """package m7

import (
\t"bufio"
\t"encoding/json"
\t"os"
\t"path/filepath"

\t"lab.local/raft_fork_lane/pkg/frame"
)

const splitMark = 99

// ResolveBranch returns the generation the replay lane treats as authoritative
// for namespace ns.
func ResolveBranch(manifestDir, ns string) (uint64, error) {
\tpath := filepath.Join(manifestDir, "tier_c.jsonl")
\tf, err := os.Open(path)
\tif err != nil {
\t\treturn 0, err
\t}
\tdefer f.Close()

\tvar head uint64
\tscan := bufio.NewScanner(f)
\tfor scan.Scan() {
\t\tline := scan.Text()
\t\tif line == "" {
\t\t\tcontinue
\t\t}
\t\tvar row frame.JournalRow
\t\tif err := json.Unmarshal([]byte(line), &row); err != nil {
\t\t\treturn 0, err
\t\t}
\t\tif row.Ns != ns {
\t\t\tcontinue
\t\t}
\t\tif row.Gen > head {
\t\t\thead = row.Gen
\t\t}
\t}
\tif err := scan.Err(); err != nil {
\t\treturn 0, err
\t}
\treturn head, nil
}

func stripesAt(manifestDir, ns string, gen uint64) ([]uint64, error) {
\tvar chain []frame.JournalRow
\tfor _, name := range []string{"tier_a.jsonl", "tier_b.jsonl", "tier_c.jsonl"} {
\t\tpath := filepath.Join(manifestDir, name)
\t\traw, err := os.ReadFile(path)
\t\tif err != nil {
\t\t\treturn nil, err
\t\t}
\t\tfor _, line := range splitLines(string(raw)) {
\t\t\tif line == "" {
\t\t\t\tcontinue
\t\t\t}
\t\t\tvar row frame.JournalRow
\t\t\tif err := json.Unmarshal([]byte(line), &row); err != nil {
\t\t\t\treturn nil, err
\t\t\t}
\t\t\tchain = append(chain, row)
\t\t}
\t}
\tvar pick *frame.JournalRow
\tfor i := range chain {
\t\trow := chain[i]
\t\tif row.Ns != ns || row.Gen > gen {
\t\t\tcontinue
\t\t}
\t\tif pick == nil || row.Gen > pick.Gen {
\t\t\tcopy := row
\t\t\tpick = &copy
\t\t}
\t}
\tif pick == nil {
\t\treturn nil, os.ErrNotExist
\t}
\treturn pick.Stripes, nil
}

func splitLines(s string) []string {
\tvar out []string
\tstart := 0
\tfor i := 0; i < len(s); i++ {
\t\tif s[i] == '\\n' {
\t\t\tout = append(out, s[start:i])
\t\t\tstart = i + 1
\t\t}
\t}
\tif start < len(s) {
\t\tout = append(out, s[start:])
\t}
\treturn out
}
""",
    )
    w(
        lane / "internal" / "m7" / "summary.go",
        """package m7

import (
\t"encoding/json"
\t"os"
\t"path/filepath"

\t"lab.local/raft_fork_lane/pkg/frame"
)

type sidecarDoc struct {
\tDigest string `json:"digest"`
}

func WriteSummary(outPath string) error {
\tmanifestDir := "/app/data/manifests"
\tdataRoot := "/app/data"
\tgen, err := ResolveBranch(manifestDir, "events")
\tif err != nil {
\t\treturn err
\t}
\teventsStripes, err := stripesAt(manifestDir, "events", gen)
\tif err != nil {
\t\treturn err
\t}
\tmetricsStripes, err := stripesAt(manifestDir, "metrics", gen)
\tif err != nil {
\t\treturn err
\t}
\teventsDigest, err := readDigest(filepath.Join(dataRoot, "sidecars", "events.idx"))
\tif err != nil {
\t\treturn err
\t}
\tmetricsDigest, err := readDigest(filepath.Join(dataRoot, "sidecars", "metrics.idx"))
\tif err != nil {
\t\treturn err
\t}
\tdoc := frame.SummaryDoc{
\t\tRestoredGeneration: gen,
\t\tEvents: frame.NamespaceBlock{
\t\t\tVisibleSegments: uint64(len(eventsStripes)),
\t\t\tSidecarDigest:  eventsDigest,
\t\t},
\t\tMetrics: frame.NamespaceBlock{
\t\t\tVisibleSegments: uint64(len(metricsStripes)),
\t\t\tSidecarDigest:  metricsDigest,
\t\t},
\t}
\tpayload, err := json.MarshalIndent(doc, "", "  ")
\tif err != nil {
\t\treturn err
\t}
\tpayload = append(payload, '\\n')
\tif err := os.MkdirAll(filepath.Dir(outPath), 0o755); err != nil {
\t\treturn err
\t}
\treturn os.WriteFile(outPath, payload, 0o644)
}

func readDigest(path string) (string, error) {
\traw, err := os.ReadFile(path)
\tif err != nil {
\t\treturn "", err
\t}
\tvar sc sidecarDoc
\tif err := json.Unmarshal(raw, &sc); err != nil {
\t\treturn "", err
\t}
\treturn sc.Digest, nil
}
""",
    )
    w(
        lane / "cmd" / "lane" / "main.go",
        """package main

import (
\t"flag"
\t"fmt"
\t"log"
\t"os"

\t"lab.local/raft_fork_lane/internal/m7"
)

func main() {
\tif len(os.Args) < 2 {
\t\tlog.Fatal("usage: lane head|emit")
\t}
\tswitch os.Args[1] {
\tcase "head":
\t\tgen, err := m7.ResolveBranch("/app/data/manifests", "events")
\t\tif err != nil {
\t\t\tlog.Fatal(err)
\t\t}
\t\tfmt.Println(gen)
\tcase "emit":
\t\tfs := flag.NewFlagSet("emit", flag.ExitOnError)
\t\tout := fs.String("out", "", "output path")
\t\t_ = fs.Parse(os.Args[2:])
\t\tif *out == "" {
\t\t\tlog.Fatal("emit requires --out")
\t\t}
\t\tif err := m7.WriteSummary(*out); err != nil {
\t\t\tlog.Fatal(err)
\t\t}
\tdefault:
\t\tlog.Fatalf("unknown subcommand %q", os.Args[1])
\t}
}
""",
    )


def patch_dockerfile() -> None:
    w(
        TASK / "environment" / "Dockerfile",
        """# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS go_builder

WORKDIR /build/lane
COPY lane/go.mod lane/go.sum ./
RUN go mod download
COPY lane/pkg/frame/row.go pkg/frame/row.go
COPY lane/internal/m7/ internal/m7/
COPY lane/cmd/lane/ cmd/lane/
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /lane ./cmd/lane

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rust_builder

WORKDIR /build/store

COPY store/Cargo.toml store/Cargo.lock ./
COPY store/manifest/Cargo.toml manifest/
COPY store/wal/Cargo.toml wal/
COPY store/index/Cargo.toml index/
COPY store/ops/Cargo.toml ops/
COPY store/ctl/Cargo.toml ctl/

COPY store/src/ src/
COPY store/manifest/src/ manifest/src/
COPY store/wal/src/ wal/src/
COPY store/index/src/ index/src/
COPY store/ops/src/ ops/src/
COPY store/ctl/src/ ctl/src/

RUN cargo build --release --locked -p ctl

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before any other setup.
RUN apt-get update \\
    && apt-get install -y --no-install-recommends tmux asciinema \\
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux kill-session -t _smoke

RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        bash \\
        ca-certificates=20230311+deb12u1 \\
        procps \\
        python3=3.11.2-1+b1 \\
        python3-pip=23.0.1+dfsg-1 \\
        python-is-python3 \\
    && rm -rf /var/lib/apt/lists/*

ENV GOPATH=/go \\
    GOCACHE=/tmp/go-cache \\
    GOMODCACHE=/go/pkg/mod \\
    GOPROXY=off
RUN mkdir -p /go /tmp/go-cache

RUN pip3 install --no-cache-dir --break-system-packages \\
    pytest==8.4.1 \\
    pytest-json-ctrf==0.3.5

COPY --from=rust_builder --chmod=755 /build/store/target/release/ctl /app/bin/ctl
COPY --from=go_builder --chmod=755 /lane /app/bin/lane
COPY config/ /app/config/
COPY data/ /app/data/
COPY store/ /app/store/
COPY lane/ /app/lane/
COPY ops/ /app/ops/

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux kill-session -t _smoke

WORKDIR /app
ENV PATH="/app/bin:${PATH}"
""",
    )


def patch_runbook() -> None:
    w(
        TASK / "environment" / "ops" / "runbooks" / "ctl_usage.md",
        """# ctl operator reference

The control binary lives at `/app/bin/ctl`. The Go replay lane lives at `/app/bin/lane`. Operator tables live under `/app/config/l7/` as TOML files; field names are read by the binaries at runtime.

## Operator tables

| Table file | Field | Role |
|------------|-------|------|
| `k9.toml` | `tier_c` | Roll anchor used by the roll phase |
| `m2.toml` | `seq_cutoff` | WAL replay cutoff applied during barrier |
| `p7.toml` | `phases` | Ordered recovery workflow phase list |

Decoy tables (`n3.toml`, `r8.toml`) mirror field names but are not read by `ctl`.

## ctl subcommands

### roll

Rolls the active journal head for one namespace using the tier anchor from operator tables.

```
/app/bin/ctl roll --ks <namespace>
```

### barrier

Applies the WAL replay cutoff from operator tables and records tombstone keys into `/app/data/state/runtime.json`.

```
/app/bin/ctl barrier
```

### rebuild

Rebuilds the secondary index sidecar for one namespace after barrier application.

```
/app/bin/ctl rebuild --ks <namespace>
```

### status

Read-only runtime snapshot (`active_gen`, `ceiling_gen`, `wal_seq`).

```
/app/bin/ctl status
```

### query

Read-only diagnostics. Supports point, range, and aggregate modes.

```
/app/bin/ctl query point --ks <namespace> --key <key> --ts <unix_ms>
/app/bin/ctl query range --ks <namespace> --lo <key> --hi <key> --ts <unix_ms>
/app/bin/ctl query aggregate --ks <namespace> --ts <unix_ms>
```

### report

Emits the recovery summary JSON.

```
/app/bin/ctl report --out /output/fork-report.json
```

## lane subcommands

### head

Prints the generation the Go replay lane currently selects for the events namespace.

```
/app/bin/lane head
```

### emit

Writes the lane-side recovery summary JSON using the lane generation picker and on-disk sidecar digests.

```
/app/bin/lane emit --out /output/fork-report.json
```

Rebuild the lane after editing Go sources:

```
cd /app/lane && go build -trimpath -ldflags="-s -w" -o /app/bin/lane ./cmd/lane
```

## Fixture layout

Column stripes live under `/app/data/columns/` (`{namespace}_{stripe}.col` and `{namespace}_merged.col`). Sidecar indexes are `/app/data/sidecars/{namespace}.idx`. Journal chains are under `/app/data/manifests/` (`tier_a.jsonl`, `tier_b.jsonl`, `tier_c.jsonl`). WAL segments are `/app/data/wal/seg_001.bin` and `/app/data/wal/seg_002.bin`. Runtime state is written to `/app/data/state/runtime.json`.

## Notes

- `compact` runs forward compaction against the current head and is unsafe on a partially applied recovery.
- Fast index patch helpers in the store sources do not replace a full rebuild after barrier application.
""",
    )


def write_branch_fixtures() -> None:
    w(
        TASK / "solution" / "fixtures" / "branch.go",
        """package m7

import (
\t"bufio"
\t"encoding/json"
\t"os"
\t"path/filepath"

\t"lab.local/raft_fork_lane/pkg/frame"
)

const splitMark = 99

// ResolveBranch returns the generation the replay lane treats as authoritative
// for namespace ns.
func ResolveBranch(manifestDir, ns string) (uint64, error) {
\tpath := filepath.Join(manifestDir, "tier_b.jsonl")
\tf, err := os.Open(path)
\tif err != nil {
\t\treturn 0, err
\t}
\tdefer f.Close()

\tvar anchor uint64
\tscan := bufio.NewScanner(f)
\tfor scan.Scan() {
\t\tline := scan.Text()
\t\tif line == "" {
\t\t\tcontinue
\t\t}
\t\tvar row frame.JournalRow
\t\tif err := json.Unmarshal([]byte(line), &row); err != nil {
\t\t\treturn 0, err
\t\t}
\t\tif row.Ns != ns {
\t\t\tcontinue
\t\t}
\t\tfor _, stripe := range row.Stripes {
\t\t\tif stripe == splitMark {
\t\t\t\treturn anchor, nil
\t\t\t}
\t\t}
\t\tanchor = row.Gen
\t}
\tif err := scan.Err(); err != nil {
\t\treturn 0, err
\t}
\treturn anchor, nil
}

func stripesAt(manifestDir, ns string, gen uint64) ([]uint64, error) {
\tvar chain []frame.JournalRow
\tfor _, name := range []string{"tier_a.jsonl", "tier_b.jsonl", "tier_c.jsonl"} {
\t\tpath := filepath.Join(manifestDir, name)
\t\traw, err := os.ReadFile(path)
\t\tif err != nil {
\t\t\treturn nil, err
\t\t}
\t\tfor _, line := range splitLines(string(raw)) {
\t\t\tif line == "" {
\t\t\t\tcontinue
\t\t\t}
\t\t\tvar row frame.JournalRow
\t\t\tif err := json.Unmarshal([]byte(line), &row); err != nil {
\t\t\t\treturn nil, err
\t\t\t}
\t\t\tchain = append(chain, row)
\t\t}
\t}
\tvar pick *frame.JournalRow
\tfor i := range chain {
\t\trow := chain[i]
\t\tif row.Ns != ns || row.Gen > gen {
\t\t\tcontinue
\t\t}
\t\tif pick == nil || row.Gen > pick.Gen {
\t\t\tcopy := row
\t\t\tpick = &copy
\t\t}
\t}
\tif pick == nil {
\t\treturn nil, os.ErrNotExist
\t}
\treturn pick.Stripes, nil
}

func splitLines(s string) []string {
\tvar out []string
\tstart := 0
\tfor i := 0; i < len(s); i++ {
\t\tif s[i] == '\\n' {
\t\t\tout = append(out, s[start:i])
\t\t\tstart = i + 1
\t\t}
\t}
\tif start < len(s) {
\t\tout = append(out, s[start:])
\t}
\treturn out
}
""",
    )


def patch_solve() -> None:
    write_branch_fixtures()
    w(
        TASK / "solution" / "solve.sh",
        f"""#!/bin/bash
set -euo pipefail

test -d /app/config/l7
test -x /app/bin/ctl
test -d /app/lane
mkdir -p /output /app/ops/staging

read -r ANCHOR CUTOFF < <(
python3 <<'PY'
import json
from pathlib import Path

data = Path("/app/data")


def discover_anchor() -> int:
    anchor = None
    for line in (data / "manifests/tier_b.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("ns") != "events":
            continue
        if 99 in rec.get("stripes", []):
            break
        anchor = int(rec["gen"])
    if anchor is None:
        raise SystemExit("could not derive anchor generation from tier_b journal")
    return anchor


def discover_barrier() -> int:
    tombstone_seq = None
    for name in ("seg_001.bin", "seg_002.bin"):
        blob = (data / "wal" / name).read_bytes()
        if blob[:4] != b"WLOG":
            raise SystemExit(f"bad wal magic in {{name}}")
        off = 4
        while off + 11 <= len(blob):
            seq = int.from_bytes(blob[off : off + 8], "little")
            off += 8
            op = blob[off]
            off += 1
            key_len = int.from_bytes(blob[off : off + 2], "little")
            off += 2
            key = blob[off : off + key_len].decode()
            off += key_len
            off += 8
            if op == 1 and key == "marker_zulu":
                tombstone_seq = seq
    if tombstone_seq is None:
        raise SystemExit("could not locate tombstone cutoff in wal segments")
    return tombstone_seq


print(discover_anchor(), discover_barrier())
PY
)

sed -i "s/^tier_c = .*/tier_c = ${{ANCHOR}}/" /app/config/l7/k9.toml
sed -i "s/^journal_pin = .*/journal_pin = ${{ANCHOR}}/" /app/config/l7/k9.toml
sed -i "s/^head_floor = .*/head_floor = ${{ANCHOR}}/" /app/config/l7/k9.toml
sed -i 's/^roll_ready = .*/roll_ready = true/' /app/config/l7/k9.toml
sed -i 's/^audit_stamp = .*/audit_stamp = "applied"/' /app/config/l7/k9.toml
sed -i 's/^sync_token = .*/sync_token = "armed"/' /app/config/l7/k9.toml

sed -i "s/^seq_cutoff = .*/seq_cutoff = ${{CUTOFF}}/" /app/config/l7/m2.toml
sed -i "s/^wal_floor = .*/wal_floor = ${{CUTOFF}}/" /app/config/l7/m2.toml
sed -i 's/^barrier_live = .*/barrier_live = true/' /app/config/l7/m2.toml
sed -i 's/^replay_gate = .*/replay_gate = 0/' /app/config/l7/m2.toml
sed -i 's/^tomb_scan = .*/tomb_scan = true/' /app/config/l7/m2.toml

sed -i 's/^phases = .*/phases = ["roll", "barrier", "rebuild"]/' /app/config/l7/p7.toml
sed -i 's/^strict_chain = .*/strict_chain = true/' /app/config/l7/p7.toml
sed -i 's/^allow_batch = .*/allow_batch = false/' /app/config/l7/p7.toml
sed -i 's/^workflow_note = .*/workflow_note = "live"/' /app/config/l7/p7.toml

cp /solution/fixtures/branch.go /app/lane/internal/m7/branch.go

(cd /app/lane && go build -trimpath -ldflags="-s -w" -o /app/bin/lane ./cmd/lane)

for phase in roll barrier rebuild; do
  case "${{phase}}" in
    roll)
      /app/bin/ctl roll --ks events
      ;;
    barrier)
      /app/bin/ctl barrier
      ;;
    rebuild)
      /app/bin/ctl rebuild --ks events
      ;;
    *)
      echo "unknown phase ${{phase}}" >&2
      exit 1
      ;;
  esac
done

/app/bin/ctl report --out /output/{REPORT_NAME}
/app/bin/lane emit --out /output/{REPORT_NAME}

probe_alpha=$(/app/bin/ctl query point --ks events --key alpha --ts 550)
probe_marker=$(/app/bin/ctl query point --ks events --key marker_zulu --ts 550)
echo "${{probe_alpha}}" | grep -q '"found":true'
echo "${{probe_marker}}" | grep -q '"found":false'

lane_head=$(/app/bin/lane head)
runtime_gen=$(python3 -c "import json; print(json.load(open('/app/data/state/runtime.json'))['active_gen'])")
test "${{lane_head}}" = "${{runtime_gen}}"

status_json=$(/app/bin/ctl status)
restored_gen=$(python3 -c "import json; print(json.load(open('/output/{REPORT_NAME}'))['restored_generation'])")
ceiling_gen=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['ceiling_gen'])" "${{status_json}}")
test "${{restored_gen}}" -le "${{ceiling_gen}}"

echo "complete" > /app/ops/staging/workflow.complete
""",
    )


def patch_tests() -> None:
    src = (REF / "tests" / "test_outputs.py").read_text()
    src = src.replace("rewind-report.json", REPORT_NAME)
    src = src.replace('CTL = "/app/bin/ctl"', 'CTL = "/app/bin/ctl"\nLANE = "/app/bin/lane"')
    extra = '''

def _lane_head() -> int:
    result = subprocess.run(
        [LANE, "head"],
        check=True,
        capture_output=True,
        text=True,
    )
    return int(result.stdout.strip())


def test_lane_generation_matches_runtime():
    """Go replay lane head matches rolled runtime generation after recovery."""
    runtime = _load_runtime()
    anchor = _discover_roll_anchor()
    lane_gen = _lane_head()
    assert lane_gen == runtime["active_gen"]
    assert lane_gen == anchor


def test_lane_report_matches_ctl_report():
    """Lane emit and ctl report agree on restored generation and digests."""
    ctl_report = json.loads(REPORT_PATH.read_text())
    lane_gen = _lane_head()
    assert ctl_report["restored_generation"] == lane_gen
    assert ctl_report["restored_generation"] == _discover_roll_anchor()
    for ns in ("events", "metrics"):
        sidecar = json.loads(Path(f"/app/data/sidecars/{ns}.idx").read_text())
        assert ctl_report[ns]["sidecar_digest"] == sidecar["digest"]
'''
    if "test_lane_generation_matches_runtime" not in src:
        src = src.rstrip() + extra + "\n"
    w(TASK / "tests" / "test_outputs.py", src)


def patch_runtime_ceiling() -> None:
    runtime_path = TASK / "environment" / "data" / "state" / "runtime.json"
    runtime = json.loads(runtime_path.read_text())
    runtime["ceiling_gen"] = 22
    runtime["active_gen"] = 22
    w(runtime_path, json.dumps(runtime, indent=2) + "\n")


def write_spec() -> None:
    spec_dir = ROOT / "specs"
    spec_dir.mkdir(exist_ok=True)
    w(
        spec_dir / "raft-snapshot-fork-reconcile.md",
        """### Decision
GO — Attempt 1. Dual-language distributed-log recovery with divergent post-crash generations; Go replay lane must align with Rust manifest tier and ctl workflow.

### Metadata
- version: 2
- Task name: raft-snapshot-fork-reconcile
- Title: Snapshot fork reconcile
- Category: system-administration
- Languages: ["go", "rust"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["distributed-log", "operational-recovery", "manifest", "wal", "go-rust", "replay"]
- Milestones: 0

## Authoring Brief

### Public contract
Symptoms-only instruction describing inconsistent events queries after a crash left competing snapshot generations. Agent may edit `/app/config/l7/` operator tables and `/app/lane/` Go sources; Rust store is read-only. Recovery uses ctl roll/barrier/rebuild workflow. Output `/output/fork-report.json` with `restored_generation`, per-namespace `visible_segments`, and `sidecar_digest`. Deterministic replay probes via ctl query at timestamp 550.

### Failure topology
Two authorities disagree after crash: Rust manifest tier journals record a pre-fork anchor while a fork head generation remains on disk; Go replay lane selects the fork head from the wrong journal tier. Operator tables ship with unsafe phase order, wrong anchor pin, and disabled barrier cutoff. Query path uses stale sidecar binding until roll/barrier/rebuild completes. Metrics namespace stays stable as control.

### Environment shape
`/app/store/` Rust workspace (ctl, manifest, wal, index, ops). `/app/lane/` Go replay module. `/app/data/` columns, sidecars, manifests, wal, runtime state. `/app/config/l7/` operator tables. `/app/ops/runbooks/` reference. `/app/bin/ctl` and `/app/bin/lane` binaries.

### Required artifacts
instruction.md, task.toml, output_contract.toml, environment/Dockerfile, environment/.dockerignore, Go lane module, Rust store copy, fixtures, solution/solve.sh, tests/test.sh, tests/test_outputs.py.

### Test plan
- Point/range/aggregate ctl probes against fixture columns
- Tombstone absence at query window
- fork-report schema and generation bounds
- Runtime chain alignment with manifest anchor
- Operator table phase order and cutoff fields
- Sidecar digest match on disk
- Metrics namespace stability
- Lane head matches runtime active generation
- Lane report agrees with ctl report fields

### Drafting guardrails
Instruction uses snapshot/fork/replay/manifest tier vocabulary; fix-path Go symbols stay opaque (m7, k3, splitMark). No Rust edits in oracle. Tests must not embed instruction nouns as substrings in function names.

### Triviality Ledger
- Setting only k9.toml tier_c without fixing lane tier picker leaves fork-head selection — blocked by lane/runtime generation test.
- Running rebuild before barrier leaves tombstone keys visible — blocked by marker absence probe.
- Copying ctl report JSON without lane emit — blocked by lane head pre-report check in oracle and lane generation test.

### Per-gate Pitfall Inventory
- RC1: oracle touches config tables, Go branch.go, and workflow phases — multi-file.
- RC3/GX3: decoy k3/anchor helper and index rebuild_fast module provide non-fix rhymes.
- CR7: code_forbidden_tokens lists instruction nouns; grep_resistance on Go/Rust fix frontier.
- GX10: concentration split across config, Go m7, and ctl workflow tests.

### Initial Draft Commitments
- instruction.md
- task.toml
- output_contract.toml
- solution/solve.sh
- tests/test.sh
- tests/test_outputs.py
- environment/Dockerfile
- environment/.dockerignore
- environment/lane/go.mod
- environment/lane/cmd/lane/main.go
- environment/lane/internal/m7/branch.go
- environment/lane/internal/m7/summary.go
- environment/lane/internal/k3/anchor.go
- environment/lane/pkg/frame/row.go
- environment/config/l7/k9.toml
- environment/config/l7/m2.toml
- environment/config/l7/p7.toml
- environment/config/l7/n3.toml
- environment/config/l7/r8.toml
- environment/data/state/runtime.json
- environment/data/manifests/tier_a.jsonl
- environment/data/manifests/tier_b.jsonl
- environment/data/manifests/tier_c.jsonl
- environment/data/wal/seg_001.bin
- environment/data/wal/seg_002.bin
- environment/data/columns/events_001.col
- environment/data/columns/events_002.col
- environment/data/columns/events_003.col
- environment/data/columns/events_merged.col
- environment/data/columns/metrics_010.col
- environment/data/columns/metrics_011.col
- environment/data/columns/metrics_merged.col
- environment/data/sidecars/events.idx
- environment/data/sidecars/metrics.idx
- environment/ops/runbooks/ctl_usage.md
- environment/store/** (full Rust workspace from reference)

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: lane/internal/m7/branch.go
  symbol: ResolveBranch
  kind: function
  signature: func ResolveBranch(manifestDir, ns string) (uint64, error)
  purpose: selects namespace generation for lane summary
- path: config/l7/k9.toml
  symbol: tier_c
  kind: constant
  signature: tier_c = <u64>
  purpose: roll anchor pin read by ctl roll phase
- path: config/l7/m2.toml
  symbol: seq_cutoff
  kind: constant
  signature: seq_cutoff = <u64>
  purpose: wal barrier cutoff for tombstone application
- path: config/l7/p7.toml
  symbol: phases
  kind: constant
  signature: phases = ["roll", "barrier", "rebuild"]
  purpose: ordered recovery workflow for ctl

#### flipping_point_contract
locations:
  - id: A
    path: lane/internal/m7/branch.go
    controls_tests: [test_lane_generation_matches_runtime, test_lane_report_matches_ctl_report]
  - id: B
    path: config/l7/k9.toml
    controls_tests: [test_recovery_config_phase_order, test_chain_order_invariant]
  - id: C
    path: config/l7/m2.toml
    controls_tests: [test_absent_marker_at_window, test_barrier_tombstone_runtime_state]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- path: lane/internal/k3/anchor.go
  kind: helper
  rhymes_with: ResolveBranch
  non_fix_purpose: standalone tier_b scanner not wired into stock lane emit path
- path: store/index/src/rebuild_fast.rs
  kind: module
  rhymes_with: rebuild
  non_fix_purpose: partial index patch helper unsafe after barrier

#### code_forbidden_tokens
code_forbidden_tokens: [snapshot, fork, replay, manifest, tier, generation, reconcile, raft, crash, divergent, align, engine, probe, recovery, barrier, roll, rebuild, wal, sidecar, events, metrics, operator, ctl, lane, report, digest, segments, tombstone, namespace, columns, journal, stripe, workflow, cutoff, anchor, ceiling, runtime, query, range, aggregate, point, key, payload, lexicographic, visible, restored, control-plane, shard, payloads, indexes, chains, subcommands, tables, sources, timestamps, status, positive, hex, string, integer, object, write, edit, rebuilds, subcommand, reference, runbooks, data, config, store, bin, output, app, must, after, same, order, matching, returns, scans, window, under, pattern, include, files, live, competing, untouched, disagree, says, should, what, left, two, with, from, through, applies, picks, admits, sorted, over, at, the, and, plus, each, not, exceed, reported, match, on-disk, for, that, namespace]
""",
    )


def main() -> None:
    copy_ref_tree()
    patch_metadata()
    write_go_lane()
    patch_dockerfile()
    patch_runbook()
    patch_solve()
    patch_tests()
    patch_runtime_ceiling()
    write_spec()
    env_files = sum(1 for _ in (TASK / "environment").rglob("*") if _.is_file())
    print(f"Generated {TASK} ({env_files} environment files)")


if __name__ == "__main__":
    main()
