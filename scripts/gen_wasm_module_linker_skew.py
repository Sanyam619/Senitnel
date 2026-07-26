#!/usr/bin/env python3
"""One-shot generator for tasks/wasm-module-linker-skew (authoring tool, not shipped)."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "wasm-module-linker-skew"
REPORT_NAME = "link-report.json"

CANONICAL_GOLANG = (
    "public.ecr.aws/docker/library/golang:1.24-bookworm"
    "@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac"
)
CANONICAL_RUST = (
    "public.ecr.aws/docker/library/rust:1.85-slim"
    "@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36"
)

MODULE_SPECS = [
    {"id": "codec", "since": 1, "exports": ["decode", "encode"]},
    {"id": "host", "since": 1, "exports": ["run"], "imports": [
        {"module": "codec", "field": "encode", "bind": "encode"},
        {"module": "codec", "field": "decode", "bind": "decode"},
        {"module": "filter", "field": "apply", "bind": "apply"},
    ]},
    {"id": "filter", "since": 3, "exports": ["apply"]},
]

MANIFEST_ROWS = [
    {"tier": "a", "epoch": 1, "tip": "m1"},
    {"tier": "a", "epoch": 2, "tip": "m2a"},
    {"tier": "b", "epoch": 2, "tip": "m2b"},
    {"tier": "c", "epoch": 3, "tip": "m3"},
]

HEAD_EPOCH = 3
STALE_EPOCH = 2


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def module_body(module_id: str, version: int) -> dict:
    spec = next(m for m in MODULE_SPECS if m["id"] == module_id)
    body = {
        "id": module_id,
        "version": version,
        "exports": sorted(spec["exports"]),
        "imports": spec.get("imports", []),
    }
    return body


def module_digest(module_id: str, version: int) -> str:
    body = module_body(module_id, version)
    canon = json.dumps(body, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canon.encode()).hexdigest()


def visible_modules(epoch: int) -> list[str]:
    return sorted(m["id"] for m in MODULE_SPECS if m["since"] <= epoch)


def resolve_imports(host_version: int, dep_versions: dict[str, int]) -> list[dict]:
    host = module_body("host", host_version)
    rows: list[dict] = []
    for imp in host["imports"]:
        dep = imp["module"]
        if dep not in dep_versions:
            continue
        rows.append(
            {
                "import": f"{dep}.{imp['field']}",
                "slot": dep_versions[dep],
                "bound": imp["bind"],
            }
        )
    return sorted(rows, key=lambda r: r["import"])


def graph_at(epoch: int) -> dict:
    mods = visible_modules(epoch)
    dep_versions = {mid: epoch for mid in mods}
    modules_out: dict[str, dict] = {}
    for mid in mods:
        modules_out[mid] = {
            "version": epoch,
            "digest": module_digest(mid, epoch),
        }
    imports = resolve_imports(epoch, dep_versions) if "host" in mods else []
    canon = {
        "epoch": epoch,
        "modules": modules_out,
        "imports": imports,
    }
    digest = hashlib.sha256(
        json.dumps(canon, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    return {
        "epoch": epoch,
        "graph_digest": digest,
        "modules": modules_out,
        "imports": imports,
    }


def write_fixtures() -> None:
    data = TASK / "environment" / "data"
    modules_dir = data / "modules"
    for spec in MODULE_SPECS:
        mid = spec["id"]
        for ver in (STALE_EPOCH, HEAD_EPOCH):
            if ver < spec["since"]:
                continue
            body = module_body(mid, ver)
            w(modules_dir / f"{mid}.slot{ver}.json", json.dumps(body, indent=2) + "\n")

    ledger_lines: list[str] = []
    for path in sorted(modules_dir.glob("*.json")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        ledger_lines.append(f"{digest}  {path.name}")
    w(modules_dir / "slots.sha256", "\n".join(ledger_lines) + "\n")

    for tier in ("a", "b", "c"):
        lines = [json.dumps(r) for r in MANIFEST_ROWS if r["tier"] == tier]
        w(data / "manifest" / f"tier_{tier}.jsonl", "\n".join(lines) + ("\n" if lines else ""))

    w(
        data / "state" / "runtime.json",
        json.dumps(
            {
                "active_epoch": HEAD_EPOCH,
                "last_link_epoch": STALE_EPOCH,
                "manifest_head": HEAD_EPOCH,
            },
            indent=2,
        )
        + "\n",
    )


def write_config() -> None:
    cfg = TASK / "environment" / "config" / "l7"
    w(
        cfg / "k9.toml",
        f"""link_epoch_cap = {STALE_EPOCH}
