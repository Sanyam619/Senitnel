#!/usr/bin/env python3
"""Generator for tasks/hydrology-gauge-backfill-reconcile (authoring tool, not shipped)."""

from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "hydrology-gauge-backfill-reconcile"
REF = ROOT / ".tmp-col-ref"

CANONICAL_GOLANG = (
    "public.ecr.aws/docker/library/golang:1.24-bookworm"
    "@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac"
)
CANONICAL_RUST = (
    "public.ecr.aws/docker/library/rust:1.85-slim"
    "@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36"
)
CANONICAL_DEBIAN = (
    "public.ecr.aws/docker/library/debian:bookworm-slim"
    "@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d"
)

INSTRUCTION = """\
Gauge point lookups and range scans under `/app/data` went inconsistent following a partial station calibration reload — some keys that should be visible are missing or wrong, a tombstoned marker surfaces in the query window, and `/app/bin/window` disagrees with `/app/bin/ctl` aggregates at the same timestamp. Telemetry was outside the reload and stays that way: do not rebuild the metrics sidecar under `/app/data/sidecars/`. Sample keys for the active window are listed under `/app/ops/fixtures/rating_samples.json`.

Recovery is operational only: edit operator tables under `/app/config/l7/` and run `/app/bin/ctl` and `/app/bin/window`. See `/app/ops/runbooks/` for subcommands and operator table fields. Do not change sources under `/app/store` or `/app/lane`. The runtime state left by the failed reload is not authoritative; use the durable stores under `/app/data/`.

The restored calibration epoch is the last events generation in `/app/data/manifests/tier_b.jsonl` whose stripe set does not include 99 (the pre-contamination tier_b head). Later merged generations that already carry stripe 99 are past the cutover and are not the recovery target.

Required recovery order on the primary gauge channel: roll, barrier, rebuild, then report. Rebuild the events sidecar with the barrier tombstone already committed in runtime state; the events sidecar under `/app/data/sidecars/` ends bound to the restored generation with the tombstoned marker absent from its map. A rebuild that ran without committed barrier tombstones is incomplete — rerun rebuild, then emit the report. Exact ctl subcommands are in `/app/ops/runbooks/`.

Emit `/output/backfill-report.json` via `/app/bin/ctl report`. `restored_generation` equals that tier_b pre-contamination generation (positive, not above `ceiling_gen` from `/app/bin/ctl status`). Per-channel objects each need integer `visible_segments` and hex `sidecar_digest` matching the on-disk sidecar under `/app/data/sidecars/`. Range scans at the probe timestamp should list the same keys in sorted order with matching payloads; aggregate count and stage-sum totals agree with the merged archive baseline. `/app/bin/window head` equals `restored_generation` — the runbook documents how scan_tier, roll_ready, and journal_pin resolve that head.
"""
TASK_TOML = """\
version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "data-processing"
subcategories = []
number_of_milestones = 0
codebase_size = "small"
languages = ["bash", "rust", "go"]
tags = ["hydrology", "gauge-recovery", "operator-tables", "wal-replay", "runtime-state", "ctl"]
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
"""

OUTPUT_CONTRACT = """\
user_visible_outputs = [
  "/output/backfill-report.json",
]

internal_harness_files = [
  "/app/data/state/runtime.json",
  "/app/data/sidecars/events.idx",
  "/app/data/sidecars/metrics.idx",
]

[structured_outputs.backfill_report]
target = "/output/backfill-report.json"
format = "json"
instruction_checks = [
  "restored_generation",
  "visible_segments",
  "sidecar_digest",
]
"""

