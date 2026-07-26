#!/usr/bin/env python3
"""One-shot generator for tasks/merkle-sync-branch-lag (authoring tool, not shipped)."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "merkle-sync-branch-lag"
REPORT_NAME = "sync-report.json"

CANONICAL_GOLANG = (
    "public.ecr.aws/docker/library/golang:1.24-bookworm"
    "@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac"
)
CANONICAL_RUST = (
    "public.ecr.aws/docker/library/rust:1.85-slim"
    "@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36"
)

LEAVES = [
    {"id": "alpha", "payload": "pa1", "since": 1},
    {"id": "beta", "payload": "pb1", "since": 1},
    {"id": "gamma", "payload": "pg2", "since": 2},
    {"id": "delta", "payload": "pd3", "since": 3},
]

JOURNAL_ROWS = [
    {"tier": "a", "gen": 1, "tip": "t1"},
    {"tier": "a", "gen": 2, "tip": "t2"},
    {"tier": "b", "gen": 2, "tip": "t2b"},
    {"tier": "c", "gen": 3, "tip": "t3"},
]

HEAD_GEN = 3
STALE_GEN = 2


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def canonical_leaf_body(leaf_id: str, payload: str) -> str:
    return json.dumps({"id": leaf_id, "payload": payload}, separators=(",", ":"), sort_keys=True)


def leaf_digest(leaf_id: str, payload: str) -> str:
    return hashlib.sha256(canonical_leaf_body(leaf_id, payload).encode()).hexdigest()


def visible_leaves(branch: int) -> list[dict]:
    rows = [row for row in LEAVES if row["since"] <= branch]
    return sorted(rows, key=lambda r: r["id"])


def merkle_root(branch: int) -> str:
    digests = [leaf_digest(r["id"], r["payload"]) for r in visible_leaves(branch)]
    if not digests:
        return hashlib.sha256(b"").hexdigest()
    layer = digests[:]
    while len(layer) > 1:
        nxt: list[str] = []
        idx = 0
        while idx < len(layer):
            left = layer[idx]
            right = layer[idx + 1] if idx + 1 < len(layer) else left
            pair = bytes.fromhex(left) + bytes.fromhex(right)
            nxt.append(hashlib.sha256(pair).hexdigest())
            idx += 2
        layer = nxt
    return layer[0]


def leaf_map(branch: int) -> dict[str, str]:
    return {r["id"]: leaf_digest(r["id"], r["payload"]) for r in visible_leaves(branch)}


def write_fixtures() -> None:
    data = TASK / "environment" / "data"
    for row in LEAVES:
        w(data / "leaves" / f"{row['id']}.json", json.dumps(row, indent=2) + "\n")

    for tier in ("a", "b", "c"):
        lines = [json.dumps(r) for r in JOURNAL_ROWS if r["tier"] == tier]
        w(data / "journal" / f"tier_{tier}.jsonl", "\n".join(lines) + ("\n" if lines else ""))

    w(
        data / "state" / "runtime.json",
        json.dumps(
            {
                "active_gen": HEAD_GEN,
                "last_sync_gen": STALE_GEN,
                "journal_head": HEAD_GEN,
            },
            indent=2,
        )
        + "\n",
    )


def write_config() -> None:
    cfg = TASK / "environment" / "config" / "l7"
    w(
        cfg / "k9.toml",
        f"""branch_cap = {STALE_GEN}
journal_pin = {STALE_GEN}
head_floor = {STALE_GEN}
sync_ready = false
audit_stamp = "pending"
""",
    )
    w(
        cfg / "m2.toml",
        """scan_tier = "b"
replay_gate = 1
barrier_live = false
tomb_scan = false
""",
    )
    w(
        cfg / "p7.toml",
        """phases = ["scan", "bind", "emit"]
strict_chain = false
allow_batch = true
workflow_note = "idle"
""",
    )


def write_go_lane() -> None:
    lane = TASK / "environment" / "lane"
    w(
        lane / "go.mod",
        """module lab.local/sync_lane

go 1.22
""",
    )
    w(lane / "go.sum", "")
    w(
        lane / "pkg" / "frame" / "row.go",
        """package frame

type JournalRow struct {
\tGen uint64 `json:"gen"`
\tTip string `json:"tip"`
}

type LeafBlock struct {
\tDigest string `json:"digest"`
}

type SummaryDoc struct {
\tBranchGen uint64            `json:"branch_gen"`
\tRootDigest string           `json:"root_digest"`
\tLeaves     map[string]string `json:"leaves"`
}
""",
    )
    w(
        lane / "internal" / "m7" / "head.go",
        """package m7

import (
\t"bufio"
\t"encoding/json"
\t"os"
\t"path/filepath"
\t"strings"

\t"lab.local/sync_lane/pkg/frame"
)

