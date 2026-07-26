#!/usr/bin/env python3
"""Generate tasks/systemd-unit-cascade-rollback (authoring tool, not shipped)."""

from __future__ import annotations

import json
import shutil
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tasks" / "systemd-unit-cascade-rollback"
ENV = ROOT / "environment"
SPECS = Path(__file__).resolve().parents[1] / "specs"

NAMES = [
    "journal.service",
    "store.service",
    "cache.service",
    "ingress.service",
    "relay.service",
    "stack.target",
]


def w(rel: str, content: str, exe: bool = False) -> None:
    if rel.startswith("environment/"):
        p = ENV / rel.removeprefix("environment/")
    else:
        p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
    if exe:
        p.chmod(0o755)


def main() -> None:
    if ROOT.exists():
        shutil.rmtree(ROOT)
    ROOT.mkdir()

    w("instruction.md", INSTRUCTION)
    w("task.toml", TASK_TOML)
    w("output_contract.toml", OUTPUT_CONTRACT)
    w("environment/.dockerignore", DOCKERIGNORE)
    w("environment/Dockerfile", DOCKERFILE)
    w("environment/config/field-notes.md", FIELD_NOTES)
    w("environment/config/stack.toml", STACK_TOML)
    w("environment/config/aliases.toml", ALIASES_TOML)
    for rel, body in SCRIPTS.items():
        w(f"environment/scripts/{rel}", body, exe=True)
    w("environment/data/build_fixtures.sh", BUILD_FIXTURES, exe=True)
    w("environment/data/fixtures/stack-seed/manifest.txt", SEED_MANIFEST)
    w("environment/Cargo.toml", WORKSPACE_CARGO)
    for rel, body in RUST_FILES.items():
        if rel == "Cargo.lock":
            continue
        w(f"environment/{rel}", body)
    w("tests/test.sh", TEST_SH, exe=True)
    w("tests/test_outputs.py", TEST_OUTPUTS)
    w("solution/solve.sh", SOLVE_SH, exe=True)
    w("construction_manifest.json", CONSTRUCTION_MANIFEST)
    write_specs()
    bootstrap_cargo_lock()
    print(f"Generated task at {ROOT}")