manifest_pin = {STALE_EPOCH}
epoch_floor = {STALE_EPOCH}
gate_ready = false
audit_stamp = "pending"
""",
    )
    w(
        cfg / "m2.toml",
        """scan_tier = "b"
replay_gate = 1
barrier_live = false
slot_scan = false
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


def write_go_gate() -> None:
    gate = TASK / "environment" / "gate"
    w(
        gate / "go.mod",
        """module lab.local/wasm_gate

go 1.22
""",
    )
    w(gate / "go.sum", "")
    w(
        gate / "pkg" / "frame" / "doc.go",
        """package frame

type ManifestRow struct {
\tEpoch uint64 `json:"epoch"`
\tTip   string `json:"tip"`
}

type LinkDoc struct {
\tEpoch       uint64                       `json:"epoch"`
\tGraphDigest string                       `json:"graph_digest"`
\tModules     map[string]ModuleView        `json:"modules"`
\tImports     []ImportBind                 `json:"imports"`
}

type ModuleView struct {
\tVersion uint64 `json:"version"`
\tDigest  string `json:"digest"`
}

type ImportBind struct {
\tImport string `json:"import"`
\tSlot   uint64 `json:"slot"`
\tBound  string `json:"bound"`
}
""",
    )
    w(
        gate / "internal" / "m4" / "epoch.go",
        """package m4

import (
\t"bufio"
\t"encoding/json"
\t"os"
\t"path/filepath"
\t"strings"

\t"lab.local/wasm_gate/pkg/frame"
)

func pickTier(configDir string) string {
\t_, err := os.ReadFile(filepath.Join(configDir, "m2.toml"))
\tif err != nil {
\t\treturn "b"
\t}
\treturn "b"
}

func ResolveEpoch(manifestDir string) (uint64, error) {
\ttier := pickTier("/app/config/l7")
\tpath := filepath.Join(manifestDir, "tier_"+tier+".jsonl")
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
\t\tvar row frame.ManifestRow
\t\tif err := json.Unmarshal([]byte(line), &row); err != nil {
\t\t\treturn 0, err
\t\t}
\t\tif row.Epoch > head {
\t\t\thead = row.Epoch
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
        gate / "internal" / "k3" / "anchor.go",
        """package k3

import (
\t"bufio"
\t"encoding/json"
\t"os"
\t"path/filepath"

\t"lab.local/wasm_gate/pkg/frame"
)

func ScanTierA(manifestDir string) (uint64, error) {
\tpath := filepath.Join(manifestDir, "tier_a.jsonl")
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
\t\tvar row frame.ManifestRow
\t\tif err := json.Unmarshal([]byte(line), &row); err != nil {
\t\t\treturn 0, err
\t\t}
\t\tif row.Epoch > head {
\t\t\thead = row.Epoch
\t\t}
\t}
\treturn head, scan.Err()
}
""",
    )
    w(
        gate / "cmd" / "gatectl" / "main.go",
        """package main

import (
\t"fmt"
\t"log"
\t"os"

\t"lab.local/wasm_gate/internal/m4"
)

func main() {
\tif len(os.Args) < 2 {
\t\tlog.Fatal("usage: gatectl epoch")
\t}
\tswitch os.Args[1] {
\tcase "epoch":
\t\tepoch, err := m4.ResolveEpoch("/app/data/manifest")
\t\tif err != nil {
\t\t\tlog.Fatal(err)
\t\t}
\t\tfmt.Println(epoch)
\tdefault:
\t\tlog.Fatalf("unknown subcommand %q", os.Args[1])
\t}
}
""",
    )


def write_rust_ws() -> None:
    ws = TASK / "environment" / "wasm"
    w(
        ws / "Cargo.toml",
        """[workspace]
members = ["core", "linkctl"]
resolver = "2"

[workspace.package]
edition = "2021"
""",
    )
    w(ws / "Cargo.lock", "")
    w(
        ws / "core" / "Cargo.toml",
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
        ws / "linkctl" / "Cargo.toml",
        """[package]