RUNBOOK = """\
# ctl operator reference

The control binary lives at `/app/bin/ctl`. Basin-window diagnostics live at `/app/bin/window`. Operator tables live under `/app/config/l7/` as TOML files read at runtime. Domain notes for the rating-curve and water-balance checks live alongside this runbook.

## Operator tables

TOML files under `/app/config/l7/` hold knobs consulted by `ctl` and `window`. Field names and types are as written in each file. Which knobs a given subcommand reads is determined by binary behavior at runtime.

Notable fields for this recovery:

- `k9.toml` — `tier_c` is the generation `ctl roll` writes into runtime `active_gen`. `journal_pin` and `roll_ready` also feed `/app/bin/window head` (see Basin-window lane).
- `m2.toml` — `scan_tier` selects which journal file `window head` scans (`tier_<scan_tier>.jsonl`). `seq_cutoff` and related fields feed `ctl barrier`.

## Subcommands

### barrier

```
/app/bin/ctl barrier
```

Applies a WAL sequence cutoff from operator tables and records committed tombstone state into `/app/data/state/runtime.json`.

### query

```
/app/bin/ctl query point --ks <channel> --key <key> --ts <unix_ms>
/app/bin/ctl query range --ks <channel> --lo <key> --hi <key> --ts <unix_ms>
/app/bin/ctl query aggregate --ks <channel> --ts <unix_ms>
```

Read-only diagnostics: point probe, range scan, and aggregate (count and stage-sum) at a given timestamp.

### rebuild

```
/app/bin/ctl rebuild --ks <channel>
```

Rebuilds the numerical sidecar index for a channel against the current head, applying any tombstones already committed in runtime state. For this incident, rebuild the primary gauge channel (`events`) only, and only after `ctl barrier` has committed the WAL tombstone cutoff. Telemetry (`metrics`) was outside the reload; leave `/app/data/sidecars/metrics.idx` at its pre-reload `bound_gen` and digest.

### report

```
/app/bin/ctl report --out /output/backfill-report.json
```

Emits the basin water-balance summary JSON to the given path. `restored_generation` reflects runtime `active_gen` after roll. Per-channel `sidecar_digest` values are read from the on-disk sidecars. Run report only after the final post-barrier rebuild.

### roll

```
/app/bin/ctl roll --ks <channel>
```

Sets the active journal head for a channel from `tier_c` in `k9.toml`. Point `tier_c` at the pre-contamination tier_b events generation (last `events` row in `/app/data/manifests/tier_b.jsonl` whose `stripes` do not include `99`).

### status

```
/app/bin/ctl status
```

Read-only runtime snapshot including `active_gen`, `ceiling_gen`, and `wal_seq`.

## Recovery sequence

After operator tables are corrected, run:

```
/app/bin/ctl roll --ks events
/app/bin/ctl barrier
/app/bin/ctl rebuild --ks events
/app/bin/ctl report --out /output/backfill-report.json
```

Order matters. Barrier commits the tombstone cutoff into runtime state. The final `rebuild --ks events` must follow that commit so `/app/data/sidecars/events.idx` is bound to the restored generation and its map excludes the tombstoned marker. If rebuild ran before barrier, rerun rebuild after barrier before `ctl report`.

## Basin-window lane

```
/app/bin/window head
/app/bin/window aggregate --ks <channel> --ts <unix_ms>
```

`window head` opens `/app/data/manifests/tier_<scan_tier>.jsonl` (from `scan_tier` in `m2.toml`) and takes the maximum `gen` in that file. When `roll_ready` in `k9.toml` is false, `journal_pin` in `k9.toml` caps that value whenever the pin is below the scanned maximum. When `roll_ready` is true, the pin is not applied and the scanned-tier maximum stands. After recovery, `window head` must equal the restored generation reported by `ctl report`.

`window aggregate` evaluates the merged archive for the requested channel at the given timestamp.

## Fixture layout

Merged gauge archives use the `{channel}_merged.col` filename under `/app/data/columns/`. Sidecar indexes include `/app/data/sidecars/events.idx` and `/app/data/sidecars/metrics.idx`. Journal chains live under `/app/data/manifests/`. WAL segments are under `/app/data/wal/`. Runtime snapshots are written to `/app/data/state/runtime.json`. Rating-window sample keys live under `/app/ops/fixtures/rating_samples.json`.
"""
HYDROLOGY_MODEL = """\
# Hydrologic gauge model notes

The pre-built rollup index under `/app/store` maintains stage-sum and count
totals for gauge series used in rating-curve and basin water-balance checks.
The basin-window helper under `/app/lane` evaluates the same epoch window for
cross-check purposes. Operator tables under `/app/config/l7/` select the
active calibration epoch and WAL replay cutoff that those tools read.

Journal generations whose stripe set includes `99` are post-contamination
(merged cutover). The recovery calibration epoch is the last `events`
generation in `/app/data/manifests/tier_b.jsonl` whose stripes do not include
`99`. Later tier_c merged generations are past that cutover and are not the
target for `restored_generation`.

Telemetry (`metrics`) was outside the failed reload. Leave its sidecar at the
pre-reload `bound_gen` and digest; do not run rebuild against that channel.

Primary recovery is roll, then barrier, then rebuild on `events`. The events
sidecar map only drops committed tombstones when rebuild runs after barrier;
an early rebuild must be redone before report.

When the active generation and barrier cutoff disagree with the journal and WAL
history, stage-sum totals and basin-window probes diverge even though individual
reading archives still look intact. `/app/bin/window head` follows `scan_tier`,
`roll_ready`, and `journal_pin` as documented in the ctl operator reference.
"""
DOCKERFILE = f"""\
# syntax=docker/dockerfile:1

FROM {CANONICAL_RUST} AS rsbuilder

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

FROM {CANONICAL_GOLANG} AS gobuilder

WORKDIR /build/lane
COPY lane/go.mod lane/go.sum ./
COPY lane/pkg/ pkg/
COPY lane/internal/ internal/
COPY lane/cmd/ cmd/
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/window ./cmd/window

FROM {CANONICAL_DEBIAN}

LABEL org.opencontainers.image.source="com.hydro.basin-gauge-ops"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        asciinema=2.2.0-1 \\
        bash \\
        ca-certificates=20230311+deb12u1 \\
        libutempter0 \\
        openssl=3.0.17-1~deb12u2 \\
        procps \\
        python3=3.11.2-1+b1 \\
        python3-pip=23.0.1+dfsg-1 \\
        python-is-python3 \\
        tmux=3.3a-3 \\
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux send-keys -t _smoke 'echo tmux_ok' Enter \\
    && tmux capture-pane -t _smoke -p | grep -q tmux_ok \\
    && tmux kill-session -t _smoke

RUN pip3 install --no-cache-dir --break-system-packages \\
    pytest==8.4.1 \\
    pytest-json-ctrf==0.3.5

COPY --from=rsbuilder --chmod=755 /build/store/target/release/ctl /app/bin/ctl
COPY --from=gobuilder --chmod=755 /out/window /app/bin/window
COPY config/ /app/config/
COPY data/ /app/data/
COPY store/ /app/store/
COPY lane/ /app/lane/
COPY ops/ /app/ops/

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux send-keys -t _smoke 'echo tmux_ok' Enter \\
    && tmux capture-pane -t _smoke -p | grep -q tmux_ok \\
    && tmux kill-session -t _smoke

ENV PATH="/app/bin:${{PATH}}"

WORKDIR /root
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
**/.venv/
**/venv/
.env
*.log
solution/
tests/
"""