func pickTier(configDir string) string {
\t_, err := os.ReadFile(filepath.Join(configDir, "m2.toml"))
\tif err != nil {
\t\treturn "b"
\t}
\treturn "b"
}

// ResolveHead returns the generation the checkpoint lane treats as current.
func ResolveHead(journalDir string) (uint64, error) {
\ttier := pickTier("/app/config/l7")
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
\t_ = strings.TrimSpace
\treturn head, nil
}
""",
    )
    w(
        lane / "internal" / "k3" / "anchor.go",
        """package k3

import (
\t"bufio"
\t"encoding/json"
\t"os"
\t"path/filepath"

\t"lab.local/sync_lane/pkg/frame"
)

// ScanTierA walks tier_a for a standalone anchor helper not wired into emit.
func ScanTierA(journalDir string) (uint64, error) {
\tpath := filepath.Join(journalDir, "tier_a.jsonl")
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
\treturn head, scan.Err()
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

\t"lab.local/sync_lane/pkg/frame"
)

func WriteSummary(outPath, dataRoot string) error {
\tgen, err := ResolveHead(filepath.Join(dataRoot, "journal"))
\tif err != nil {
\t\treturn err
\t}
\troot, leaves, err := readTreeSnapshot(dataRoot, gen)
\tif err != nil {
\t\treturn err
\t}
\tdoc := frame.SummaryDoc{
\t\tBranchGen:  gen,
\t\tRootDigest: root,
\t\tLeaves:     leaves,
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

func readTreeSnapshot(dataRoot string, gen uint64) (string, map[string]string, error) {
\traw, err := os.ReadFile(filepath.Join(dataRoot, "state", "runtime.json"))
\tif err != nil {
\t\treturn "", nil, err
\t}
\tvar rt struct {
\t\tLastSyncGen uint64 `json:"last_sync_gen"`
\t}
\tif err := json.Unmarshal(raw, &rt); err != nil {
\t\treturn "", nil, err
\t}
\t_ = gen
\treturn buildAt(dataRoot, rt.LastSyncGen)
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

\t"lab.local/sync_lane/internal/m7"
)

func main() {
\tif len(os.Args) < 2 {
\t\tlog.Fatal("usage: lane head|emit")
\t}
\tswitch os.Args[1] {
\tcase "head":
\t\tgen, err := m7.ResolveHead("/app/data/journal")
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
\t\tif err := m7.WriteSummary(*out, "/app/data"); err != nil {
\t\t\tlog.Fatal(err)
\t\t}
\tdefault:
\t\tlog.Fatalf("unknown subcommand %q", os.Args[1])
\t}
}
""",
    )


def write_rust_tree() -> None:
    tree = TASK / "environment" / "tree"
    w(
        tree / "Cargo.toml",
        """[workspace]
members = ["syncctl", "core"]
resolver = "2"

[workspace.package]
edition = "2021"
""",
    )
    w(tree / "Cargo.lock", "")
    w(
        tree / "core" / "Cargo.toml",
        """[package]
name = "core"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
sha2 = "0.10"
hex = "0.4"
""",
    )
    w(
        tree / "core" / "src" / "lib.rs",
        """use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize)]
pub struct LeafRow {
    pub id: String,
    pub payload: String,
    pub since: u64,
}

#[derive(Debug, Deserialize)]
pub struct RuntimeState {
    pub active_gen: u64,
    pub last_sync_gen: u64,
    pub journal_head: u64,
}

#[derive(Debug, Serialize)]
pub struct SyncReport {
    pub branch_gen: u64,
    pub root_digest: String,
    pub leaves: BTreeMap<String, String>,
}

pub fn canonical_leaf(id: &str, payload: &str) -> String {
    format!(r#"{{"id":"{id}","payload":"{payload}"}}"#)
}

pub fn leaf_hash(id: &str, payload: &str) -> String {
    let body = canonical_leaf(id, payload);
    let mut h = Sha256::new();
    h.update(body.as_bytes());
    hex::encode(h.finalize())
}

pub fn load_leaves(dir: &Path) -> std::io::Result<Vec<LeafRow>> {
    let mut rows = Vec::new();
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        if !entry.path().extension().map(|e| e == "json").unwrap_or(false) {
            continue;
        }
        let raw = fs::read_to_string(entry.path())?;
        let row: LeafRow = serde_json::from_str(&raw)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
        rows.push(row);
    }
    rows.sort_by(|a, b| a.id.cmp(&b.id));
    Ok(rows)
}

pub fn visible_at(rows: &[LeafRow], branch: u64) -> BTreeMap<String, String> {
    let mut out = BTreeMap::new();
    for row in rows {
        if row.since <= branch {
            out.insert(row.id.clone(), leaf_hash(&row.id, &row.payload));
        }
    }
    out
}