name = "linkctl"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "linkctl"
path = "src/main.rs"

[dependencies]
core = { path = "../core" }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
clap = { version = "4", features = ["derive"] }
""",
    )
    w(
        ws / "core" / "src" / "lib.rs",
        """use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize)]
pub struct RuntimeState {
    pub active_epoch: u64,
    pub last_link_epoch: u64,
    pub manifest_head: u64,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct ModuleSpec {
    pub id: String,
    pub version: u64,
    pub exports: Vec<String>,
    #[serde(default)]
    pub imports: Vec<ImportRow>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct ImportRow {
    pub module: String,
    pub field: String,
    pub bind: String,
}

#[derive(Debug, Serialize)]
pub struct ModuleView {
    pub version: u64,
    pub digest: String,
}

#[derive(Debug, Serialize)]
pub struct ImportBind {
    pub import: String,
    pub slot: u64,
    pub bound: String,
}

#[derive(Debug, Serialize)]
pub struct LinkDoc {
    pub epoch: u64,
    pub graph_digest: String,
    pub modules: BTreeMap<String, ModuleView>,
    pub imports: Vec<ImportBind>,
}

pub fn epoch_cut(state: &RuntimeState, cap: u64) -> u64 {
    let mut e = state.last_link_epoch;
    if cap > 0 && cap < e {
        e = cap;
    }
    if e > state.active_epoch {
        e = state.active_epoch;
    }
    e
}

pub fn load_slot(modules_dir: &Path, module_id: &str, slot: u64) -> Result<ModuleSpec, String> {
    let path = modules_dir.join(format!("{module_id}.slot{slot}.json"));
    let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

fn module_digest(path: &Path) -> Result<String, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let val: serde_json::Value = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let canon = canonical_json(&val);
    Ok(hex::encode(Sha256::digest(canon.as_bytes())))
}

fn canonical_json(value: &serde_json::Value) -> String {
    match value {
        serde_json::Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            let body: Vec<String> = keys
                .iter()
                .map(|k| format!("\\"{k}\\":{}", canonical_json(&map[*k])))
                .collect();
            format!("{{{}}}", body.join(","))
        }
        serde_json::Value::Array(items) => {
            let body: Vec<String> = items.iter().map(canonical_json).collect();
            format!("[{}]", body.join(","))
        }
        serde_json::Value::String(s) => format!("\\"{}\\"", s.replace('\\\\', "\\\\\\\\").replace('"', "\\\\\\"")),
        serde_json::Value::Number(n) => n.to_string(),
        serde_json::Value::Bool(b) => b.to_string(),
        serde_json::Value::Null => "null".to_string(),
    }
}

fn visible_ids(epoch: u64) -> Vec<&'static str> {
    let mut out = Vec::new();
    if epoch >= 1 {
        out.push("codec");
        out.push("host");
    }
    if epoch >= 3 {
        out.push("filter");
    }
    out.sort();
    out
}

pub fn resolve_graph(data_root: &Path, epoch: u64) -> Result<LinkDoc, String> {
    let modules_dir = data_root.join("modules");
    let mut modules = BTreeMap::new();
    let mut dep_versions = BTreeMap::new();
    for mid in visible_ids(epoch) {
        let path = modules_dir.join(format!("{mid}.slot{epoch}.json"));
        let spec = load_slot(&modules_dir, mid, epoch)?;
        let digest = module_digest(&path)?;
        dep_versions.insert(mid.to_string(), epoch);
        modules.insert(
            mid.to_string(),
            ModuleView {
                version: epoch,
                digest,
            },
        );
    }
    let mut imports = Vec::new();
    if let Ok(host) = load_slot(&modules_dir, "host", epoch) {
        for row in host.imports {
            let dep = row.module.clone();
            let slot = dep_versions.get(&dep).copied().unwrap_or(0);
            if slot == 0 {
                continue;
            }
            imports.push(ImportBind {
                import: format!("{}.{}" , dep, row.field),
                slot,
                bound: row.bind,
            });
        }
    }
    imports.sort_by(|a, b| a.import.cmp(&b.import));
    let canon_val = serde_json::json!({
        "epoch": epoch,
        "modules": &modules,
        "imports": &imports,
    });
    let digest = hex::encode(Sha256::digest(canonical_json(&canon_val).as_bytes()));
    Ok(LinkDoc {
        epoch,
        graph_digest: digest,
        modules,
        imports,
    })
}

pub fn write_report(out_path: &Path, data_root: &Path) -> Result<(), String> {
    let state_path = data_root.join("state/runtime.json");
    let raw = fs::read_to_string(&state_path).map_err(|e| e.to_string())?;
    let state: RuntimeState = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let cap = read_cap(data_root)?;
    let epoch = epoch_cut(&state, cap);
    let doc = resolve_graph(data_root, epoch)?;
    let payload = serde_json::to_string_pretty(&doc).map_err(|e| e.to_string())?;
    if let Some(parent) = out_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(out_path, format!("{payload}\\n")).map_err(|e| e.to_string())
}

fn read_cap(data_root: &Path) -> Result<u64, String> {
    let cfg_dir = Path::new("/app/config/l7");
    for entry in fs::read_dir(cfg_dir).map_err(|e| e.to_string())? {
        let entry = entry.map_err(|e| e.to_string())?;
        if entry.file_name() != "k9.toml" {
            continue;
        }
        let text = fs::read_to_string(entry.path()).map_err(|e| e.to_string())?;
        for line in text.lines() {
            let trimmed = line.trim();
            if !trimmed.starts_with("link_epoch_cap") {
                continue;
            }
            let val = trimmed.split('=').nth(1).unwrap_or("0").trim();
            return val.parse().map_err(|e| format!("cap: {e}"));
        }
    }
    Ok(0)
}
""",
    )
    w(
        ws / "linkctl" / "src" / "main.rs",
        """use clap::{Parser, Subcommand};
use core::write_report;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "linkctl")]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Report {
        #[arg(long)]
        out: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    match cli.cmd {
        Commands::Report { out } => {
            if let Err(err) = write_report(&out, PathBuf::from("/app/data").as_path()) {
                eprintln!("{err}");
                std::process::exit(1);
            }
        }
    }
}
""",
    )


def write_graph_lab() -> None:
    w(
        TASK / "environment" / "ops" / "scripts" / "graph_lab.py",
        """#!/usr/bin/env python3