GO_MOD = """module lab.local/hydro_lane

go 1.22
"""

GO_FRAME = """package frame

type JournalRow struct {
\tGen uint64 `json:"gen"`
\tNs   string `json:"ns"`
\tStripes []int `json:"stripes"`
}

type ColumnRecord struct {
\tK string `json:"k"`
\tV string `json:"v"`
\tT int64  `json:"t"`
}

type ColumnStripe struct {
\tID      int    `json:"id"`
\tRecords []ColumnRecord `json:"records"`
}
"""

GO_CFG = """package cfg

import (
\t"os"
\t"path/filepath"
\t"strconv"
\t"strings"
)

func readTable(configDir, table string) map[string]string {
\tout := map[string]string{}
\traw, err := os.ReadFile(filepath.Join(configDir, table))
\tif err != nil {
\t\treturn out
\t}
\tfor _, line := range strings.Split(string(raw), "\\n") {
\t\ttrimmed := strings.TrimSpace(line)
\t\tif trimmed == "" || strings.HasPrefix(trimmed, "#") {
\t\t\tcontinue
\t\t}
\t\tparts := strings.SplitN(trimmed, "=", 2)
\t\tif len(parts) != 2 {
\t\t\tcontinue
\t\t}
\t\tkey := strings.TrimSpace(parts[0])
\t\tval := strings.TrimSpace(parts[1])
\t\tout[key] = val
\t}
\treturn out
}

func ScanTier(configDir string) string {
\ttbl := readTable(configDir, "m2.toml")
\tif raw, ok := tbl["scan_tier"]; ok {
\t\treturn strings.Trim(raw, "\\"")
\t}
\treturn "b"
}

func JournalPin(configDir string) (uint64, bool) {
\ttbl := readTable(configDir, "k9.toml")
\traw, ok := tbl["journal_pin"]
\tif !ok {
\t\treturn 0, false
\t}
\tval, err := strconv.ParseUint(raw, 10, 64)
\tif err != nil {
\t\treturn 0, false
\t}
\treturn val, true
}

func RollReady(configDir string) bool {
\ttbl := readTable(configDir, "k9.toml")
\treturn strings.TrimSpace(tbl["roll_ready"]) == "true"
}
"""

GO_M7 = """package m7

import (
\t"bufio"
\t"encoding/json"
\t"os"
\t"path/filepath"

\t"lab.local/hydro_lane/internal/cfg"
\t"lab.local/hydro_lane/pkg/frame"
)

func ResolveHead(journalDir, configDir string) (uint64, error) {
\ttier := cfg.ScanTier(configDir)
\tpath := filepath.Join(journalDir, "tier_"+tier+".jsonl")
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
\t\tif row.Gen > head {
\t\t\thead = row.Gen
\t\t}
\t}
\tif err := scan.Err(); err != nil {
\t\treturn 0, err
\t}
\tif !cfg.RollReady(configDir) {
\t\tif pin, ok := cfg.JournalPin(configDir); ok && pin < head {
\t\t\thead = pin
\t\t}
\t}
\treturn head, nil
}
"""

GO_K3 = """package k3

import (
\t"encoding/json"
\t"os"
\t"path/filepath"

\t"lab.local/hydro_lane/pkg/frame"
)

func mergedAggregate(dataRoot, channel string, ts int64) (int, int64, error) {
\tpath := filepath.Join(dataRoot, "columns", channel+"_merged.col")
\traw, err := os.ReadFile(path)
\tif err != nil {
\t\treturn 0, 0, err
\t}
\tvar stripe frame.ColumnStripe
\tif err := json.Unmarshal(raw, &stripe); err != nil {
\t\treturn 0, 0, err
\t}
\tcount := 0
\tvar sum int64
\tfor _, rec := range stripe.Records {
\t\tif rec.T <= ts {
\t\t\tcount++
\t\t\tsum += rec.T
\t\t}
\t}
\treturn count, sum, nil
}
"""