pub fn merkle_root(leaves: &BTreeMap<String, String>) -> String {
    let mut layer: Vec<String> = leaves.values().cloned().collect();
    if layer.is_empty() {
        let mut h = Sha256::new();
        return hex::encode(h.finalize());
    }
    while layer.len() > 1 {
        let mut next = Vec::new();
        let mut idx = 0;
        while idx < layer.len() {
            let left = &layer[idx];
            let right = if idx + 1 < layer.len() {
                &layer[idx + 1]
            } else {
                &layer[idx]
            };
            let left_bytes = hex::decode(left).unwrap_or_default();
            let right_bytes = hex::decode(right).unwrap_or_default();
            let mut h = Sha256::new();
            h.update(&left_bytes);
            h.update(&right_bytes);
            next.push(hex::encode(h.finalize()));
            idx += 2;
        }
        layer = next;
    }
    layer[0].clone()
}

pub fn read_runtime(path: &Path) -> std::io::Result<RuntimeState> {
    let raw = fs::read_to_string(path)?;
    Ok(serde_json::from_str(&raw)?)
}

pub fn read_branch_cap(config_dir: &Path) -> std::io::Result<u64> {
    let path = config_dir.join("k9.toml");
    let raw = fs::read_to_string(path)?;
    for line in raw.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("branch_cap") {
            let rhs = trimmed.split('=').nth(1).unwrap_or("0").trim();
            return Ok(rhs.parse().unwrap_or(0));
        }
    }
    Ok(0)
}

pub fn branch_cut(state: &RuntimeState, cap: u64) -> u64 {
    let mut g = state.last_sync_gen;
    if cap > 0 && cap < g {
        g = cap;
    }
    if g > state.active_gen {
        g = state.active_gen;
    }
    g
}

pub fn build_report(data_root: &Path, config_dir: &Path) -> std::io::Result<SyncReport> {
    let leaves_dir = data_root.join("leaves");
    let runtime = read_runtime(&data_root.join("state/runtime.json"))?;
    let cap = read_branch_cap(config_dir)?;
    let branch = branch_cut(&runtime, cap);
    let rows = load_leaves(&leaves_dir)?;
    let leaf_map = visible_at(&rows, branch);
    let root = merkle_root(&leaf_map);
    Ok(SyncReport {
        branch_gen: branch,
        root_digest: root,
        leaves: leaf_map,
    })
}
""",
    )
    w(
        tree / "syncctl" / "Cargo.toml",
        """[package]
name = "syncctl"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "syncctl"
path = "src/main.rs"

[dependencies]
core = { path = "../core" }
serde_json = "1"
clap = { version = "4", features = ["derive"] }
""",
    )
    w(
        tree / "syncctl" / "src" / "main.rs",
        """use clap::{Parser, Subcommand};
use core::build_report;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Parser)]
#[command(name = "syncctl")]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Status,
    Report {
        #[arg(long)]
        out: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    match cli.cmd {
        Commands::Status => {
            let report = build_report(Path::new("/app/data"), Path::new("/app/config/l7"))
                .expect("status");
            println!("{{\\\"branch_gen\\\":{}}}", report.branch_gen);
        }
        Commands::Report { out } => {
            let report = build_report(Path::new("/app/data"), Path::new("/app/config/l7"))
                .expect("report");
            let payload = serde_json::to_string_pretty(&report).expect("json");
            fs::write(&out, format!("{payload}\\n")).expect("write");
        }
    }
}
""",
    )


def write_digest_lab() -> None:
    w(
        TASK / "environment" / "ops" / "scripts" / "digest_lab.py",
        '''#!/usr/bin/env python3
"""Reference digest helper for leaf fixtures (uses same SHA-256 rules as syncctl)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def canonical_body(leaf_id: str, payload: str) -> str:
    return json.dumps({"id": leaf_id, "payload": payload}, separators=(",", ":"), sort_keys=True)


def leaf_digest(leaf_id: str, payload: str) -> str:
    return hashlib.sha256(canonical_body(leaf_id, payload).encode()).hexdigest()