\"\"\"Reference graph digests for a manifest epoch (verifier oracle).\"\"\"

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

DATA = Path("/app/data")
MODULES = DATA / "modules"


def module_body(module_id: str, version: int) -> dict:
    raw = (MODULES / f"{module_id}.slot{version}.json").read_text()
    return json.loads(raw)


def module_digest(module_id: str, version: int) -> str:
    body = module_body(module_id, version)
    canon = json.dumps(body, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canon.encode()).hexdigest()


def visible(epoch: int) -> list[str]:
    out: list[str] = []
    for mid, since in (("codec", 1), ("host", 1), ("filter", 3)):
        if since <= epoch:
            out.append(mid)
    return sorted(out)


def resolve_imports(epoch: int, dep_versions: dict[str, int]) -> list[dict]:
    host = module_body("host", epoch)
    rows: list[dict] = []
    for imp in host.get("imports", []):
        dep = imp["module"]
        if dep not in dep_versions:
            continue
        rows.append(
            {
                "import": f"{dep}.{imp['field']}",
                "slot": dep_versions[dep],
                "bound": imp["bind"],
            }
        )
    return sorted(rows, key=lambda r: r["import"])


def graph_at(epoch: int) -> dict:
    mods = visible(epoch)
    dep_versions = {mid: epoch for mid in mods}
    modules_out = {
        mid: {"version": epoch, "digest": module_digest(mid, epoch)} for mid in mods
    }
    imports = resolve_imports(epoch, dep_versions) if "host" in mods else []
    canon = {"epoch": epoch, "modules": modules_out, "imports": imports}
    digest = hashlib.sha256(
        json.dumps(canon, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    return {
        "epoch": epoch,
        "graph_digest": digest,
        "modules": modules_out,
        "imports": imports,
    }


def main() -> None:
    epoch = int(sys.argv[1])
    print(json.dumps(graph_at(epoch), separators=(",", ":")))


if __name__ == "__main__":
    main()
""",
    )


def write_runbook() -> None:
    w(
        TASK / "environment" / "ops" / "runbooks" / "linkctl_usage.md",
        """# linkctl / gatectl operator notes

Partial builds may leave multiple slot files per module id under `/app/data/modules/`.
The active manifest epoch selects which slot participates in the import table.

Subcommands:
- `gatectl epoch` — prints manifest epoch the gate treats as current
- `linkctl report --out PATH` — writes JSON link report for the resolved epoch

Operator tables under `/app/config/l7/` influence epoch resolution and slot binding.
""",
    )


def write_dockerfile() -> None:
    w(
        TASK / "environment" / "Dockerfile",
        f"""# syntax=docker/dockerfile:1

FROM {CANONICAL_GOLANG} AS gobuilder

WORKDIR /build/gate
COPY gate/go.mod gate/go.sum ./
RUN go mod download
COPY gate/pkg/ pkg/
COPY gate/internal/ internal/
COPY gate/cmd/ cmd/
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/gatectl ./cmd/gatectl

FROM {CANONICAL_RUST} AS rsbuilder

WORKDIR /build/wasm
COPY wasm/Cargo.toml wasm/Cargo.lock ./
COPY wasm/core/Cargo.toml core/
COPY wasm/linkctl/Cargo.toml linkctl/
COPY wasm/core/src/ core/src/
COPY wasm/linkctl/src/ linkctl/src/
RUN cargo generate-lockfile && cargo build --release --locked -p linkctl

FROM {CANONICAL_GOLANG}

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
    GOPROXY=off \\
    RUSTUP_HOME=/usr/local/rustup \\
    CARGO_HOME=/usr/local/cargo

RUN mkdir -p /go /tmp/go-cache

RUN pip3 install --no-cache-dir --break-system-packages \\
    pytest==8.4.1 \\
    pytest-json-ctrf==0.3.5

COPY --from=rsbuilder /usr/local/rustup /usr/local/rustup
COPY --from=rsbuilder /usr/local/cargo /usr/local/cargo
COPY --from=rsbuilder /build/wasm/target /app/wasm/target
COPY --from=gobuilder --chmod=755 /out/gatectl /app/bin/gatectl
COPY --from=rsbuilder --chmod=755 /build/wasm/target/release/linkctl /app/bin/linkctl
COPY config/ /app/config/
COPY data/ /app/data/
COPY gate/ /app/gate/
COPY wasm/ /app/wasm/
COPY --from=rsbuilder /build/wasm/Cargo.lock /app/wasm/Cargo.lock
COPY ops/ /app/ops/

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
**/node_modules/
**/target/
**/dist/
**/build/
.env
*.log
solution/
tests/
""",
    )


def write_metadata() -> None:
    w(
        TASK / "instruction.md",
        """Partial compile artifacts remain under `/app/data/modules/`, yet `linkctl report` and `gatectl epoch` disagree with `/app/ops/scripts/graph_lab.py` at the promoted manifest head. The link report omits filter even though codec, host, and filter should all appear in the graph at that head.

Edit operator tables under `/app/config/l7/`, Go sources under `/app/gate/`, and Rust sources under `/app/wasm/`. Do not cap the link epoch below the promoted manifest head. Rebuild `/app/bin/gatectl` and `/app/bin/linkctl` after code changes. Do not hand-edit files under `/app/data/modules/`; `slots.sha256` there is the integrity ledger for inputs.

Write `/output/link-report.json` using `linkctl report --out /output/link-report.json`. The report includes integer `epoch`, hex string `graph_digest`, a `modules` object mapping each visible module id to `{version, digest}`, and an `imports` list binding host imports to dependency slots. Values agree with `/app/ops/scripts/graph_lab.py` for the active epoch. `gatectl epoch` prints the same integer as `epoch`.
""",
    )
    w(
        TASK / "task.toml",
        """version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "build-and-dependency-management"
subcategories = ["tool_specific"]
number_of_milestones = 0
codebase_size = "small"
languages = ["rust", "go"]
tags = ["wasm", "linker", "build-graph", "manifest", "cross-language"]
expert_time_estimate_min = 120
junior_time_estimate_min = 300

[verifier]
timeout_sec = 900

[agent]
timeout_sec = 1800

[environment]
allow_internet = false
build_timeout_sec = 900
cpus = 2
memory_mb = 4096
storage_mb = 10240
""",
    )
    w(
        TASK / "output_contract.toml",
        """user_visible_outputs = [
  "/output/link-report.json",
  "/app/bin/gatectl",
  "/app/bin/linkctl",
]

internal_harness_files = [
  "/app/gate/internal",
  "/app/wasm/core/src",
]

[structured_outputs.link_report]
target = "/output/link-report.json"
format = "json"
instruction_checks = [
  "epoch",
  "graph_digest",
  "modules",
  "imports",
]
""",
    )
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


def write_tests() -> None:
    w(
        TASK / "tests" / "test_outputs.py",
        '''import json
import subprocess
from pathlib import Path

GATECTL = "/app/bin/gatectl"
GRAPH_LAB = "/app/ops/scripts/graph_lab.py"
REPORT_PATH = Path("/output/link-report.json")
DATA = Path("/app/data")
CFG = Path("/app/config/l7")
MODULES = DATA / "modules"
SLOTS_LEDGER = MODULES / "slots.sha256"


def _manifest_head() -> int:
    head = 0
    for path in sorted((DATA / "manifest").glob("tier_*.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            head = max(head, int(rec["epoch"]))
    return head


def _expected(epoch: int) -> dict:
    raw = subprocess.run(
        ["python3", GRAPH_LAB, str(epoch)],
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


def test_codec_digest_at_head():
    """Codec module digest matches fixture slot at promoted epoch."""
    epoch = _manifest_head()
    expected = _expected(epoch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["modules"]["codec"]["digest"] == expected["modules"]["codec"]["digest"]


def test_host_digest_at_head():
    """Host module digest matches fixture slot at promoted epoch."""
    epoch = _manifest_head()
    expected = _expected(epoch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["modules"]["host"]["digest"] == expected["modules"]["host"]["digest"]


def test_filter_module_present():
    """Filter module appears once manifest epoch reaches three."""
    epoch = _manifest_head()
    expected = _expected(epoch)
    report = json.loads(REPORT_PATH.read_text())
    assert "filter" in report["modules"]
    assert report["modules"]["filter"]["digest"] == expected["modules"]["filter"]["digest"]


def test_visible_module_map_complete():
    """Every fixture-visible module id appears with matching digests."""
    epoch = _manifest_head()
    expected = _expected(epoch)
    report = json.loads(REPORT_PATH.read_text())
    assert set(report["modules"]) == set(expected["modules"])
    for mid, view in expected["modules"].items():
        assert report["modules"][mid]["digest"] == view["digest"]
        assert report["modules"][mid]["version"] == view["version"]


def test_import_table_bindings():
    """Host import table binds dependency slots for the active epoch."""
    epoch = _manifest_head()
    expected = _expected(epoch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["imports"] == expected["imports"]


def test_graph_digest_matches_fixture():
    """Graph digest matches fixture-derived composite at manifest head."""
    epoch = _manifest_head()
    expected = _expected(epoch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["graph_digest"] == expected["graph_digest"]


def test_epoch_matches_manifest_head():
    """Report epoch equals manifest-derived head."""
    head = _manifest_head()
    report = json.loads(REPORT_PATH.read_text())
    assert report["epoch"] == head


def test_gatectl_epoch_alignment():
    """Gate manifest epoch agrees with link report epoch."""
    report = json.loads(REPORT_PATH.read_text())
    gate_epoch = int(_run([GATECTL, "epoch"]))
    assert gate_epoch == report["epoch"]


def test_config_link_epoch_cap_cleared():
    """Operator link epoch ceiling matches promoted manifest head."""
    head = _manifest_head()
    assert _config_field("link_epoch_cap") == head


def test_module_slots_ledger_intact():
    """Module slot fixtures under /app/data/modules/ match slots.sha256."""
    assert SLOTS_LEDGER.is_file(), SLOTS_LEDGER
    for line in SLOTS_LEDGER.read_text().splitlines():
        if not line.strip():
            continue
        want_hash, rel = line.split(None, 1)
        path = MODULES / rel
        assert path.is_file(), rel
        result = subprocess.run(
            ["sha256sum", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.split()[0] == want_hash, rel


def test_output_json_schema_valid():
    """Link report exposes required fields with valid types."""
    assert REPORT_PATH.is_file(), "link report missing"
    payload = json.loads(REPORT_PATH.read_text())
    assert isinstance(payload.get("epoch"), int)
    assert isinstance(payload.get("graph_digest"), str)
    modules = payload.get("modules")
    assert isinstance(modules, dict)
    for view in modules.values():
        assert isinstance(view.get("version"), int)
        assert isinstance(view.get("digest"), str)
        int(view["digest"], 16)
    imports = payload.get("imports")
    assert isinstance(imports, list)
    for row in imports:
        assert isinstance(row.get("import"), str)
        assert isinstance(row.get("slot"), int)
        assert isinstance(row.get("bound"), str)
''',
    )


def fixed_epoch_go() -> str:
    return '''package m4

import (
\t"bufio"
\t"encoding/json"
\t"os"
\t"path/filepath"
\t"strings"

\t"lab.local/wasm_gate/pkg/frame"
)

func pickTier(configDir string) string {
\traw, err := os.ReadFile(filepath.Join(configDir, "m2.toml"))
\tif err != nil {
\t\treturn "b"
\t}
\tfor _, line := range strings.Split(string(raw), "\\n") {
\t\ttrimmed := strings.TrimSpace(line)
\t\tif !strings.HasPrefix(trimmed, "scan_tier") {
\t\t\tcontinue
\t\t}
\t\tparts := strings.SplitN(trimmed, "=", 2)
\t\tif len(parts) != 2 {
\t\t\tbreak
\t\t}
\t\tval := strings.Trim(strings.TrimSpace(parts[1]), "\\"")
\t\tif val != "" {
\t\t\treturn val
\t\t}
\t}
\treturn "b"
}

func ResolveEpoch(manifestDir string) (uint64, error) {
\ttier := pickTier("/app/config/l7")
\tpath := filepath.Join(manifestDir, "tier_"+tier+".jsonl")
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
\t\tvar row frame.ManifestRow
\t\tif err := json.Unmarshal([]byte(line), &row); err != nil {
\t\t\treturn 0, err
\t\t}
\t\tif row.Epoch > head {
\t\t\thead = row.Epoch
\t\t}
\t}
\tif err := scan.Err(); err != nil {
\t\treturn 0, err
\t}
\treturn head, nil
}
'''


def write_solution() -> None:
    epoch_go = fixed_epoch_go()
    w(
        TASK / "solution" / "solve.sh",
        f"""#!/bin/bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/cargo/bin:/app/bin:${{PATH}}"

test -d /app/config/l7
test -x /app/bin/linkctl
mkdir -p /output /app/ops/staging

read -r HEAD < <(
python3 <<'PY'
import json
from pathlib import Path

head = 0
for path in sorted(Path("/app/data/manifest").glob("tier_*.jsonl")):
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        head = max(head, int(rec["epoch"]))
if head == 0:
    raise SystemExit("could not derive manifest head")
print(head)
PY
)

sed -i "s/^link_epoch_cap = .*/link_epoch_cap = ${{HEAD}}/" /app/config/l7/k9.toml
sed -i "s/^manifest_pin = .*/manifest_pin = ${{HEAD}}/" /app/config/l7/k9.toml
sed -i "s/^epoch_floor = .*/epoch_floor = ${{HEAD}}/" /app/config/l7/k9.toml
sed -i 's/^gate_ready = .*/gate_ready = true/' /app/config/l7/k9.toml
sed -i 's/^audit_stamp = .*/audit_stamp = "applied"/' /app/config/l7/k9.toml

sed -i 's/^scan_tier = .*/scan_tier = "c"/' /app/config/l7/m2.toml
sed -i 's/^replay_gate = .*/replay_gate = 0/' /app/config/l7/m2.toml
sed -i 's/^barrier_live = .*/barrier_live = true/' /app/config/l7/m2.toml

sed -i 's/^phases = .*/phases = ["scan", "bind", "emit"]/' /app/config/l7/p7.toml
sed -i 's/^strict_chain = .*/strict_chain = true/' /app/config/l7/p7.toml
sed -i 's/^allow_batch = .*/allow_batch = false/' /app/config/l7/p7.toml

cat > /app/gate/internal/m4/epoch.go <<'GOFIX'
{epoch_go}
GOFIX

python3 <<'PY'
from pathlib import Path

path = Path("/app/wasm/core/src/lib.rs")
text = path.read_text()
old = '''pub fn epoch_cut(state: &RuntimeState, cap: u64) -> u64 {{
    let mut e = state.last_link_epoch;
    if cap > 0 && cap < e {{
        e = cap;
    }}
    if e > state.active_epoch {{
        e = state.active_epoch;
    }}
    e
}}'''
new = '''pub fn epoch_cut(state: &RuntimeState, cap: u64) -> u64 {{
    let mut e = state.active_epoch;
    if cap > 0 && cap < e {{
        e = cap;
    }}
    if e < state.last_link_epoch {{
        e = state.last_link_epoch;
    }}
    e
}}'''
if old not in text:
    raise SystemExit("epoch_cut pattern missing")
path.write_text(text.replace(old, new))
PY

python3 <<PY
import json
import subprocess

head = int("${{HEAD}}")
probe = subprocess.run(
    ["python3", "/app/ops/scripts/graph_lab.py", str(head)],
    check=True,
    capture_output=True,
    text=True,
)
expected = json.loads(probe.stdout)
for mid in ("codec", "host", "filter"):
    if mid not in expected["modules"]:
        raise SystemExit(f"missing expected module {{mid}}")
PY

(cd /app/gate && CGO_ENABLED=0 go build -o /app/bin/gatectl ./cmd/gatectl)
(cd /app/wasm && cargo build --release --locked --offline -p linkctl)
install -m 755 /app/wasm/target/release/linkctl /app/bin/linkctl

/app/bin/linkctl report --out /output/link-report.json

gate_epoch=$(/app/bin/gatectl epoch)
report_epoch=$(python3 -c "import json; print(json.load(open('/output/link-report.json'))['epoch'])")
test "${{gate_epoch}}" -eq "${{report_epoch}}"
test "${{report_epoch}}" -eq "${{HEAD}}"

probe=$(python3 /app/ops/scripts/graph_lab.py "${{HEAD}}")
report_root=$(python3 -c "import json; print(json.load(open('/output/link-report.json'))['graph_digest'])")
expected_root=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['graph_digest'])" "${{probe}}")
test "${{report_root}}" = "${{expected_root}}"

echo "complete" > /app/ops/staging/workflow.complete
""",
    )


def write_spec() -> None:
    w(
        ROOT / "specs" / "wasm-module-linker-skew.md",
        """# wasm-module-linker-skew

## Authoring Brief

Symptoms-only instruction for WASM module graph skew after partial compile. Agent edits `/app/config/l7/`, Go gate epoch reader, and Rust link epoch cut. Tests derive expected digests from `/app/data/modules/` via graph_lab. Output `/output/link-report.json`. `gatectl epoch` must match report `epoch`.

### Failure topology
Three authorities lag after promotion: Go ResolveEpoch scans tier_b (epoch 2); Rust epoch_cut prefers last_link_epoch; operator link_epoch_cap pins epoch 2. Filter module (since=3) absent until all three align.

### symbol_table
- gate/internal/m4/epoch.go :: ResolveEpoch
- wasm/core/src/lib.rs :: epoch_cut
- config/l7/k9.toml :: link_epoch_cap
- config/l7/m2.toml :: scan_tier

### flipping_point_contract
- Go gate fix: gatectl_epoch_alignment, epoch_matches_manifest_head
- Rust link table fix: filter_module_present, graph_digest_matches_fixture
- Config cap fix: config_link_epoch_cap_cleared
""",
    )


def main() -> None:
    if TASK.exists():
        shutil.rmtree(TASK)
    write_fixtures()
    write_config()
    write_go_gate()
    write_rust_ws()
    write_graph_lab()
    write_runbook()
    write_dockerfile()
    write_metadata()
    write_tests()
    write_solution()
    write_spec()
    stale = graph_at(STALE_EPOCH)
    head = graph_at(HEAD_EPOCH)
    assert stale["graph_digest"] != head["graph_digest"]
    assert "filter" not in stale["modules"]
    assert "filter" in head["modules"]
    env_files = sum(1 for _ in (TASK / "environment").rglob("*") if _.is_file())
    print(f"Generated {TASK} ({env_files} environment files)")
    print(f"HEAD graph={head['graph_digest'][:16]} STALE graph={stale['graph_digest'][:16]}")


if __name__ == "__main__":
    main()