GO_MAIN = """package main

import (
\t"encoding/json"
\t"fmt"
\t"os"
\t"path/filepath"
\t"strconv"

\t"lab.local/hydro_lane/internal/k3"
\t"lab.local/hydro_lane/internal/m7"
)

func main() {
\tif len(os.Args) < 2 {
\t\tfmt.Fprintln(os.Stderr, "usage: window <head|aggregate>")
\t\tos.Exit(2)
\t}
\tdataRoot := "/app/data"
\tconfigDir := "/app/config/l7"
\tswitch os.Args[1] {
\tcase "head":
\t\tgen, err := m7.ResolveHead(filepath.Join(dataRoot, "manifests"), configDir)
\t\tif err != nil {
\t\t\tfmt.Fprintln(os.Stderr, err)
\t\t\tos.Exit(1)
\t\t}
\t\tfmt.Println(gen)
\tcase "aggregate":
\t\tvar channel string
\t\tvar ts int64
\t\tfor i := 2; i < len(os.Args); i++ {
\t\t\tswitch os.Args[i] {
\t\t\tcase "--ks":
\t\t\t\tif i+1 >= len(os.Args) {
\t\t\t\t\tos.Exit(2)
\t\t\t\t}
\t\t\t\tchannel = os.Args[i+1]
\t\t\t\ti++
\t\t\tcase "--ts":
\t\t\t\tif i+1 >= len(os.Args) {
\t\t\t\t\tos.Exit(2)
\t\t\t\t}
\t\t\t\tv, err := strconv.ParseInt(os.Args[i+1], 10, 64)
\t\t\t\tif err != nil {
\t\t\t\t\tos.Exit(2)
\t\t\t\t}
\t\t\t\tts = v
\t\t\t\ti++
\t\t\t}
\t\t}
\t\tif channel == "" || ts == 0 {
\t\t\tos.Exit(2)
\t\t}
\t\tcount, sum, err := k3.MergedAggregate(dataRoot, channel, ts)
\t\tif err != nil {
\t\t\tfmt.Fprintln(os.Stderr, err)
\t\t\tos.Exit(1)
\t\t}
\t\tout, _ := json.Marshal(map[string]any{"count": count, "sum_ts": sum})
\t\tfmt.Println(string(out))
\tdefault:
\t\tos.Exit(2)
\t}
}
"""

# Fix k3 export name
GO_K3 = GO_K3.replace("func mergedAggregate", "func MergedAggregate")