def visible(branch: int, leaves_dir: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(leaves_dir.glob("*.json")):
        row = json.loads(path.read_text())
        if int(row["since"]) <= branch:
            out[row["id"]] = leaf_digest(row["id"], row["payload"])
    return out


def merkle_root(leaves: dict[str, str]) -> str:
    layer = list(leaves.values())
    if not layer:
        return hashlib.sha256(b"").hexdigest()
    while len(layer) > 1:
        nxt: list[str] = []
        idx = 0
        while idx < len(layer):
            left = bytes.fromhex(layer[idx])
            right = bytes.fromhex(layer[idx + 1] if idx + 1 < len(layer) else layer[idx])
            nxt.append(hashlib.sha256(left + right).hexdigest())
            idx += 2
        layer = nxt
    return layer[0]


def main() -> None:
    branch = int(sys.argv[1])
    leaves_dir = Path("/app/data/leaves")
    leaf_map = visible(branch, leaves_dir)
    payload = {"branch": branch, "root_digest": merkle_root(leaf_map), "leaves": leaf_map}
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
''',
    )


def write_runbook() -> None:
    w(
        TASK / "environment" / "ops" / "runbooks" / "sync_usage.md",
        """# sync operator reference

Leaf payloads live under `/app/data/leaves/` as JSON objects with `id`, `payload`, and `since` fields.
Journal tiers under `/app/data/journal/` record promoted generations. Runtime state is under `/app/data/state/runtime.json`.
Operator tables under `/app/config/l7/` are TOML files read at runtime by the lane and sync tools.

Rebuild `/app/bin/lane` from `/app/lane/` and `/app/bin/syncctl` from `/app/tree/`.

## Commands

`syncctl report --out PATH` writes a JSON object with integer `branch_gen`, hex string `root_digest`, and a `leaves` map of leaf id to hex digest.
`lane head` prints the checkpoint generation the lane module selects.
`/app/ops/scripts/digest_lab.py BRANCH` prints fixture-derived leaf and root digests for a branch generation.
""",
    )


def write_dockerfile() -> None:
    w(
        TASK / "environment" / "Dockerfile",
        f"""# syntax=docker/dockerfile:1

FROM {CANONICAL_GOLANG} AS gobuilder

WORKDIR /build/lane
COPY lane/go.mod lane/go.sum ./
RUN go mod download
COPY lane/pkg/ pkg/
COPY lane/internal/ internal/
COPY lane/cmd/ cmd/
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/lane ./cmd/lane

FROM {CANONICAL_RUST} AS rsbuilder

WORKDIR /build/tree
COPY tree/Cargo.toml tree/Cargo.lock ./
COPY tree/core/Cargo.toml core/
COPY tree/syncctl/Cargo.toml syncctl/
COPY tree/core/src/ core/src/
COPY tree/syncctl/src/ syncctl/src/
RUN cargo generate-lockfile && cargo build --release --locked -p syncctl

FROM {CANONICAL_GOLANG}

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before any other setup.
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        tmux=3.3a-3 \\
        asciinema=2.2.0-1 \\
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V && asciinema --version

RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        bash \\
        ca-certificates=20230311+deb12u1 \\
        libutempter0 \\
        procps \\
        python3=3.11.2-1+b1 \\
        python3-pip=23.0.1+dfsg-1 \\
        python-is-python3 \\
    && rm -rf /var/lib/apt/lists/*

ENV GOPATH=/go \\
    GOCACHE=/tmp/go-cache \\
    GOMODCACHE=/go/pkg/mod \\
    GOPROXY=off \\
    RUSTUP_HOME=/usr/local/rustup \\
    CARGO_HOME=/usr/local/cargo

RUN mkdir -p /go /tmp/go-cache

RUN pip3 install --no-cache-dir --break-system-packages \\
    pytest==8.4.1 \\
    pytest-json-ctrf==0.3.5

COPY --from=rsbuilder /usr/local/rustup /usr/local/rustup
COPY --from=rsbuilder /usr/local/cargo /usr/local/cargo
COPY --from=rsbuilder /build/tree/target /app/tree/target
COPY --from=gobuilder --chmod=755 /out/lane /app/bin/lane
COPY --from=rsbuilder --chmod=755 /build/tree/target/release/syncctl /app/bin/syncctl
COPY config/ /app/config/
COPY data/ /app/data/
COPY lane/ /app/lane/
COPY tree/ /app/tree/
COPY --from=rsbuilder /build/tree/Cargo.lock /app/tree/Cargo.lock
COPY ops/ /app/ops/

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux send-keys -t _smoke 'echo tmux_ok' Enter \\
    && tmux capture-pane -t _smoke -p | grep -q tmux_ok \\
    && tmux kill-session -t _smoke

ENV PATH="/app/bin:/usr/local/cargo/bin:/usr/local/go/bin:${{PATH}}"
""",
    )
    w(
        TASK / "environment" / ".dockerignore",
        """.git
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
""",
    )


def write_metadata() -> None:
    w(
        TASK / "task.toml",
        """version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "data-processing"
subcategories = ["tool_specific"]
number_of_milestones = 0
codebase_size = "small"
languages = ["rust", "go"]
tags = ["merkle-tree", "incremental-sync", "checkpoint", "cross-language", "digest-reconciliation"]
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
        """Incremental sync against `/app/data/leaves/` serves leaf digests that disagree with the promoted journal head. The checkpoint reader and sync report bind different branch generations. A leaf that should appear at the promoted head is missing from the sync report leaf map. Aggregate root checks fail against `/app/ops/scripts/digest_lab.py` expectations for that head.

Edit operator tables under `/app/config/l7/`, Go sources under `/app/lane/`, and Rust sources under `/app/tree/`. Operator tables must not cap the active branch below the promoted journal head. Rebuild `/app/bin/lane` and `/app/bin/syncctl` after code changes. Do not hand-edit files under `/app/data/leaves/`.

Write `/output/sync-report.json` using `syncctl report --out /output/sync-report.json`. The report includes integer `branch_gen`, hex string `root_digest`, and a `leaves` object mapping each visible leaf id to its hex digest. Digests agree with `/app/ops/scripts/digest_lab.py` expectations for the active branch. `lane head` prints the same generation as `branch_gen`.
""",
    )
    w(
        TASK / "output_contract.toml",
        f"""user_visible_outputs = [
  "/output/{REPORT_NAME}",
  "/app/bin/lane",
  "/app/bin/syncctl",
]

internal_harness_files = [
  "/app/lane/internal",
  "/app/tree/core/src",
]

[structured_outputs.sync_report]
target = "/output/{REPORT_NAME}"
format = "json"
instruction_checks = [
  "branch_gen",
  "root_digest",
  "leaves",
]
""",
    )


def write_tests() -> None:
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
    w(
        TASK / "tests" / "test_outputs.py",
        '''import json
import subprocess
from pathlib import Path

LANE = "/app/bin/lane"
DIGEST_LAB = "/app/ops/scripts/digest_lab.py"
REPORT_PATH = Path("/output/sync-report.json")
DATA = Path("/app/data")
CFG = Path("/app/config/l7")


def _journal_head() -> int:
    head = 0
    for path in sorted((DATA / "journal").glob("tier_*.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            head = max(head, int(rec["gen"]))
    return head


def _expected(branch: int) -> dict:
    raw = subprocess.run(
        ["python3", DIGEST_LAB, str(branch)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return json.loads(raw)


def _config_field(field: str):
    for path in sorted(CFG.glob("*.toml")):
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped.startswith(f"{field} ="):
                continue
            raw = stripped.split("=", 1)[1].strip()
            if raw.startswith('"'):
                return json.loads(raw)
            return int(raw)
    raise AssertionError(f"missing operator table field {field}")


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def test_fixture_leaf_alpha():
    """Primary leaf resolves to fixture-derived digest at promoted branch."""
    branch = _journal_head()
    expected = _expected(branch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["leaves"]["alpha"] == expected["leaves"]["alpha"]


def test_fixture_leaf_gamma():
    """Branch-two leaf payload digest matches fixture expectations."""
    branch = _journal_head()
    expected = _expected(branch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["leaves"]["gamma"] == expected["leaves"]["gamma"]


def test_fixture_leaf_beta():
    """Baseline leaf digest matches fixture expectations at the promoted branch."""
    branch = _journal_head()
    expected = _expected(branch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["leaves"]["beta"] == expected["leaves"]["beta"]


def test_visible_leaf_map_complete():
    """Every fixture-visible leaf id appears in the sync report with matching digests."""
    branch = _journal_head()
    expected = _expected(branch)
    report = json.loads(REPORT_PATH.read_text())
    assert set(report["leaves"]) == set(expected["leaves"])
    for leaf_id, digest in expected["leaves"].items():
        assert report["leaves"][leaf_id] == digest


def test_promoted_leaf_present():
    """A leaf introduced only at the promoted head appears in the sync report."""
    branch = _journal_head()
    expected = _expected(branch)
    report = json.loads(REPORT_PATH.read_text())
    assert "delta" in report["leaves"]
    assert report["leaves"]["delta"] == expected["leaves"]["delta"]


def test_root_digest_matches_fixture_tree():
    """Root digest matches fixture-derived merkle root at journal head."""
    branch = _journal_head()
    expected = _expected(branch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["root_digest"] == expected["root_digest"]


def test_branch_gen_matches_journal_head():
    """Report branch generation equals journal-derived head."""
    head = _journal_head()
    report = json.loads(REPORT_PATH.read_text())
    runtime = json.loads((DATA / "state/runtime.json").read_text())
    assert report["branch_gen"] == head
    assert runtime["active_gen"] == head


def test_lane_head_alignment():
    """Lane checkpoint head agrees with sync report generation."""
    report = json.loads(REPORT_PATH.read_text())
    lane_head = int(_run([LANE, "head"]))
    assert lane_head == report["branch_gen"]


def test_config_branch_cap_cleared():
    """Operator branch ceiling matches the promoted journal head."""
    head = _journal_head()
    assert _config_field("branch_cap") == head


def test_runtime_active_matches_head():
    """Runtime active generation matches journal-derived head."""
    runtime = json.loads((DATA / "state/runtime.json").read_text())
    head = _journal_head()
    assert runtime["active_gen"] == head


def test_output_json_schema_valid():
    """Sync report exposes required fields with valid types."""
    assert REPORT_PATH.is_file(), "sync report missing"
    payload = json.loads(REPORT_PATH.read_text())
    assert isinstance(payload.get("branch_gen"), int)
    assert isinstance(payload.get("root_digest"), str)
    leaves = payload.get("leaves")
    assert isinstance(leaves, dict)
    for digest in leaves.values():
        assert isinstance(digest, str)
        int(digest, 16)
''',
    )


def fixed_head_go() -> str:
    return '''package m7

import (
	"bufio"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"

	"lab.local/sync_lane/pkg/frame"
)

func pickTier(configDir string) string {
	raw, err := os.ReadFile(filepath.Join(configDir, "m2.toml"))
	if err != nil {
		return "b"
	}
	for _, line := range strings.Split(string(raw), "\\n") {
		trimmed := strings.TrimSpace(line)
		if !strings.HasPrefix(trimmed, "scan_tier") {
			continue
		}
		parts := strings.SplitN(trimmed, "=", 2)
		if len(parts) != 2 {
			break
		}
		val := strings.Trim(strings.TrimSpace(parts[1]), "\\"")
		if val != "" {
			return val
		}
	}
	return "b"
}

func ResolveHead(journalDir string) (uint64, error) {
	tier := pickTier("/app/config/l7")
	path := filepath.Join(journalDir, "tier_"+tier+".jsonl")
	f, err := os.Open(path)
	if err != nil {
		return 0, err
	}
	defer f.Close()

	var head uint64
	scan := bufio.NewScanner(f)
	for scan.Scan() {
		line := scan.Text()
		if line == "" {
			continue
		}
		var row frame.JournalRow
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			return 0, err
		}
		if row.Gen > head {
			head = row.Gen
		}
	}
	if err := scan.Err(); err != nil {
		return 0, err
	}
	return head, nil
}
'''


def fixed_summary_go() -> str:
    return '''package m7

import (
	"encoding/json"
	"os"
	"path/filepath"

	"lab.local/sync_lane/pkg/frame"
)

func WriteSummary(outPath, dataRoot string) error {
	gen, err := ResolveHead(filepath.Join(dataRoot, "journal"))
	if err != nil {
		return err
	}
	root, leaves, err := readTreeSnapshot(dataRoot, gen)
	if err != nil {
		return err
	}
	doc := frame.SummaryDoc{
		BranchGen:  gen,
		RootDigest: root,
		Leaves:     leaves,
	}
	payload, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	payload = append(payload, '\\n')
	if err := os.MkdirAll(filepath.Dir(outPath), 0o755); err != nil {
		return err
	}
	return os.WriteFile(outPath, payload, 0o644)
}

func readTreeSnapshot(dataRoot string, gen uint64) (string, map[string]string, error) {
	return buildAt(dataRoot, gen)
}
'''


def write_solution() -> None:
    head_go = fixed_head_go()
    summary_go = fixed_summary_go()
    w(
        TASK / "solution" / "solve.sh",
        f"""#!/bin/bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/cargo/bin:/app/bin:${{PATH}}"

test -d /app/config/l7
test -x /app/bin/syncctl
mkdir -p /output /app/ops/staging

read -r HEAD < <(
python3 <<'PY'
import json
from pathlib import Path

head = 0
for path in sorted(Path("/app/data/journal").glob("tier_*.jsonl")):
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        head = max(head, int(rec["gen"]))
if head == 0:
    raise SystemExit("could not derive journal head")
print(head)
PY
)

sed -i "s/^branch_cap = .*/branch_cap = ${{HEAD}}/" /app/config/l7/k9.toml
sed -i "s/^journal_pin = .*/journal_pin = ${{HEAD}}/" /app/config/l7/k9.toml
sed -i "s/^head_floor = .*/head_floor = ${{HEAD}}/" /app/config/l7/k9.toml
sed -i 's/^sync_ready = .*/sync_ready = true/' /app/config/l7/k9.toml
sed -i 's/^audit_stamp = .*/audit_stamp = "applied"/' /app/config/l7/k9.toml

sed -i 's/^scan_tier = .*/scan_tier = "c"/' /app/config/l7/m2.toml
sed -i 's/^replay_gate = .*/replay_gate = 0/' /app/config/l7/m2.toml
sed -i 's/^barrier_live = .*/barrier_live = true/' /app/config/l7/m2.toml

sed -i 's/^phases = .*/phases = ["scan", "bind", "emit"]/' /app/config/l7/p7.toml
sed -i 's/^strict_chain = .*/strict_chain = true/' /app/config/l7/p7.toml
sed -i 's/^allow_batch = .*/allow_batch = false/' /app/config/l7/p7.toml

cat > /app/lane/internal/m7/head.go <<'GOFIX'
{head_go}
GOFIX

cat > /app/lane/internal/m7/summary.go <<'GOFIX'
{summary_go}
GOFIX

python3 <<'PY'
from pathlib import Path

path = Path("/app/tree/core/src/lib.rs")
text = path.read_text()
old = '''pub fn branch_cut(state: &RuntimeState, cap: u64) -> u64 {{
    let mut g = state.last_sync_gen;
    if cap > 0 && cap < g {{
        g = cap;
    }}
    if g > state.active_gen {{
        g = state.active_gen;
    }}
    g
}}'''
new = '''pub fn branch_cut(state: &RuntimeState, cap: u64) -> u64 {{
    let mut g = state.active_gen;
    if cap > 0 && cap < g {{
        g = cap;
    }}
    if g < state.last_sync_gen {{
        g = state.last_sync_gen;
    }}
    g
}}'''
if old not in text:
    raise SystemExit("branch_cut pattern missing")
path.write_text(text.replace(old, new))
PY

python3 <<PY
import json
import subprocess

head = int("${{HEAD}}")
probe = subprocess.run(
    ["python3", "/app/ops/scripts/digest_lab.py", str(head)],
    check=True,
    capture_output=True,
    text=True,
)
expected = json.loads(probe.stdout)
for leaf in ("alpha", "gamma", "delta"):
    if leaf not in expected["leaves"]:
        raise SystemExit(f"missing expected leaf {{leaf}}")
PY

(cd /app/lane && CGO_ENABLED=0 go build -o /app/bin/lane ./cmd/lane)
(cd /app/tree && cargo build --release --locked --offline -p syncctl)
install -m 755 /app/tree/target/release/syncctl /app/bin/syncctl

/app/bin/syncctl report --out /output/sync-report.json

lane_head=$(/app/bin/lane head)
report_gen=$(python3 -c "import json; print(json.load(open('/output/sync-report.json'))['branch_gen'])")
test "${{lane_head}}" -eq "${{report_gen}}"
test "${{report_gen}}" -eq "${{HEAD}}"

probe=$(python3 /app/ops/scripts/digest_lab.py "${{HEAD}}")
report_root=$(python3 -c "import json; print(json.load(open('/output/sync-report.json'))['root_digest'])")
expected_root=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['root_digest'])" "${{probe}}")
test "${{report_root}}" = "${{expected_root}}"

echo "complete" > /app/ops/staging/workflow.complete
""",
    )


def write_spec() -> None:
    w(
        ROOT / "specs" / "merkle-sync-branch-lag.md",
        """# merkle-sync-branch-lag

## Authoring Brief

Symptoms-only instruction describing stale incremental sync digests after branch promotion. Agent may edit `/app/config/l7/`, Go lane checkpoint reader, and Rust tree builder. Tests derive expected leaf and root digests from `/app/data/leaves/` fixtures and journal head. Output `/output/sync-report.json` with `branch_gen`, `root_digest`, and per-leaf digests. `lane head` must match `branch_gen`.

### Failure topology
Three authorities lag after promotion: Go ResolveHead scans tier_b (gen 2) while tier_c holds gen 3; Rust branch_cut prefers last_sync_gen; operator branch_cap pins generation 2. Delta leaf (since=3) absent until all three align.

### Triviality Ledger
- Config-only without lane tier fix leaves head at 2 — blocked by lane_head_alignment.
- Lane-only without Rust branch_cut leaves stale tree — blocked by promoted_leaf_present.
- Rust-only without config cap keeps branch_cut capped — blocked by config_branch_cap_cleared.

### Per-gate Pitfall Inventory
- RC1: oracle touches config, Go head.go/summary.go, Rust branch_cut — multi-file.
- RC3/GX3: decoy k3/ScanTierA rhymes with ResolveHead but unwired.
- CR7: code_forbidden_tokens on fix-path symbols.

### Construction manifest

#### symbol_table
- path: lane/internal/m7/head.go
  symbol: pickTier
  kind: function
- path: lane/internal/m7/summary.go
  symbol: WriteSummary
  kind: function
- path: tree/core/src/lib.rs
  symbol: branch_cut
  kind: function
- path: config/l7/k9.toml
  symbol: branch_cap
  kind: constant

#### flipping_point_contract
locations:
  - id: A
    path: lane/internal/m7/head.go
    controls_tests: [test_lane_head_alignment, test_branch_gen_matches_journal_head]
  - id: B
    path: tree/core/src/lib.rs
    controls_tests: [test_promoted_leaf_present, test_root_digest_matches_fixture_tree]
  - id: C
    path: config/l7/k9.toml
    controls_tests: [test_config_branch_cap_cleared, test_runtime_active_matches_head]
no_single_location_flips_majority: true

#### code_forbidden_tokens
code_forbidden_tokens: [merkle, sync, branch, lag, stale, leaf, checkpoint, digest, incremental, promote, generation, reconcile, tree, reader, builder, fixture, journal, tier, head, root, visible, canonical, operator, lane, syncctl, report, cap, runtime, active, last, promoted, delta, gamma, alpha, fixture-derived, cross-language, bind, scan, emit, workflow, recovery, peers, trust, aggregate, payload, since, map, hex, integer, object, write, rebuild, edit, tables, sources, data, config, output, app, must, agree, prints, same, matches, on-disk, after, again, when, never, appears, reflects, older, checks, fail, expectations, serving, started, landed, promotion, disk, still, hand-edit, files, under, paths, bin, may, code, changes, do, not, the, and, for, each, that, those, with, via, out, from, see, but, an, at, three, two, one, four, five, six, seven, eight, nine, ten]
""",
    )


def patch_lane_summary_buildat() -> None:
    """Inject buildAt helper referenced by summary.go."""
    w(
        TASK / "environment" / "lane" / "internal" / "m7" / "build.go",
        """package m7

import (
\t"encoding/json"
\t"os"
\t"path/filepath"
\t"sort"

\t"lab.local/sync_lane/pkg/frame"
)

type leafRow struct {
\tID      string `json:"id"`
\tPayload string `json:"payload"`
\tSince   uint64 `json:"since"`
}

func buildAt(dataRoot string, branch uint64) (string, map[string]string, error) {
\tentries, err := os.ReadDir(filepath.Join(dataRoot, "leaves"))
\tif err != nil {
\t\treturn "", nil, err
\t}
\tvar rows []leafRow
\tfor _, ent := range entries {
\t\tif ent.IsDir() {
\t\t\tcontinue
\t\t}
\t\traw, err := os.ReadFile(filepath.Join(dataRoot, "leaves", ent.Name()))
\t\tif err != nil {
\t\t\treturn "", nil, err
\t\t}
\t\tvar row leafRow
\t\tif err := json.Unmarshal(raw, &row); err != nil {
\t\t\treturn "", nil, err
\t\t}
\t\trows = append(rows, row)
\t}
\tsort.Slice(rows, func(i, j int) bool { return rows[i].ID < rows[j].ID })
\tleaves := make(map[string]string)
\tvar layer []string
\tfor _, row := range rows {
\t\tif row.Since > branch {
\t\t\tcontinue
\t\t}
\t\tdigest, err := leafDigest(row.ID, row.Payload)
\t\tif err != nil {
\t\t\treturn "", nil, err
\t\t}
\t\tleaves[row.ID] = digest
\t\tlayer = append(layer, digest)
\t}
\troot, err := merkleLayer(layer)
\tif err != nil {
\t\treturn "", nil, err
\t}
\t_ = frame.SummaryDoc{}
\treturn root, leaves, nil
}
""",
    )
    w(
        TASK / "environment" / "lane" / "internal" / "m7" / "hash.go",
        """package m7

import (
\t"crypto/sha256"
\t"encoding/hex"
)

func leafDigest(id, payload string) (string, error) {
\tcanon := []byte(`{"id":"` + id + `","payload":"` + payload + `"}`)
\tsum := sha256.Sum256(canon)
\treturn hex.EncodeToString(sum[:]), nil
}

func merkleLayer(layer []string) (string, error) {
\tif len(layer) == 0 {
\t\tsum := sha256.Sum256(nil)
\t\treturn hex.EncodeToString(sum[:]), nil
\t}
\tcur := layer
\tfor len(cur) > 1 {
\t\tvar nxt []string
\t\tfor idx := 0; idx < len(cur); idx += 2 {
\t\t\tleft, err := hex.DecodeString(cur[idx])
\t\t\tif err != nil {
\t\t\t\treturn "", err
\t\t\t}
\t\t\tright := left
\t\t\tif idx+1 < len(cur) {
\t\t\t\tright, err = hex.DecodeString(cur[idx+1])
\t\t\t\tif err != nil {
\t\t\t\t\treturn "", err
\t\t\t\t}
\t\t\t}
\t\t\tsum := sha256.Sum256(append(left, right...))
\t\t\tnxt = append(nxt, hex.EncodeToString(sum[:]))
\t\t}
\t\tcur = nxt
\t}
\treturn cur[0], nil
}
""",
    )


def main() -> None:
    if TASK.exists():
        shutil.rmtree(TASK)
    write_fixtures()
    write_config()
    write_go_lane()
    patch_lane_summary_buildat()
    write_rust_tree()
    write_digest_lab()
    write_runbook()
    write_dockerfile()
    write_metadata()
    write_tests()
    write_solution()
    write_spec()
    # sanity: broken tree should be stale
    assert merkle_root(HEAD_GEN) != merkle_root(STALE_GEN)
    assert "delta" not in leaf_map(STALE_GEN)
    assert "delta" in leaf_map(HEAD_GEN)
    env_files = sum(1 for _ in (TASK / "environment").rglob("*") if _.is_file())
    print(f"Generated {TASK} ({env_files} environment files)")
    print(f"HEAD root={merkle_root(HEAD_GEN)} STALE root={merkle_root(STALE_GEN)}")


if __name__ == "__main__":
    main()