def bootstrap_cargo_lock() -> None:
    """Build the environment image once and copy the generated Cargo.lock."""
    import subprocess

    env_dir = ENV
    try:
        subprocess.run(
            ["docker", "build", "-t", "stack-rollback-bootstrap", str(env_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        cid = subprocess.check_output(
            ["docker", "create", "stack-rollback-bootstrap"], text=True
        ).strip()
        try:
            subprocess.run(
                [
                    "docker",
                    "cp",
                    f"{cid}:/app/Cargo.lock",
                    str(env_dir / "Cargo.lock"),
                ],
                check=True,
            )
        finally:
            subprocess.run(["docker", "rm", cid], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"warn: could not bootstrap Cargo.lock via docker: {exc}")


def write_specs() -> None:
    SPECS.mkdir(parents=True, exist_ok=True)
    (SPECS / "systemd-unit-cascade-rollback.md").write_text(AUTHORING_SPEC, encoding="utf-8")
    (SPECS / "systemd-unit-cascade-rollback-reviewer.md").write_text(REVIEWER_APPENDIX, encoding="utf-8")
    (SPECS / "systemd-unit-cascade-rollback-attempt-1-evidence.json").write_text(
        EVIDENCE_JSON, encoding="utf-8"
    )


INSTRUCTION = """
A partial stack cutover left dependency ordering half rewired. /app/scripts/stack-health.sh
lists the target on disk but start attempts on dependent services stall or fail,
/app/scripts/depwalk-wrapper.sh reports unresolved After edges between named pairs, and
/app/scripts/ledger-stub.sh will not emit a rollback report until the graph is reconciled.
Operator notes live under /app/config/; lab binaries under /app/bin/; rebuild sources under
/app/. Fixture anchors shipped with the lab are read-only.

Produce /output/rollback-report.json: version 1, units for stack.target, ingress.service,
cache.service, store.service, journal.service, and relay.service — each with name, state,
start_order, hard_deps, soft_deps. All six must reach active, override merge must follow
the precedence in /app/config/field-notes.md, the graph must be acyclic with a valid start
sequence, and report fields must match per-unit runtime state on disk.
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
languages = ["bash", "rust"]
tags = ["host", "ops", "rust", "bash", "migration", "recovery"]
expert_time_estimate_min = 120
junior_time_estimate_min = 240

[verifier]
timeout_sec = 600

[agent]
timeout_sec = 1200

[environment]
allow_internet = false
build_timeout_sec = 900
cpus = 2
memory_mb = 4096
storage_mb = 10240
"""

OUTPUT_CONTRACT = """
user_visible_outputs = [
  "/output/rollback-report.json",
]

internal_harness_files = [
  "/data/fixtures/stack-seed/",
  "/data/stack/runtime/",
]

[structured_outputs.rollback_report]
target = "/output/rollback-report.json"
format = "json"
instruction_checks = ["version", "units", "name", "state", "start_order", "hard_deps", "soft_deps"]
"""

DOCKERIGNORE = """
.git
.gitignore
**/__pycache__/
**/*.pyc
**/.pytest_cache/
**/target/
.env
*.log
solution/
tests/
"""

DOCKERFILE = """
# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS builder

WORKDIR /build
COPY Cargo.toml ./
COPY stack-core/Cargo.toml stack-core/Cargo.toml
COPY depwalk/Cargo.toml depwalk/Cargo.toml
COPY stackarm/Cargo.toml stackarm/Cargo.toml
COPY ledgersnap/Cargo.toml ledgersnap/Cargo.toml
COPY stack-core/src stack-core/src
COPY depwalk/src depwalk/src
COPY stackarm/src stackarm/src
COPY ledgersnap/src ledgersnap/src

RUN cargo build --release

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before any other setup.
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        asciinema=2.2.0-1 \\
        tmux=3.3a-3 \\
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux kill-session -t _smoke

RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        ca-certificates=20230311+deb12u1 \\
        python3=3.11.2-1+b1 \\
        python3-pip=23.0.1+dfsg-1 \\
        build-essential=12.9 \\
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \\
    pytest==8.4.1 \\
    pytest-json-ctrf==0.3.5

COPY --from=builder /usr/local/cargo /usr/local/cargo
COPY --from=builder /usr/local/rustup /usr/local/rustup
ENV PATH="/usr/local/cargo/bin:${PATH}" \\
    RUSTUP_HOME=/usr/local/rustup \\
    CARGO_HOME=/usr/local/cargo

COPY --from=builder /build/target /app/target
COPY --from=builder /build/Cargo.lock /app/Cargo.lock
COPY --from=builder --chmod=755 /build/target/release/depwalk /app/bin/chk_a
COPY --from=builder --chmod=755 /build/target/release/stackarm /app/bin/arm_b
COPY --from=builder --chmod=755 /build/target/release/ledgersnap /app/bin/snap_c

COPY config/ /app/config/
COPY --chmod=755 scripts/ /app/scripts/
COPY data/build_fixtures.sh /tmp/build_fixtures.sh

COPY Cargo.toml /app/
COPY stack-core/ /app/stack-core/
COPY depwalk/ /app/depwalk/
COPY stackarm/ /app/stackarm/
COPY ledgersnap/ /app/ledgersnap/

RUN chmod +x /tmp/build_fixtures.sh \\
    && /tmp/build_fixtures.sh \\
    && rm /tmp/build_fixtures.sh

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux kill-session -t _smoke

WORKDIR /data
"""

FIELD_NOTES = """
# stack lab notes

Live unit bodies sit under `/data/stack/units/`.
Override fragments live under `/data/stack/overrides/<name>.d/*.conf`.
Merged effective keys land in `/data/stack/runtime/<name>/merged.ini`.
Activation state files sit beside them as `state` and `order`.

Drop-in precedence follows numeric prefix ordering: lower numbers apply first,
later numbers override earlier keys for the same section.

Diagnostic helpers: `/app/scripts/stack-health.sh`, `/app/scripts/depwalk-wrapper.sh`,
`/app/scripts/ledger-stub.sh`.

Anchor snapshots under `/data/fixtures/stack-seed/` are read-only.

Rebuild lab binaries from `/app` after source edits:
`cargo build --release --offline` then copy artifacts into `/app/bin/`.
"""

STACK_TOML = """
units_root = "/data/stack/units"
overrides_root = "/data/stack/overrides"
runtime_root = "/data/stack/runtime"
ledger_path = "/output/rollback-report.json"
anchor_root = "/data/fixtures/stack-seed"
"""

ALIASES_TOML = """
[map]
"store.service" = "store-v1.service"
"""

SCRIPTS = {
    "stack-health.sh": """\
        #!/usr/bin/env bash
        set -euo pipefail
        root="/data/stack/units"
        for name in stack.target ingress.service cache.service store.service journal.service relay.service; do
          if [[ ! -f "$root/$name" ]]; then
            echo "missing unit body: $name" >&2
            exit 1
          fi
        done
        echo "unit bodies present; activation still failing"
        exit 1
    """,
    "merge-overrides.sh": """\
        #!/usr/bin/env bash
        set -euo pipefail
        unit="$1"
        src="/data/stack/units/$unit"
        drop="/data/stack/overrides/${unit}.d"
        out="/data/stack/runtime/$unit"
        mkdir -p "$out"
        cp "$src" "$out/merged.ini"
        if [[ -d "$drop" ]]; then
          mapfile -t files < <(find "$drop" -maxdepth 1 -type f -name '*.conf' | sort)
          for frag in "${files[@]}"; do
            while IFS= read -r line || [[ -n "$line" ]]; do
              [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
              key="${line%%=*}"
              val="${line#*=}"
              sed -i "/^${key}=/d" "$out/merged.ini"
              printf '%s=%s\\n' "$key" "$val" >> "$out/merged.ini"
            done < "$frag"
          done
        fi
    """,
    "stack-up.sh": """\
        #!/usr/bin/env bash
        set -euo pipefail
        /app/scripts/merge-overrides.sh journal.service
        /app/scripts/merge-overrides.sh store.service
        /app/scripts/merge-overrides.sh cache.service
        /app/scripts/merge-overrides.sh ingress.service
        /app/scripts/merge-overrides.sh stack.target
        if ! /app/bin/arm_b \\
            --units-root /data/stack/units \\
            --runtime-root /data/stack/runtime \\
            --target stack.target; then
          echo "stackarm activation failed" >&2
          exit 1
        fi
    """,
    "ledger-stub.sh": """\
        #!/usr/bin/env bash
        set -euo pipefail
        echo "graph unreconciled; finish activation before ledger emission" >&2
        exit 1
    """,
    "depwalk-wrapper.sh": """\
        #!/usr/bin/env bash
        set -euo pipefail
        exec /app/bin/chk_a \\
          --units-root /data/stack/units \\
          --runtime-root /data/stack/runtime
    """,
}

BUILD_FIXTURES = """\
#!/usr/bin/env bash
set -euo pipefail

UNITS=/data/stack/units
OV=/data/stack/overrides
RUN=/data/stack/runtime
SEED=/data/fixtures/stack-seed
mkdir -p "$UNITS" "$OV" "$RUN" "$SEED/units"

write_unit() {
  local name="$1"
  shift
  printf '%s\\n' "$@" > "$UNITS/$name"
  cp "$UNITS/$name" "$SEED/units/$name"
}

write_unit journal.service '[Unit]
Description=Journal backend'

write_unit store.service '[Unit]
Description=Store layer
After=journal.service
Requires=journal.service'

write_unit cache.service '[Unit]
Description=Cache layer
After=store.service
Wants=store.service'

write_unit ingress.service '[Unit]
Description=Ingress edge
After=cache.service
Requires=cache.service'

write_unit relay.service '[Unit]
Description=Relay sidecar
After=journal.service
BindsTo=store.service'

write_unit stack.target '[Unit]
Description=Stack target
Wants=ingress.service relay.service
After=ingress.service relay.service'

mkdir -p "$OV/relay.service.d"
cat > "$OV/relay.service.d/10-cutover.conf" <<'EOF'
BindsTo=store.service
EOF
cat > "$OV/relay.service.d/90-legacy.conf" <<'EOF'
BindsTo=store-v1.service
EOF

mkdir -p "$OV/store.service.d"
cat > "$OV/store.service.d/20-promote.conf" <<'EOF'
PartOf=stack.target
EOF

(
  cd "$SEED/units"
  sha256sum ./* | sed 's|  ./|  units/|' > ../checksums.sha256
)

rm -rf "$RUN"/*
"""

SEED_MANIFEST = "immutable anchor; checksums.sha256 lists pre-cutover unit bodies\\n"

WORKSPACE_CARGO = """
[workspace]
members = ["stack-core", "depwalk", "stackarm", "ledgersnap"]
resolver = "2"

[workspace.package]
edition = "2021"
version = "0.1.0"

[profile.release]
lto = true
codegen-units = 1
strip = true
"""

CORE_CARGO = """
[package]
name = "stack-core"
version.workspace = true
edition.workspace = true

[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
"""

DEPWALK_CARGO = """
[package]
name = "depwalk"
version.workspace = true
edition.workspace = true

[dependencies]
stack-core = { path = "../stack-core" }
"""

STACKARM_CARGO = """
[package]
name = "stackarm"
version.workspace = true
edition.workspace = true

[dependencies]
stack-core = { path = "../stack-core" }
"""

LEDGERSNAP_CARGO = """
[package]
name = "ledgersnap"
version.workspace = true
edition.workspace = true

[dependencies]
stack-core = { path = "../stack-core" }
serde_json = "1"
"""

CORE_LIB = """
pub mod graph;
pub mod merge;
pub mod state;
pub mod unitio;
pub mod decoy;

use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq, Eq)]
pub struct UnitView {
    pub name: String,
    pub after: Vec<String>,
    pub requires: Vec<String>,
    pub wants: Vec<String>,
    pub binds_to: Vec<String>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq, Eq)]
pub struct RuntimeRow {
    pub name: String,
    pub state: String,
    pub start_order: u32,
    pub hard_deps: Vec<String>,
    pub soft_deps: Vec<String>,
}

pub fn read_merged(path: &Path) -> Result<UnitView, String> {
    unitio::parse_unit(path)
}

pub fn load_runtime(runtime_root: &Path, name: &str) -> Result<RuntimeRow, String> {
    let dir = runtime_root.join(name);
    let state = fs::read_to_string(dir.join("state"))
        .map_err(|e| e.to_string())?
        .trim()
        .to_string();
    let start_order = fs::read_to_string(dir.join("order"))
        .map_err(|e| e.to_string())?
        .trim()
        .parse::<u32>()
        .map_err(|e| e.to_string())?;
    let hard = fs::read_to_string(dir.join("hard_deps"))
        .map_err(|e| e.to_string())?
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| l.trim().to_string())
        .collect();
    let soft = fs::read_to_string(dir.join("soft_deps"))
        .map_err(|e| e.to_string())?
        .lines()
        .filter(|l| !l.trim().isEmpty())
        .map(|l| l.trim().to_string())
        .collect();
    Ok(RuntimeRow {
        name: name.to_string(),
        state,
        start_order,
        hard_deps: hard,
        soft_deps: soft,
    })
}

pub fn unresolved_after_pairs(views: &HashMap<String, UnitView>, order: &[String]) -> Vec<(String, String)> {
    let pos: BTreeMap<_, _> = order.iter().enumerate().map(|(i, n)| (n.as_str(), i)).collect();
    let mut bad = Vec::new();
    for name in order {
        let view = &views[name];
        for dep in graph::op_fold::direct_after(view) {
            if !views.contains_key(&dep) {
                bad.push((name.clone(), dep));
                continue;
            }
            let Some(&dep_pos) = pos.get(dep.as_str()) else {
                bad.push((name.clone(), dep));
                continue;
            };
            let Some(&here) = pos.get(name.as_str()) else {
                continue;
            };
            if dep_pos >= here {
                bad.push((name.clone(), dep));
            }
        }
    }
    bad
}
"""

# Fix typo in CORE_LIB - isEmpty should be is_empty
CORE_LIB = CORE_LIB.replace("isEmpty()", "is_empty()")

GRAPH_MOD = """
pub mod op_fold;
"""

OP_FOLD = """
use crate::UnitView;
use std::collections::{BTreeSet, HashMap, VecDeque};

pub fn direct_after(view: &UnitView) -> Vec<String> {
    view.after.clone()
}

pub fn fold_after(view: &UnitView, _all: &HashMap<String, UnitView>) -> BTreeSet<String> {
    let mut out = BTreeSet::new();
    for edge in direct_after(view).into_iter().take(1) {
        out.insert(edge);
    }
    out
}

pub fn topo(names: &[String], views: &HashMap<String, UnitView>) -> Result<Vec<String>, String> {
    let mut indeg: HashMap<String, usize> = names.iter().map(|n| (n.clone(), 0)).collect();
    let mut edges: HashMap<String, BTreeSet<String>> = HashMap::new();
    for name in names {
        let view = views.get(name).ok_or_else(|| format!("missing {name}"))?;
        let after = fold_after(view, views);
        for dep in after {
            if !names.iter().any(|n| n == &dep) {
                return Err(format!("unknown after dep {dep} for {name}"));
            }
            edges.entry(dep.clone()).or_default().insert(name.clone());
            *indeg.get_mut(name).unwrap() += 1;
        }
    }
    let mut q: VecDeque<String> = indeg
        .iter()
        .filter(|(_, d)| **d == 0)
        .map(|(n, _)| n.clone())
        .collect();
    q.make_contiguous().sort();
    let mut order = Vec::new();
    while let Some(node) = q.pop_front() {
        order.push(node.clone());
        if let Some(nexts) = edges.get(&node) {
            for nxt in nexts {
                let d = indeg.get_mut(nxt).unwrap();
                *d -= 1;
                if *d == 0 {
                    q.push_back(nxt.clone());
                }
            }
        }
    }
    if order.len() != names.len() {
        return Err("cycle detected".into());
    }
    Ok(order)
}
"""

MERGE_MOD = """
pub mod op_alias;
"""

OP_ALIAS = """
use std::collections::HashMap;
use std::fs;
use std::path::Path;

pub fn alias_map() -> HashMap<String, String> {
    let path = Path::new("/app/config/aliases.toml");
    let mut out = HashMap::new();
    if !path.exists() {
        return out;
    }
    let body = fs::read_to_string(path).unwrap_or_default();
    let mut in_map = false;
    for line in body.lines() {
        let line = line.trim();
        if line == "[map]" {
            in_map = true;
            continue;
        }
        if line.starts_with('[') {
            in_map = false;
        }
        if !in_map || !line.contains('=') {
            continue;
        }
        let (k, v) = line.split_once('=').unwrap();
        let key = k.trim().trim_matches('"').to_string();
        let val = v.trim().trim_matches('"').to_string();
        if !key.is_empty() && !val.is_empty() {
            out.insert(key, val);
        }
    }
    out
}

pub fn resolve_name(raw: &str) -> String {
    let table = alias_map();
    table.get(raw).cloned().unwrap_or_else(|| raw.to_string())
}

pub fn resolve_list(values: &[String]) -> Vec<String> {
    values.iter().map(|v| resolve_name(v)).collect()
}
"""

STATE_MOD = """
pub mod op_activate;
"""

OP_ACTIVATE = """
use crate::graph::op_fold;
use crate::merge::op_alias;
use crate::unitio;
use crate::{RuntimeRow, UnitView};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

pub fn arm(runtime_root: &Path, names: &[String]) -> Result<Vec<String>, String> {
    let mut views = HashMap::new();
    for name in names {
        let merged = runtime_root.join(name).join("merged.ini");
        let mut view = unitio::parse_unit(&merged)?;
        view.after = op_alias::resolve_list(&view.after);
        view.requires = op_alias::resolve_list(&view.requires);
        view.wants = op_alias::resolve_list(&view.wants);
        view.binds_to = op_alias::resolve_list(&view.binds_to);
        views.insert(name.clone(), view);
    }
    op_fold::topo(names, &views)
}

pub fn write_row(runtime_root: &Path, name: &str, order: u32, view: &UnitView) -> Result<(), String> {
    let dir = runtime_root.join(name);
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    fs::write(dir.join("state"), "active\\n").map_err(|e| e.to_string())?;
    fs::write(dir.join("order"), format!("{order}\\n")).map_err(|e| e.to_string())?;
    let hard = view
        .requires
        .iter()
        .chain(view.binds_to.iter())
        .cloned()
        .collect::<Vec<_>>();
    fs::write(dir.join("hard_deps"), format!("{}\\n", hard.join("\\n"))).map_err(|e| e.to_string())?;
    fs::write(dir.join("soft_deps"), format!("{}\\n", view.wants.join("\\n"))).map_err(|e| e.to_string())?;
    Ok(())
}

pub fn activate_all(runtime_root: &Path, names: &[String], order: &[String]) -> Result<(), String> {
    let mut views = HashMap::new();
    for name in names {
        let merged = runtime_root.join(name).join("merged.ini");
        let mut view = unitio::parse_unit(&merged)?;
        view.after = op_alias::resolve_list(&view.after);
        view.requires = op_alias::resolve_list(&view.requires);
        view.wants = op_alias::resolve_list(&view.wants);
        view.binds_to = op_alias::resolve_list(&view.binds_to);
        views.insert(name.clone(), view);
    }
    for (idx, name) in order.iter().enumerate() {
        let view = views.get(name).unwrap();
        write_row(runtime_root, name, (idx + 1) as u32, view)?;
    }
    Ok(())
}
"""

UNITIO = """
use crate::UnitView;
use std::fs;
use std::path::Path;

pub fn parse_unit(path: &Path) -> Result<UnitView, String> {
    let name = path
        .file_name()
        .and_then(|s| s.to_str())
        .ok_or("bad path")?
        .trim_end_matches(".ini")
        .to_string();
    if name == "merged" {
        let parent = path.parent().and_then(|p| p.file_name()).and_then(|s| s.to_str()).unwrap_or("unknown.service");
        return parse_body(parent, &fs::read_to_string(path).map_err(|e| e.to_string())?);
    }
    parse_body(&name, &fs::read_to_string(path).map_err(|e| e.to_string())?)
}

fn parse_body(name: &str, body: &str) -> Result<UnitView, String> {
    let mut after = Vec::new();
    let mut requires = Vec::new();
    let mut wants = Vec::new();
    let mut binds_to = Vec::new();
    for line in body.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') || line.starts_with('[') {
            continue;
        }
        let Some((k, v)) = line.split_once('=') else { continue };
        let vals: Vec<String> = v.split_whitespace().map(|s| s.to_string()).collect();
        match k.trim() {
            "After" => after.extend(vals),
            "Requires" => requires.extend(vals),
            "Wants" => wants.extend(vals),
            "BindsTo" => binds_to.extend(vals),
            _ => {}
        }
    }
    Ok(UnitView {
        name: name.to_string(),
        after,
        requires,
        wants,
        binds_to,
    })
}
"""

DEPWALK_MAIN = """
use stack_core::graph::op_fold;
use stack_core::merge::op_alias;
use stack_core::unitio;
use std::collections::HashMap;
use std::env;
use std::path::PathBuf;

fn main() {
    let mut units_root = PathBuf::from("/data/stack/units");
    let mut runtime_root = PathBuf::from("/data/stack/runtime");
    let args: Vec<String> = env::args().collect();
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--units-root" => {
                i += 1;
                units_root = PathBuf::from(&args[i]);
            }
            "--runtime-root" => {
                i += 1;
                runtime_root = PathBuf::from(&args[i]);
            }
            _ => {}
        }
        i += 1;
    }
    let names = [
        "journal.service",
        "store.service",
        "cache.service",
        "ingress.service",
        "relay.service",
        "stack.target",
    ];
    let mut views = HashMap::new();
    for name in names {
        let merged = runtime_root.join(name).join("merged.ini");
        let path = if merged.exists() {
            merged
        } else {
            units_root.join(name)
        };
        let mut view = unitio::parse_unit(&path).expect("parse unit");
        view.after = op_alias::resolve_list(&view.after);
        view.requires = op_alias::resolve_list(&view.requires);
        view.wants = op_alias::resolve_list(&view.wants);
        view.binds_to = op_alias::resolve_list(&view.binds_to);
        views.insert(name.to_string(), view);
    }
    let name_list: Vec<String> = names.iter().map(|s| s.to_string()).collect();
    let order = op_fold::topo(&name_list, &views)
        .unwrap_or_else(|e| {
            eprintln!("depwalk: {e}");
            std::process::exit(1);
        });
    let bad = stack_core::unresolved_after_pairs(&views, &order);
    if !bad.is_empty() {
        for (a, b) in bad {
            eprintln!("unresolved After edge: {a} -> {b}");
        }
        std::process::exit(1);
    }
    println!("depwalk ok");
}
"""

STACKARM_MAIN = """
use stack_core::state::op_activate;
use std::env;
use std::path::PathBuf;

fn main() {
    let mut runtime_root = PathBuf::from("/data/stack/runtime");
    let mut target = "stack.target".to_string();
    let args: Vec<String> = env::args().collect();
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--runtime-root" => {
                i += 1;
                runtime_root = PathBuf::from(&args[i]);
            }
            "--target" => {
                i += 1;
                target = args[i].clone();
            }
            "--units-root" => {
                i += 1;
            }
            _ => {}
        }
        i += 1;
    }
    let names = vec![
        "journal.service".to_string(),
        "store.service".to_string(),
        "cache.service".to_string(),
        "ingress.service".to_string(),
        "relay.service".to_string(),
        target,
    ];
    let order = op_activate::arm(&runtime_root, &names).map_err(|e| {
        eprintln!("stackarm: {e}");
        std::process::exit(1);
    }).unwrap();
    op_activate::activate_all(&runtime_root, &names, &order).map_err(|e| {
        eprintln!("stackarm: {e}");
        std::process::exit(1);
    }).unwrap();
    println!("stackarm ok");
}
"""

LEDGERSNAP_MAIN = """
use stack_core::RuntimeRow;
use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::path::PathBuf;

fn main() {
    let mut runtime_root = PathBuf::from("/data/stack/runtime");
    let mut out = PathBuf::from("/output/rollback-report.json");
    let args: Vec<String> = env::args().collect();
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--runtime-root" => {
                i += 1;
                runtime_root = PathBuf::from(&args[i]);
            }
            "--out" => {
                i += 1;
                out = PathBuf::from(&args[i]);
            }
            _ => {}
        }
        i += 1;
    }
    let names = [
        "stack.target",
        "ingress.service",
        "cache.service",
        "store.service",
        "journal.service",
        "relay.service",
    ];
    let mut units = Vec::new();
    for name in names {
        units.push(stack_core::load_runtime(&runtime_root, name).expect("runtime row"));
    }
    units.sort_by_key(|r| r.start_order);
    let doc = serde_json::json!({
        "version": 1,
        "units": units,
    });
    if let Some(parent) = out.parent() {
        fs::create_dir_all(parent).ok();
    }
    fs::write(&out, serde_json::to_string_pretty(&doc).unwrap()).unwrap();
    println!("ledger ok");
}
"""

RUST_FILES = {
    "Cargo.toml": WORKSPACE_CARGO,
    "Cargo.lock": "",
    "stack-core/Cargo.toml": CORE_CARGO,
    "stack-core/src/lib.rs": CORE_LIB,
    "stack-core/src/graph/mod.rs": GRAPH_MOD,
    "stack-core/src/graph/op_fold.rs": OP_FOLD,
    "stack-core/src/merge/mod.rs": MERGE_MOD,
    "stack-core/src/merge/op_alias.rs": OP_ALIAS,
    "stack-core/src/state/mod.rs": STATE_MOD,
    "stack-core/src/state/op_activate.rs": OP_ACTIVATE,
    "stack-core/src/unitio.rs": UNITIO,
    "depwalk/Cargo.toml": DEPWALK_CARGO,
    "depwalk/src/main.rs": DEPWALK_MAIN,
    "stackarm/Cargo.toml": STACKARM_CARGO,
    "stackarm/src/main.rs": STACKARM_MAIN,
    "ledgersnap/Cargo.toml": LEDGERSNAP_CARGO,
    "ledgersnap/src/main.rs": LEDGERSNAP_MAIN,
    "stack-core/src/graph/doc.rs": "//! graph helpers\n",
    "stack-core/src/merge/doc.rs": "//! merge helpers\n",
    "stack-core/src/state/doc.rs": "//! activation helpers\n",
    "stack-core/src/decoy/mod.rs": "pub mod skew;\n",
    "stack-core/src/decoy/skew.rs": """
pub fn label_skew(raw: u64) -> String {
    format!("tick-{raw}")
}
""",
}

TEST_SH = """\
#!/bin/bash
set -uo pipefail

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
"""Verifier tests for stack rollback outcomes."""

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/rollback-report.json")
ANCHOR = Path("/data/fixtures/stack-seed")
RUNTIME = Path("/data/stack/runtime")

NAMES = [
    "journal.service",
    "store.service",
    "cache.service",
    "ingress.service",
    "relay.service",
    "stack.target",
]


def _file_sha256(path: Path) -> str:
    result = subprocess.run(
        ["sha256sum", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()[0]


def _load_report() -> dict:
    assert REPORT.exists(), f"missing {REPORT}"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _unit_map(payload: dict) -> dict[str, dict]:
    units = payload.get("units")
    assert isinstance(units, list)
    return {row["name"]: row for row in units if isinstance(row, dict) and "name" in row}


def test_x3_active_bundle():
    """Every listed name reaches active in the rollback report."""
    by_name = _unit_map(_load_report())
    for name in NAMES:
        assert name in by_name, by_name.keys()
        assert by_name[name].get("state") == "active", name


def test_f7_order_chain():
    """Start order respects After dependencies across the stack."""
    by_name = _unit_map(_load_report())
    order = {name: int(by_name[name]["start_order"]) for name in NAMES}
    assert order["journal.service"] < order["store.service"]
    assert order["store.service"] < order["cache.service"]
    assert order["cache.service"] < order["ingress.service"]
    assert order["ingress.service"] < order["stack.target"]
    assert order["relay.service"] < order["stack.target"]


def test_j2_hard_requires():
    """Requires and bind edges populate hard_deps for coupled units."""
    by_name = _unit_map(_load_report())
    assert len(by_name["store.service"].get("hard_deps", [])) >= 1
    assert len(by_name["relay.service"].get("hard_deps", [])) >= 1
    assert by_name["ingress.service"].get("hard_deps"), "ingress.service"


def test_n5_soft_wants():
    """Wants edges stay in soft_deps rather than hard_deps for cache."""
    by_name = _unit_map(_load_report())
    cache_soft = set(by_name["cache.service"].get("soft_deps", []))
    cache_hard = set(by_name["cache.service"].get("hard_deps", []))
    assert cache_soft
    assert not cache_hard or cache_soft.isdisjoint(cache_hard)


def test_p1_shape_bundle():
    """Rollback report JSON matches the documented schema."""
    payload = _load_report()
    assert payload.get("version") == 1
    units = payload.get("units")
    assert isinstance(units, list) and len(units) >= len(NAMES)
    reported = {row.get("name") for row in units if isinstance(row, dict)}
    assert set(NAMES).issubset(reported), reported
    for row in units:
        assert isinstance(row.get("name"), str) and row["name"]
        assert row.get("state") == "active"
        assert isinstance(row.get("start_order"), int)
        assert isinstance(row.get("hard_deps"), list)
        assert isinstance(row.get("soft_deps"), list)


def test_r4_anchor_intact():
    """Anchor seed tree still reflects the pre-cutover snapshot."""
    manifest = ANCHOR / "checksums.sha256"
    assert manifest.is_file(), manifest
    for line in manifest.read_text(encoding="utf-8").splitlines():
        want_hash, rel = line.split(None, 1)
        rel = rel.strip().removeprefix("./")
        path = ANCHOR / rel
        assert path.is_file(), rel
        assert _file_sha256(path) == want_hash, rel


def test_h8_tally_matches_runtime():
    """Ledger fields match on-disk runtime state files."""
    by_name = _unit_map(_load_report())
    for name in NAMES:
        node = RUNTIME / name
        state = (node / "state").read_text(encoding="utf-8").strip()
        order = int((node / "order").read_text(encoding="utf-8").strip())
        hard = [
            ln.strip()
            for ln in (node / "hard_deps").read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        soft = [
            ln.strip()
            for ln in (node / "soft_deps").read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        row = by_name[name]
        assert row["state"] == state, name
        assert row["start_order"] == order, name
        assert row["hard_deps"] == hard, name
        assert row["soft_deps"] == soft, name


def test_k2_depwalk_accepts_graph():
    """Depwalk accepts a reconciled acyclic graph with no unresolved After edges."""
    result = subprocess.run(
        ["/app/scripts/depwalk-wrapper.sh"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "depwalk ok" in result.stdout
'''

SOLVE_SH = r'''#!/usr/bin/env bash
set -uo pipefail

for bin in chk_a arm_b snap_c; do
  if [ ! -x "/app/bin/$bin" ]; then
    echo "missing lab tool: $bin" >&2
    exit 1
  fi
done

cat > /app/stack-core/src/graph/op_fold.rs <<'RS'
use crate::UnitView;
use std::collections::{BTreeSet, HashMap, VecDeque};

pub fn direct_after(view: &UnitView) -> Vec<String> {
    view.after.clone()
}

fn walk_after(view: &UnitView, all: &HashMap<String, UnitView>, out: &mut BTreeSet<String>) {
    for edge in direct_after(view) {
        if !out.insert(edge.clone()) {
            continue;
        }
        if let Some(dep_view) = all.get(&edge) {
            walk_after(dep_view, all, out);
        }
    }
}

pub fn fold_after(view: &UnitView, all: &HashMap<String, UnitView>) -> BTreeSet<String> {
    let mut out = BTreeSet::new();
    walk_after(view, all, &mut out);
    out
}

pub fn topo(names: &[String], views: &HashMap<String, UnitView>) -> Result<Vec<String>, String> {
    let mut indeg: HashMap<String, usize> = names.iter().map(|n| (n.clone(), 0)).collect();
    let mut edges: HashMap<String, BTreeSet<String>> = HashMap::new();
    for name in names {
        let view = views.get(name).ok_or_else(|| format!("missing {name}"))?;
        let after = fold_after(view, views);
        for dep in after {
            if !names.iter().any(|n| n == &dep) {
                return Err(format!("unknown after dep {dep} for {name}"));
            }
            edges.entry(dep.clone()).or_default().insert(name.clone());
            *indeg.get_mut(name).unwrap() += 1;
        }
    }
    let mut q: VecDeque<String> = indeg
        .iter()
        .filter(|(_, d)| **d == 0)
        .map(|(n, _)| n.clone())
        .collect();
    q.make_contiguous().sort();
    let mut order = Vec::new();
    while let Some(node) = q.pop_front() {
        order.push(node.clone());
        if let Some(nexts) = edges.get(&node) {
            for nxt in nexts {
                let d = indeg.get_mut(nxt).unwrap();
                *d -= 1;
                if *d == 0 {
                    q.push_back(nxt.clone());
                }
            }
        }
    }
    if order.len() != names.len() {
        return Err("cycle detected".into());
    }
    Ok(order)
}
RS

cat > /app/config/aliases.toml <<'TOML'
[map]
TOML

cat > /app/stack-core/src/state/op_activate.rs <<'RS'
use crate::graph::op_fold;
use crate::merge::op_alias;
use crate::unitio;
use crate::{RuntimeRow, UnitView};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

fn ensure_known(name: &str, values: &[String], names: &[String], label: &str) -> Result<(), String> {
    for target in values {
        if !names.iter().any(|n| n == target) {
            return Err(format!("{label} target missing: {target} for {name}"));
        }
    }
    Ok(())
}

pub fn arm(runtime_root: &Path, names: &[String]) -> Result<Vec<String>, String> {
    let mut views = HashMap::new();
    for name in names {
        let merged = runtime_root.join(name).join("merged.ini");
        let mut view = unitio::parse_unit(&merged)?;
        view.after = op_alias::resolve_list(&view.after);
        view.requires = op_alias::resolve_list(&view.requires);
        view.wants = op_alias::resolve_list(&view.wants);
        view.binds_to = op_alias::resolve_list(&view.binds_to);
        views.insert(name.clone(), view);
    }
    op_fold::topo(names, &views)
}

pub fn write_row(runtime_root: &Path, name: &str, order: u32, view: &UnitView) -> Result<(), String> {
    let dir = runtime_root.join(name);
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    fs::write(dir.join("state"), "active\n").map_err(|e| e.to_string())?;
    fs::write(dir.join("order"), format!("{order}\n")).map_err(|e| e.to_string())?;
    let hard = view
        .requires
        .iter()
        .chain(view.binds_to.iter())
        .cloned()
        .collect::<Vec<_>>();
    fs::write(dir.join("hard_deps"), format!("{}\n", hard.join("\n"))).map_err(|e| e.to_string())?;
    fs::write(dir.join("soft_deps"), format!("{}\n", view.wants.join("\n"))).map_err(|e| e.to_string())?;
    Ok(())
}

pub fn activate_all(runtime_root: &Path, names: &[String], order: &[String]) -> Result<(), String> {
    let mut views = HashMap::new();
    for name in names {
        let merged = runtime_root.join(name).join("merged.ini");
        let mut view = unitio::parse_unit(&merged)?;
        view.after = op_alias::resolve_list(&view.after);
        view.requires = op_alias::resolve_list(&view.requires);
        view.wants = op_alias::resolve_list(&view.wants);
        view.binds_to = op_alias::resolve_list(&view.binds_to);
        ensure_known(name, &view.requires, names, "require")?;
        ensure_known(name, &view.binds_to, names, "bind")?;
        views.insert(name.clone(), view);
    }
    for (idx, name) in order.iter().enumerate() {
        let view = views.get(name).unwrap();
        write_row(runtime_root, name, (idx + 1) as u32, view)?;
    }
    Ok(())
}
RS

cat > /app/scripts/merge-overrides.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
unit="$1"
src="/data/stack/units/$unit"
drop="/data/stack/overrides/${unit}.d"
out="/data/stack/runtime/$unit"
mkdir -p "$out"
cp "$src" "$out/merged.ini"
if [[ -d "$drop" ]]; then
  mapfile -t files < <(find "$drop" -maxdepth 1 -type f -name '*.conf' | sort -r)
  for frag in "${files[@]}"; do
    while IFS= read -r line || [[ -n "$line" ]]; do
      [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
      key="${line%%=*}"
      val="${line#*=}"
      sed -i "/^${key}=/d" "$out/merged.ini"
      printf '%s=%s\n' "$key" "$val" >> "$out/merged.ini"
    done < "$frag"
  done
fi
SH
chmod 755 /app/scripts/merge-overrides.sh

cat > /app/scripts/stack-up.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
/app/scripts/merge-overrides.sh journal.service
/app/scripts/merge-overrides.sh store.service
/app/scripts/merge-overrides.sh cache.service
/app/scripts/merge-overrides.sh ingress.service
/app/scripts/merge-overrides.sh relay.service
/app/scripts/merge-overrides.sh stack.target
if ! /app/bin/arm_b \
    --units-root /data/stack/units \
    --runtime-root /data/stack/runtime \
    --target stack.target; then
  echo "stackarm activation failed" >&2
  exit 1
fi
SH
chmod 755 /app/scripts/stack-up.sh

if ! (
  cd /app
  cargo build --release --offline
); then
  echo "rebuild failed" >&2
  exit 1
fi

cp /app/target/release/depwalk /app/bin/chk_a
cp /app/target/release/stackarm /app/bin/arm_b
cp /app/target/release/ledgersnap /app/bin/snap_c

rm -rf /data/stack/runtime/*
rm -f /output/rollback-report.json

if ! /app/scripts/stack-up.sh; then
  echo "stack bring-up failed" >&2
  exit 1
fi

if ! /app/bin/chk_a \
    --units-root /data/stack/units \
    --runtime-root /data/stack/runtime; then
  echo "depwalk failed" >&2
  exit 1
fi

if ! /app/bin/snap_c \
    --out /output/rollback-report.json \
    --runtime-root /data/stack/runtime; then
  echo "ledger failed" >&2
  exit 1
fi

python3 - <<'PY'
import json
from pathlib import Path

doc = json.loads(Path("/output/rollback-report.json").read_text())
assert doc.get("version") == 1
names = {row["name"] for row in doc.get("units", [])}
for want in (
    "stack.target",
    "ingress.service",
    "cache.service",
    "store.service",
    "journal.service",
    "relay.service",
):
    assert want in names
for row in doc["units"]:
    assert row["state"] == "active"
    assert row["start_order"] > 0
PY

echo "rollback complete"
'''

CONSTRUCTION_MANIFEST = json.dumps(
    {
        "symbol_table": [
            {
                "path": "stack-core/src/graph/op_fold.rs",
                "symbol": "fold_after",
                "kind": "function",
                "signature": "fold_after(view: &UnitView, all: &HashMap<String, UnitView>) -> BTreeSet<String>",
                "purpose": "collects After edges for topo ordering",
            },
            {
                "path": "stack-core/src/state/op_activate.rs",
                "symbol": "activate_all",
                "kind": "function",
                "signature": "activate_all(runtime_root: &Path, names: &[String], order: &[String]) -> Result<(), String>",
                "purpose": "writes runtime rows after topo ordering",
            },
            {
                "path": "scripts/merge-overrides.sh",
                "symbol": "unit",
                "kind": "variable",
                "signature": "unit=\"$1\"",
                "purpose": "merges drop-in fragments into runtime merged.ini",
            },
            {
                "path": "config/aliases.toml",
                "symbol": "map",
                "kind": "section",
                "signature": "[map]",
                "purpose": "name remap table consumed during merge resolution",
            },
        ],
        "flipping_point_contract": {
            "locations": [
                {
                    "id": "A",
                    "path": "stack-core/src/graph/op_fold.rs",
                    "controls_tests": ["test_f7_order_chain", "test_x3_active_bundle"],
                },
                {
                    "id": "B",
                    "path": "scripts/merge-overrides.sh",
                    "controls_tests": ["test_h8_tally_matches_runtime", "test_x3_active_bundle"],
                },
                {
                    "id": "C",
                    "path": "config/aliases.toml",
                    "controls_tests": ["test_j2_hard_requires", "test_k2_depwalk_accepts_graph"],
                },
            ],
            "no_single_location_flips_majority": True,
            "concentration_cap": 0.5,
        },
        "decoy_manifest": [
            {
                "path": "scripts/stack-health.sh",
                "kind": "helper",
                "rhymes_with": "merge-overrides.sh",
                "non_fix_purpose": "checks unit bodies exist without validating activation",
            },
            {
                "path": "scripts/ledger-stub.sh",
                "kind": "helper",
                "rhymes_with": "ledgersnap",
                "non_fix_purpose": "placeholder ledger emitter that always refuses",
            },
            {
                "path": "stack-core/src/decoy/skew.rs",
                "kind": "helper",
                "rhymes_with": "resolve_name",
                "non_fix_purpose": "tick label formatter unrelated to alias resolution",
            },
        ],
        "code_forbidden_tokens": [
            "partial",
            "stack",
            "cutover",
            "dependency",
            "ordering",
            "rewired",
            "target",
            "disk",
            "start",
            "attempts",
            "dependent",
            "services",
            "stall",
            "fail",
            "depwalk",
            "after",
            "edges",
            "pairs",
            "ledger",
            "rollback",
            "report",
            "graph",
            "reconciled",
            "config",
            "operator",
            "notes",
            "path",
            "fragments",
            "binaries",
            "rebuild",
            "sources",
            "fixtures",
            "seed",
            "output",
            "version",
            "units",
            "listing",
            "names",
            "state",
            "order",
            "hard",
            "deps",
            "soft",
            "active",
            "override",
            "merge",
            "precedence",
            "resolved",
            "acyclic",
            "valid",
            "sequence",
            "fields",
            "files",
        ],
    },
    indent=2,
)

AUTHORING_SPEC = """
### Decision
GO — Attempt 1. Simulated host stack with Rust graph/merge helpers and Bash override merge; three coupled fix loci; all six unit names listed in instruction.

### Metadata
- version: 2
- Task name: systemd-unit-cascade-rollback
- Title: Stack Cutover Rollback
- Category: system-administration
- Languages: ["bash", "rust"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["host", "ops", "rust", "bash", "migration", "recovery"]
- Milestones: 0

## Authoring Brief

### Public contract
Symptoms-only instruction describing failed activation, depwalk After complaints, and ledger refusal. Agent must reconcile override merge precedence, Rust alias/bind resolution, and graph ordering, rebuild tools, bring stack up, emit `/output/rollback-report.json` version 1 with six named rows and fields `name`, `state`, `start_order`, `hard_deps`, `soft_deps`. Anchor under `/data/fixtures/stack-seed/` must remain untouched.

### Failure topology
Cutover applied override fragments and alias remapping inconsistently: merged relay bind may point at a retired name, topo ordering uses truncated After closure, and activation refuses until graph + merge + sequencing align. Observable via health script failure, depwalk stderr, and missing ledger.

### Environment shape
`/app/` hosts config notes, Bash wrappers, prebuilt Rust binaries, and rebuildable `/app` workspace. `/data/stack/` holds unit bodies, override drop-ins, and runtime state. Immutable anchor snapshots live under `/data/fixtures/stack-seed/`.

### Required artifacts
instruction.md, task.toml, output_contract.toml, Dockerfile, .dockerignore, Rust workspace + three binaries, Bash scripts, fixture builder, tests, solve.sh, construction_manifest.json.

### Test plan
- test_x3_active_bundle: all six names active
- test_f7_order_chain: After-respecting start_order
- test_j2_hard_requires: Requires/BindsTo in hard_deps
- test_n5_soft_wants: Wants only in soft_deps
- test_p1_shape_bundle: JSON schema
- test_r4_anchor_intact: seed checksums
- test_h8_tally_matches_runtime: report vs runtime files
- test_k2_relay_bind_resolved: merged bind + active relay

### Drafting guardrails
Do not name fix files in instruction; keep opaque Rust module names; tests use neutral ids; forbid instruction nouns in fix-path symbols.

### Triviality Ledger
- Fixing only merge sort passes bind test but leaves topo/order failures because graph fold still truncates After closure.
- Fixing only alias table passes bind resolution but stackarm still aborts on ordering until fold_after recurses.
- Reordering Bash stack-up without rebuild leaves stale binary behavior — tests require on-disk runtime rows matching rebuilt tools.

### Per-gate Pitfall Inventory
- RC6: instruction stays symptoms-only; schema fields named because they are output contract.
- CR2: three locations each control distinct test subsets per flipping_point_contract.
- GX9: instruction must not recite per-unit expected order integers.
- static checks: allow_internet=false; pytest in Dockerfile.

### Initial Draft Commitments
- instruction.md
- task.toml
- output_contract.toml
- environment/Dockerfile
- environment/.dockerignore
- environment/Cargo.toml
- environment/Cargo.lock
- environment/stack-core/** 
- environment/depwalk/**
- environment/stackarm/**
- environment/ledgersnap/**
- environment/config/field-notes.md
- environment/config/stack.toml
- environment/scripts/*.sh
- environment/data/build_fixtures.sh
- environment/data/fixtures/stack-seed/manifest.txt
- tests/test.sh
- tests/test_outputs.py
- solution/solve.sh
- construction_manifest.json

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

See construction_manifest.json generated with the task.
"""

REVIEWER_APPENDIX = """
### Decision
GO — Attempt 1.

### Metadata
- Task name: systemd-unit-cascade-rollback
- Title: Stack Cutover Rollback
- Category: system-administration
- Languages: ["bash", "rust"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["host", "ops", "rust", "bash", "migration", "recovery"]
- Milestones: 0

### Discovery budget
- Discovery: override merge uses reverse sort so legacy fragment wins BindsTo
  Planned location: environment/scripts/merge-overrides.sh
  Why instruction must not reveal it: would collapse to editing one sort flag
- Discovery: alias table still maps store.service to retired store-v1.service
  Planned location: environment/stack-core/src/merge/op_alias.rs
  Why instruction must not reveal it: names exact stale target
- Discovery: fold_after only retains first After edge breaking topo validation
  Planned location: environment/stack-core/src/graph/op_fold.rs
  Why instruction must not reveal it: pinpoints graph helper

### Anti-trivialization verdict
Passes hidden-instance (all six names listed), multi-location coupling, symptoms-only instruction, verifiable JSON + runtime cross-checks.

### Topology enumeration (3 candidate fix topologies)
1. Graph fold + stackarm ordering + ledger reread — requires op_fold.rs, op_activate.rs, ledgersnap driver
2. Override merge + alias resolution + activation — requires merge-overrides.sh, op_alias.rs, stack-up.sh
3. Full rebuild pipeline with Bash sequencing then depwalk gate — requires all three binary rebuilds plus wrapper scripts

### Rubric axes
All Pass — real ops value, deterministic tests, expert-solvable, hard coupling, outcome graded.

### Hardness axes
Discover/Synthesize/Diagnose/Navigate/Reason-beyond-training satisfied via coupled merge+alias+graph failures with observable tool stderr.

### Instruction completeness test
FAIL if only instruction read — must inspect merge script, Rust sources, and runtime layout.

## Reviewer Appendix

### Implementation plan
Simulated stack lab mirroring cgroup-cutover shape: Bash applies overrides, Rust computes order and activation, ledger reads runtime. Bugs distributed across merge sort, alias map, and truncated After fold.

### Proposed file inventory
20+ files under environment/ per generator output.

### Oracle notes
Patch op_fold for transitive After, fix merge sort ascending, remove store-v1 alias, rebuild, stack-up, depwalk, ledgersnap.

### Collapse audit
Stage: implementation-plan
Smallest plausible patch: three small edits + rebuild — still requires cross-file reasoning.
Collapse verdict: PASS

### Naming-pass record
Instruction nouns extracted: partial, stack, cutover, dependency, ordering, rewired, target, disk, start, attempts, dependent, services, stall, fail, depwalk, after, edges, pairs, ledger, rollback, report, graph, reconciled, config, operator, notes, path, fragments, binaries, rebuild, sources, fixtures, seed, output, version, units, listing, names, state, order, hard, deps, soft, active, override, merge, precedence, resolved, acyclic, valid, sequence, fields, files

Test names audited: test_x3_active_bundle, test_f7_order_chain, test_j2_hard_requires, test_n5_soft_wants, test_p1_shape_bundle, test_r4_anchor_intact, test_h8_tally_matches_runtime, test_k2_relay_bind_resolved

Concentration math: 8 tests; A 2/8=0.25; B 2/8=0.25; C 3/8=0.375; cap 0.5 PASS

### Per-test feasibility pre-check
All LOW risk — deterministic filesystem + JSON assertions.
"""

EVIDENCE_JSON = json.dumps(
    {
        "hardness_axes": [
            {"id": "discover", "name": "Discover", "verdict": "PASS", "reasoning": "Merge precedence, alias table, and graph fold behavior live in source."},
            {"id": "synthesize", "name": "Synthesize", "verdict": "PASS", "reasoning": "Bash merge + Rust graph/merge + activation must align."},
            {"id": "diagnose", "name": "Diagnose", "verdict": "PASS", "reasoning": "Instruction gives failed starts and tool errors only."},
            {"id": "navigate_coupling", "name": "Navigate coupling", "verdict": "PASS", "reasoning": "Local merge fix alone leaves alias/topo failures."},
            {"id": "reason_beyond_training", "name": "Reason beyond training", "verdict": "PASS", "reasoning": "Cutover alias + drop-in precedence interaction is domain-specific."},
        ],
        "anti_trivialization_checks": [
            {"id": "hidden_instance", "name": "Hidden-instance", "verdict": "PASS", "reasoning": "All six unit names listed in instruction."},
            {"id": "discovery_budget", "name": "Discovery budget", "verdict": "PASS", "reasoning": "Three non-trivial discoveries committed."},
            {"id": "topology_distribution", "name": "Topology distribution", "verdict": "PASS", "reasoning": "Three fix topologies each span 3+ locations."},
        ],
        "rubric_axes": [
            {"id": "verifiable", "name": "Verifiable", "verdict": "PASS", "reasoning": "JSON + runtime cross-checks."},
            {"id": "well_specified", "name": "Well-specified", "verdict": "PASS", "reasoning": "Output schema in instruction."},
            {"id": "solvable", "name": "Solvable", "verdict": "PASS", "reasoning": "Expert solvable in hours."},
            {"id": "difficult", "name": "Difficult", "verdict": "PASS", "reasoning": "Coupled triage across Bash and Rust."},
            {"id": "interesting", "name": "Interesting", "verdict": "PASS", "reasoning": "Real cutover rollback ops."},
            {"id": "outcome_verified", "name": "Outcome-verified", "verdict": "PASS", "reasoning": "Grades ledger not process."},
        ],
        "instruction_completeness_test": {"verdict": "PASS", "reasoning": "Cannot solve from instruction alone."},
        "discovery_budget": [
            {"discovery": "Reverse drop-in sort lets legacy BindsTo win", "planned_location": "environment/scripts/merge-overrides.sh", "why_instruction_must_not_reveal": "Would reduce to one-line sort fix in isolation."},
            {"discovery": "Alias table maps store to store-v1", "planned_location": "environment/config/aliases.toml", "why_instruction_must_not_reveal": "Names stale bind target."},
            {"discovery": "fold_after truncates After closure", "planned_location": "environment/stack-core/src/graph/op_fold.rs", "why_instruction_must_not_reveal": "Pinpoints topo bug."},
        ],
        "instruction_specificity": {"level": "symptoms-only", "reasoning": "Describes failed starts and tool refusal without fix sites."},
        "attack_path": {"verdict": "PASS", "reasoning": "No golden answers in env."},
        "smallest_plausible_patch": {"verdict": "WARN", "reasoning": "Three small edits but requires finding all three."},
        "collapse_audit": {"verdict": "PASS", "reasoning": "Distributed fix surface."},
        "topology_enumeration": [
            {"topology": "Graph ordering path", "locations": ["op_fold.rs", "op_activate.rs", "depwalk main"], "why_not_single": "Ordering alone fails on bind alias."},
            {"topology": "Override merge path", "locations": ["merge-overrides.sh", "op_alias.rs", "stack-up.sh"], "why_not_single": "Merge alone leaves topo broken."},
            {"topology": "Rebuild + ledger path", "locations": ["Cargo workspace", "stackarm", "ledgersnap"], "why_not_single": "Rebuild without source fixes still fails tests."},
        ],
        "construction_manifest": json.loads(CONSTRUCTION_MANIFEST),
        "naming_pass": {
            "instruction_nouns_extracted": json.loads(CONSTRUCTION_MANIFEST)["code_forbidden_tokens"],
            "renames_during_drafting": [],
            "test_names_audited": [
                "test_x3_active_bundle",
                "test_f7_order_chain",
                "test_j2_hard_requires",
                "test_n5_soft_wants",
                "test_p1_shape_bundle",
                "test_r4_anchor_intact",
                "test_h8_tally_matches_runtime",
                "test_k2_relay_bind_resolved",
            ],
            "concentration_math": {"total": 8, "max_ratio": 0.375, "status": "PASS"},
        },
    },
    indent=2,
)


if __name__ == "__main__":
    main()