TEST_OUTPUTS = '''import json
import subprocess
from pathlib import Path

CTL = "/app/bin/ctl"
WINDOW = "/app/bin/window"
REPORT_PATH = Path("/output/backfill-report.json")
RUNTIME_PATH = Path("/app/data/state/runtime.json")
CFG = Path("/app/config/l7")
QUERY_TS = 550
TELEMETRY_TS = 100
PRIMARY = "events"
SECONDARY = "metrics"

# Frozen verifier baselines (not recomputed from agent-writable answers alone).
# Domain sample tokens also appear under /app/ops/fixtures/rating_samples.json.
_ANCHOR = 17
_STATIONS_SEGMENTS = 2
_TELEMETRY_SEGMENTS = 2


def _ctl_json(args: list[str]) -> dict:
    result = subprocess.run(
        [CTL, *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout.strip())


def _window_json(args: list[str]) -> dict:
    result = subprocess.run(
        [WINDOW, *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout.strip())


def _window_head() -> int:
    return int(
        subprocess.run([WINDOW, "head"], check=True, capture_output=True, text=True).stdout.strip()
    )


def _load_report() -> dict:
    assert REPORT_PATH.is_file(), "backfill report missing"
    return json.loads(REPORT_PATH.read_text())


def _load_runtime() -> dict:
    return json.loads(RUNTIME_PATH.read_text())


def _config_field(field: str):
    """Read a single field from whichever operator table defines it."""
    for path in sorted(CFG.glob("*.toml")):
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped.startswith(f"{field} ="):
                continue
            raw = stripped.split("=", 1)[1].strip()
            if raw.startswith("["):
                return json.loads(raw)
            if raw.startswith('"'):
                return json.loads(raw)
            if raw in ("true", "false"):
                return raw == "true"
            return int(raw)
    raise AssertionError(f"missing operator table field {field}")


def _discover_roll_anchor() -> int:
    """Last events generation in tier_b before the tainted stripe-99 cutover."""
    anchor = None
    for line in Path("/app/data/manifests/tier_b.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("ns") != "events":
            continue
        if 99 in rec.get("stripes", []):
            break
        anchor = int(rec["gen"])
    if anchor is None:
        raise AssertionError("could not derive roll anchor from tier_b journal")
    return anchor


def _manifest_stripes_at(ns: str, gen: int) -> list[int]:
    """Stripe list for a namespace at a journal generation."""
    entries: list[dict] = []
    for name in ("tier_a.jsonl", "tier_b.jsonl", "tier_c.jsonl"):
        path = Path(f"/app/data/manifests/{name}")
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            entries.append(json.loads(line))
    matching = [entry for entry in entries if entry.get("ns") == ns and int(entry["gen"]) <= gen]
    if not matching:
        raise AssertionError(f"no journal entry for {ns} gen {gen}")
    latest = max(matching, key=lambda entry: int(entry["gen"]))
    return [int(stripe) for stripe in latest["stripes"]]


def _stripe_col_path(ns: str, stripe_id: int) -> Path:
    if stripe_id == 99:
        return Path(f"/app/data/columns/{ns}_merged.col")
    return Path(f"/app/data/columns/{ns}_{stripe_id:03}.col")


def _sha256_stripe_bytes(paths: list[Path]) -> str:
    """SHA256 hex over concatenated raw stripe file bytes in manifest order."""
    blob = b"".join(path.read_bytes() for path in paths)
    result = subprocess.run(
        ["openssl", "dgst", "-sha256"],
        input=blob,
        check=True,
        capture_output=True,
    )
    return result.stdout.decode().strip().split("= ", 1)[1].replace(":", "").strip()


def _expected_sidecar_digest(ns: str, anchor: int) -> str:
    stripes = _manifest_stripes_at(ns, anchor)
    paths = [_stripe_col_path(ns, stripe_id) for stripe_id in stripes]
    return _sha256_stripe_bytes(paths)


def _expected_sidecar_map(ns: str, anchor: int, tombstone_keys: set[str]) -> dict[str, int]:
    """Key-to-stripe map after rebuild, excluding applied tombstones."""
    runtime = _load_runtime()
    wal_seq = int(runtime.get("wal_seq", 0))
    tombstone_seq = int(runtime.get("tombstone_seq", 0))
    mapping: dict[str, int] = {}
    for stripe_id in _manifest_stripes_at(ns, anchor):
        stripe = json.loads(_stripe_col_path(ns, stripe_id).read_text())
        stripe_num = int(stripe["id"])
        for row in stripe["records"]:
            key = row["k"]
            if key in tombstone_keys and wal_seq >= tombstone_seq and tombstone_seq > 0:
                continue
            mapping[key] = stripe_num
    return mapping


def _discover_barrier_cutoff() -> tuple[int, str]:
    """WAL sequence and tombstoned key at the barrier cutoff fixture."""
    tombstone_seq = None
    tombstone_key = None
    for name in ("seg_001.bin", "seg_002.bin"):
        blob = (Path("/app/data/wal") / name).read_bytes()
        if blob[:4] != b"WLOG":
            raise AssertionError(f"bad wal magic in {name}")
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
            if op == 1:
                tombstone_seq = seq
                tombstone_key = key
    if tombstone_seq is None or tombstone_key is None:
        raise AssertionError("could not locate tombstone cutoff in wal segments")
    return tombstone_seq, tombstone_key


def test_fixture_vector_alpha():
    """Primary gauge keys resolve to expected payloads at the query timestamp."""
    got_alpha = _ctl_json(["query", "point", "--ks", PRIMARY, "--key", "alpha", "--ts", str(QUERY_TS)])
    got_beta = _ctl_json(["query", "point", "--ks", PRIMARY, "--key", "beta", "--ts", str(QUERY_TS)])
    got_gamma = _ctl_json(["query", "point", "--ks", PRIMARY, "--key", "gamma", "--ts", str(QUERY_TS)])

    assert got_alpha["found"] is True
    assert got_alpha["value"] == "payload_a"
    assert got_alpha["ts"] == 100

    assert got_beta["found"] is True
    assert got_beta["value"] == "payload_b"

    assert got_gamma["found"] is True
    assert got_gamma["value"] == "payload_c"


def test_fixture_vector_beta():
    """Range scan returns keys in sorted order with stable payload values."""
    payload = _ctl_json(
        [
            "query",
            "range",
            "--ks",
            PRIMARY,
            "--lo",
            "alpha",
            "--hi",
            "gamma",
            "--ts",
            str(QUERY_TS),
        ]
    )
    keys = [hit["key"] for hit in payload["hits"]]
    assert keys == ["alpha", "beta", "gamma"]
    values = [hit["value"] for hit in payload["hits"]]
    assert values == ["payload_a", "payload_b", "payload_c"]


def test_absent_marker_at_window():
    """Tombstoned gauge marker stays absent for the queried time window."""
    wal_cutoff, tombstone_key = _discover_barrier_cutoff()
    config_cutoff = _config_field("seq_cutoff")
    payload = _ctl_json(
        ["query", "point", "--ks", PRIMARY, "--key", tombstone_key, "--ts", str(QUERY_TS)]
    )
    assert payload["found"] is False
    runtime = _load_runtime()
    assert config_cutoff >= wal_cutoff
    assert runtime["tombstone_seq"] == config_cutoff


def test_aggregate_totals_stable():
    """Channel aggregate totals match the frozen stage-sum baseline at the query window."""
    payload = _ctl_json(["query", "aggregate", "--ks", PRIMARY, "--ts", str(QUERY_TS)])
    assert payload["count"] == 3
    assert payload["sum_ts"] == 600


def test_basin_window_aggregate_alignment():
    """Basin-window lane totals agree with numerical rollup probes at the query epoch."""
    ctl = _ctl_json(["query", "aggregate", "--ks", PRIMARY, "--ts", str(QUERY_TS)])
    basin = _window_json(["aggregate", "--ks", PRIMARY, "--ts", str(QUERY_TS)])
    assert basin["count"] == 3
    assert basin["sum_ts"] == 600
    assert ctl["count"] == basin["count"]
    assert ctl["sum_ts"] == basin["sum_ts"]


def test_basin_window_head_alignment():
    """Basin-window head matches the restored generation reported by ctl."""
    head = _window_head()
    report = _load_report()
    assert head == report["restored_generation"]
    assert head == _ANCHOR
    assert head == _discover_roll_anchor()


def test_output_json_schema_valid():
    """Backfill report JSON exposes required fields with valid types and values."""
    payload = _load_report()

    assert isinstance(payload.get("restored_generation"), int)
    for ns in ("stations", "telemetry"):
        block = payload.get(ns)
        assert isinstance(block, dict)
        assert isinstance(block.get("visible_segments"), int)
        digest = block.get("sidecar_digest")
        assert isinstance(digest, str)
        assert len(digest) >= 16
        int(digest, 16)

    status = _ctl_json(["status"])
    assert 0 < payload["restored_generation"] <= status["ceiling_gen"]
    assert payload["restored_generation"] == _ANCHOR


def test_report_visible_segments_match_journal():
    """Report visible_segments match the frozen stripe counts at the restored generation."""
    payload = _load_report()
    assert payload["restored_generation"] == _ANCHOR
    assert payload["stations"]["visible_segments"] == _STATIONS_SEGMENTS
    assert payload["telemetry"]["visible_segments"] == _TELEMETRY_SEGMENTS
    assert payload["stations"]["visible_segments"] == len(
        _manifest_stripes_at(PRIMARY, _discover_roll_anchor())
    )


def test_chain_order_invariant():
    """Restored report generation stays at or below the ctl status ceiling."""
    status = _ctl_json(["status"])
    runtime = _load_runtime()
    payload = _load_report()
    restored = payload["restored_generation"]
    anchor = _discover_roll_anchor()

    assert 0 < restored <= status["ceiling_gen"]
    assert restored == _ANCHOR
    assert restored == runtime["active_gen"]
    assert runtime["active_gen"] == anchor
    assert payload["stations"]["visible_segments"] == _STATIONS_SEGMENTS
    assert payload["telemetry"]["visible_segments"] == _TELEMETRY_SEGMENTS


def test_barrier_tombstone_runtime_state():
    """Barrier replay committed tombstone state tied to the WAL cutoff fixture."""
    runtime = _load_runtime()
    wal_cutoff, tombstone_key = _discover_barrier_cutoff()
    config_cutoff = _config_field("seq_cutoff")

    assert config_cutoff >= wal_cutoff
    assert runtime["tombstone_seq"] == config_cutoff
    assert runtime["wal_seq"] >= wal_cutoff
    assert tombstone_key in runtime["tombstone_keys"]

    point = _ctl_json(
        ["query", "point", "--ks", PRIMARY, "--key", tombstone_key, "--ts", str(QUERY_TS)]
    )
    assert point["found"] is False

    scanned = _ctl_json(
        [
            "query",
            "range",
            "--ks",
            PRIMARY,
            "--lo",
            tombstone_key,
            "--hi",
            tombstone_key,
            "--ts",
            str(QUERY_TS),
        ]
    )
    keys = [hit["key"] for hit in scanned["hits"]]
    assert tombstone_key not in keys

    aggregate = _ctl_json(["query", "aggregate", "--ks", PRIMARY, "--ts", str(QUERY_TS)])
    assert aggregate["count"] == 3


def test_recovery_config_anchors():
    """Recovered generation anchors agree across report, window head, runtime, and status."""
    status = _ctl_json(["status"])
    report = _load_report()
    head = _window_head()
    runtime = _load_runtime()
    anchor = _discover_roll_anchor()

    assert report["restored_generation"] == _ANCHOR
    assert head == _ANCHOR
    assert runtime["active_gen"] == anchor
    assert _config_field("tier_c") == anchor
    assert 0 < report["restored_generation"] <= status["ceiling_gen"]


def test_rebuild_generation_alignment():
    """Rebuilt events sidecar is bound to the rolled generation with a full key map."""
    runtime = _load_runtime()
    anchor = _discover_roll_anchor()
    _cutoff, tombstone_key = _discover_barrier_cutoff()
    sidecar = json.loads(Path("/app/data/sidecars/events.idx").read_text())
    expected_map = _expected_sidecar_map(PRIMARY, anchor, {tombstone_key})
    report = _load_report()

    assert report["restored_generation"] == _ANCHOR
    assert runtime["active_gen"] == anchor
    assert sidecar["bound_gen"] == anchor
    assert runtime["sidecar_gen"]["events"] == anchor
    assert sidecar["map"] == expected_map
    assert tombstone_key not in sidecar["map"]


def test_digest_checksum_match():
    """Events sidecar digest matches stripe SHA256 and the report stations entry."""
    anchor = _discover_roll_anchor()
    runtime = _load_runtime()
    assert runtime["active_gen"] == anchor
    payload = _load_report()
    sidecar = json.loads(Path("/app/data/sidecars/events.idx").read_text())
    expected = _expected_sidecar_digest(PRIMARY, anchor)

    assert sidecar["bound_gen"] == anchor
    assert sidecar["digest"] == expected
    assert payload["stations"]["sidecar_digest"] == expected
    assert payload["stations"]["sidecar_digest"] == sidecar["digest"]


def test_secondary_namespace_stable():
    """Unaffected telemetry channel probes remain at baseline; report digest matches sidecar."""
    point = _ctl_json(["query", "point", "--ks", SECONDARY, "--key", "m1", "--ts", str(TELEMETRY_TS)])
    agg = _ctl_json(["query", "aggregate", "--ks", SECONDARY, "--ts", str(TELEMETRY_TS)])

    assert point["found"] is True
    assert point["key"] == "m1"
    assert point["value"] == "metric_one"
    assert point["ts"] == 50

    assert agg["count"] == 3
    assert agg["sum_ts"] == 215

    report = _load_report()
    metrics_sidecar = json.loads(Path("/app/data/sidecars/metrics.idx").read_text())
    assert metrics_sidecar["bound_gen"] < _ANCHOR
    assert report["telemetry"]["visible_segments"] == _TELEMETRY_SEGMENTS
    assert report["telemetry"]["sidecar_digest"] == metrics_sidecar["digest"]


def test_prebuilt_runtime_binaries():
    """Recovery relies on prebuilt ctl and window binaries without rebuilding /app/store or /app/lane."""
    for path in ("/app/bin/ctl", "/app/bin/window"):
        payload = Path(path).read_bytes()
        assert payload[:4] == b"\x7fELF", f"{path} must remain a shipped binary"
    assert Path("/app/store/Cargo.toml").is_file()
    assert Path("/app/lane/go.mod").is_file()
'''
SOLVE_SH = r"""#!/bin/bash
set -euo pipefail

test -d /app/config/l7
test -x /app/bin/ctl
test -x /app/bin/window
mkdir -p /output /app/ops/staging

# Discover anchor generation from tier_b journal manifest: iterate the events
# records in order and keep the last gen whose stripe set does not include
# the tainted stripe 99.
discover_anchor() {
    awk '
        /"ns":[[:space:]]*"events"/ {
            stripes_field = ""
            if (match($0, /"stripes":[[:space:]]*\[[^]]*\]/)) {
                stripes_field = substr($0, RSTART, RLENGTH)
            }
            if (stripes_field ~ /(^|[^0-9])99([^0-9]|$)/) { exit }
            if (match($0, /"gen":[[:space:]]*[0-9]+/)) {
                gen_field = substr($0, RSTART, RLENGTH)
                gsub(/[^0-9]/, "", gen_field)
                anchor = gen_field
            }
        }
        END {
            if (anchor == "") { exit 1 }
            print anchor
        }
    ' /app/data/manifests/tier_b.jsonl
}

# Scan a WAL segment binary and print the sequence number of any tombstone
# (op == 1) entry whose key equals marker_zulu. Record layout after the
# 4-byte "WLOG" magic:
#   seq  : u64 little-endian
#   op   : u8
#   klen : u16 little-endian
#   key  : klen bytes
#   val  : 8 bytes
scan_wal_segment() {
    local file="$1"
    local size magic off op key_len key seq
    size=$(stat -c%s "$file")
    magic=$(dd if="$file" bs=1 count=4 status=none)
    if [ "$magic" != "WLOG" ]; then
        echo "bad wal magic in $file" >&2
        return 1
    fi
    off=4
    while [ $((off + 11)) -le "$size" ]; do
        seq=$(od -An -j"$off" -N8 --endian=little -tu8 "$file" | tr -d ' \n')
        off=$((off + 8))
        op=$(od -An -j"$off" -N1 -tu1 "$file" | tr -d ' \n')
        off=$((off + 1))
        key_len=$(od -An -j"$off" -N2 --endian=little -tu2 "$file" | tr -d ' \n')
        off=$((off + 2))
        if [ "$key_len" -gt 0 ]; then
            key=$(dd if="$file" bs=1 skip="$off" count="$key_len" status=none)
        else
            key=""
        fi
        off=$((off + key_len + 8))
        if [ "$op" = "1" ] && [ "$key" = "marker_zulu" ]; then
            echo "$seq"
        fi
    done
}

discover_barrier() {
    local hit=""
    local candidate
    for name in seg_001.bin seg_002.bin; do
        candidate=$(scan_wal_segment "/app/data/wal/$name" | tail -n1)
        if [ -n "$candidate" ]; then
            hit="$candidate"
        fi
    done
    if [ -z "$hit" ]; then
        echo "could not locate tombstone cutoff in wal segments" >&2
        return 1
    fi
    echo "$hit"
}

anchor_gen=$(discover_anchor)
barrier_cutoff=$(discover_barrier)

sed -i "s/^tier_c = .*/tier_c = ${anchor_gen}/" /app/config/l7/k9.toml
sed -i "s/^journal_pin = .*/journal_pin = ${anchor_gen}/" /app/config/l7/k9.toml
sed -i "s/^head_floor = .*/head_floor = ${anchor_gen}/" /app/config/l7/k9.toml
sed -i 's/^roll_ready = .*/roll_ready = true/' /app/config/l7/k9.toml
sed -i 's/^audit_stamp = .*/audit_stamp = "applied"/' /app/config/l7/k9.toml
sed -i 's/^sync_token = .*/sync_token = "armed"/' /app/config/l7/k9.toml

sed -i "s/^seq_cutoff = .*/seq_cutoff = ${barrier_cutoff}/" /app/config/l7/m2.toml
sed -i "s/^wal_floor = .*/wal_floor = ${barrier_cutoff}/" /app/config/l7/m2.toml
sed -i 's/^scan_tier = .*/scan_tier = "b"/' /app/config/l7/m2.toml
sed -i 's/^barrier_live = .*/barrier_live = true/' /app/config/l7/m2.toml
sed -i 's/^replay_gate = .*/replay_gate = 0/' /app/config/l7/m2.toml
sed -i 's/^tomb_scan = .*/tomb_scan = true/' /app/config/l7/m2.toml

# Optional operator log sync for ctl workflow; individual roll/barrier/rebuild
# do not require this table, and the verifier does not grade phases order.
sed -i 's/^phases = .*/phases = ["roll", "barrier", "rebuild"]/' /app/config/l7/p7.toml
sed -i 's/^strict_chain = .*/strict_chain = true/' /app/config/l7/p7.toml
sed -i 's/^allow_batch = .*/allow_batch = false/' /app/config/l7/p7.toml
sed -i 's/^workflow_note = .*/workflow_note = "live"/' /app/config/l7/p7.toml

grep -q "^tier_c = ${anchor_gen}$" /app/config/l7/k9.toml
grep -q "^seq_cutoff = ${barrier_cutoff}$" /app/config/l7/m2.toml

/app/bin/ctl roll --ks events
/app/bin/ctl barrier
/app/bin/ctl rebuild --ks events

/app/bin/ctl report --out /output/backfill-report.json

probe_alpha=$(/app/bin/ctl query point --ks events --key alpha --ts 550)
probe_marker=$(/app/bin/ctl query point --ks events --key marker_zulu --ts 550)
echo "${probe_alpha}" | grep -q '"found":true'
echo "${probe_marker}" | grep -q '"found":false'

window_head=$(/app/bin/window head)
test "${window_head}" -eq "${anchor_gen}"

status_json=$(/app/bin/ctl status)
restored_gen=$(awk 'match($0, /"restored_generation":[[:space:]]*[0-9]+/) { s=substr($0, RSTART, RLENGTH); gsub(/[^0-9]/, "", s); print s; exit }' /output/backfill-report.json)
ceiling_gen=$(printf '%s' "$status_json" | awk 'match($0, /"ceiling_gen":[[:space:]]*[0-9]+/) { s=substr($0, RSTART, RLENGTH); gsub(/[^0-9]/, "", s); print s; exit }')
test "${restored_gen}" -le "${ceiling_gen}"

echo "complete" > /app/ops/staging/workflow.complete
"""


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip("\n"))


def patch_ctl_report() -> None:
    """Map events/metrics report keys to stations/telemetry for hydrology contract."""
    report_path = TASK / "environment" / "store" / "ctl" / "src" / "main.rs"
    if not report_path.exists():
        return
    text = report_path.read_text()
    text = text.replace(
        """#[derive(Serialize)]
struct RewindReport {
    restored_generation: u64,
    events: NamespaceReport,
    metrics: NamespaceReport,
}""",
        """#[derive(Serialize)]
struct RewindReport {
    restored_generation: u64,
    #[serde(rename = "stations")]
    events: NamespaceReport,
    #[serde(rename = "telemetry")]
    metrics: NamespaceReport,
}""",
    )
    report_path.write_text(text)


def write_go_lane() -> None:
    lane = TASK / "environment" / "lane"
    w(lane / "go.mod", GO_MOD)
    w(lane / "go.sum", "")
    w(lane / "pkg" / "frame" / "row.go", GO_FRAME)
    w(lane / "internal" / "cfg" / "load.go", GO_CFG)
    w(lane / "internal" / "m7" / "head.go", GO_M7)
    w(lane / "internal" / "k3" / "aggregate.go", GO_K3)
    w(lane / "cmd" / "window" / "main.go", GO_MAIN)


def patch_broken_config() -> None:
    m2 = TASK / "environment" / "config" / "l7" / "m2.toml"
    text = m2.read_text()
    if "scan_tier" not in text:
        m2.write_text('scan_tier = "c"\n' + text)


def main() -> None:
    if not REF.is_dir():
        raise SystemExit(f"missing reference tree: {REF}")

    if TASK.exists():
        shutil.rmtree(TASK)

    shutil.copytree(REF, TASK, ignore=shutil.ignore_patterns(".DS_Store"))

    w(TASK / "instruction.md", INSTRUCTION)
    w(TASK / "task.toml", TASK_TOML)
    w(TASK / "output_contract.toml", OUTPUT_CONTRACT)
    w(TASK / "environment" / "ops" / "runbooks" / "ctl_usage.md", RUNBOOK)
    w(TASK / "environment" / "ops" / "runbooks" / "hydrology_model.md", HYDROLOGY_MODEL)
    w(TASK / "environment" / "Dockerfile", DOCKERFILE)
    w(TASK / "environment" / ".dockerignore", DOCKERIGNORE)
    w(TASK / "tests" / "test_outputs.py", TEST_OUTPUTS)
    w(TASK / "solution" / "solve.sh", SOLVE_SH)
    w(
        TASK / "tests" / "test.sh",
        """#!/bin/bash

# Verifier dependencies are installed in environment/Dockerfile.

mkdir -p /logs/verifier

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
    echo 0 > /logs/verifier/reward.txt
    exit 1
fi

python -m pytest -o cache_dir=/tmp/pytest_cache \\
  --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA

if [ $? -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
""",
    )

    write_go_lane()
    patch_broken_config()
    patch_ctl_report()

    env_files = sum(1 for p in (TASK / "environment").rglob("*") if p.is_file())
    print(f"generated {TASK} ({env_files} environment files)")


if __name__ == "__main__":
    main()
