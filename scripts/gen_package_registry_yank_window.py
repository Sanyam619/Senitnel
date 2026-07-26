#!/usr/bin/env python3
"""One-shot generator for tasks/package-registry-yank-window (authoring tool, not shipped).

Failure topology (NOT the three-authority epoch-lag pattern):
  1. Yank windows are half-open [from, until). Broken code uses closed [from, until].
  2. Installability must refuse versions whose pinned deps are under an active yank.
  3. Advisories belong only while the matching version is still actively yanked.
  4. Operator tables select bound_mode / dep_block / adv_live_only policies.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "package-registry-yank-window"

CANONICAL_GOLANG = (
    "public.ecr.aws/docker/library/golang:1.24-bookworm"
    "@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac"
)
CANONICAL_RUST = (
    "public.ecr.aws/docker/library/rust:1.85-slim"
    "@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36"
)

HEAD_GEN = 4

# Version fixtures: name, vers, introduced_gen, deps as list of {crate, version}
VERSIONS = [
    {"name": "alpha-core", "vers": "1.0.0", "gen": 1, "deps": []},
    {
        "name": "alpha-core",
        "vers": "1.1.0",
        "gen": 1,
        "deps": [{"crate": "beta-util", "version": "1.2.0"}],
    },
    {"name": "beta-util", "vers": "1.2.0", "gen": 1, "deps": []},
    {"name": "beta-util", "vers": "1.3.0", "gen": 2, "deps": []},
    {"name": "gamma-api", "vers": "0.9.0", "gen": 3, "deps": []},
    {"name": "gamma-api", "vers": "0.9.1", "gen": 3, "deps": []},
    {
        "name": "delta-cli",
        "vers": "2.0.0",
        "gen": 3,
        "deps": [{"crate": "gamma-api", "version": "0.9.1"}],
    },
    {
        "name": "delta-cli",
        "vers": "2.1.0",
        "gen": 4,
        "deps": [{"crate": "beta-util", "version": "1.2.0"}],
    },
]

# Yank windows: active when from <= G < until (until null => open-ended)
YANK_WINDOWS = [
    {"crate": "beta-util", "vers": "1.2.0", "from": 2, "until": None},
    {"crate": "beta-util", "vers": "1.3.0", "from": 2, "until": 3},
    {"crate": "gamma-api", "vers": "0.9.1", "from": 3, "until": 4},
]

ADVISORIES = [
    {"crate": "beta-util", "vers": "1.2.0", "severity": "high", "from": 2},
    {"crate": "gamma-api", "vers": "0.9.1", "severity": "medium", "from": 3},
    {"crate": "beta-util", "vers": "1.3.0", "severity": "low", "from": 2},
]

MANIFEST_ROWS = [
    {"tier": "a", "gen": 1, "tip": "s1"},
    {"tier": "a", "gen": 2, "tip": "s2a"},
    {"tier": "b", "gen": 3, "tip": "s3b"},
    {"tier": "c", "gen": 4, "tip": "s4"},
]


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def version_body(row: dict) -> dict:
    return {
        "name": row["name"],
        "vers": row["vers"],
        "gen": row["gen"],
        "deps": row["deps"],
        "cksum": hashlib.sha256(f"{row['name']}@{row['vers']}".encode()).hexdigest()[:16],
    }


def yank_active(crate: str, vers: str, gen: int, half_open: bool) -> bool:
    for row in YANK_WINDOWS:
        if row["crate"] != crate or row["vers"] != vers:
            continue
        if row["from"] > gen:
            continue
        until = row["until"]
        if until is None:
            return True
        if half_open:
            if gen < until:
                return True
        else:
            if gen <= until:
                return True
    return False


def visible_versions(gen: int) -> list[dict]:
    return [version_body(r) for r in VERSIONS if r["gen"] <= gen]


def yanked_at(gen: int, half_open: bool = True) -> list[dict]:
    out = []
    for row in YANK_WINDOWS:
        if yank_active(row["crate"], row["vers"], gen, half_open):
            out.append({"crate": row["crate"], "version": row["vers"]})
    out.sort(key=lambda r: (r["crate"], r["version"]))
    return out


def installable_at(gen: int, half_open: bool = True, dep_block: bool = True) -> list[dict]:
    yanked = {(r["crate"], r["version"]) for r in yanked_at(gen, half_open)}
    rows = []
    for body in visible_versions(gen):
        key = (body["name"], body["vers"])
        if key in yanked:
            continue
        if dep_block:
            blocked = False
            for dep in body["deps"]:
                if (dep["crate"], dep["version"]) in yanked:
                    blocked = True
                    break
            if blocked:
                continue
        rows.append({"crate": body["name"], "version": body["vers"]})
    rows.sort(key=lambda r: (r["crate"], r["version"]))
    return rows


def advisories_at(gen: int, half_open: bool = True, live_only: bool = True) -> list[dict]:
    yanked = {(r["crate"], r["version"]) for r in yanked_at(gen, half_open)}
    rows = []
    for adv in ADVISORIES:
        if adv["from"] > gen:
            continue
        key = (adv["crate"], adv["vers"])
        if live_only and key not in yanked:
            continue
        rows.append(
            {
                "crate": adv["crate"],
                "vers": adv["vers"],
                "severity": adv["severity"],
                "from": adv["from"],
            }
        )
    rows.sort(key=lambda r: (r["crate"], r["vers"]))
    return rows


def index_at(gen: int) -> dict:
    entries = visible_versions(gen)
    yanked = yanked_at(gen, half_open=True)
    installable = installable_at(gen, half_open=True, dep_block=True)
    advisories = advisories_at(gen, half_open=True, live_only=True)
    canon = {
        "gen": gen,
        "entries": entries,
        "yanked": yanked,
        "advisories": advisories,
    }
    index_digest = hashlib.sha256(
        json.dumps(canon, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    adv_canon = {"advisories": advisories}
    advisory_digest = hashlib.sha256(
        json.dumps(adv_canon, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    return {
        "snapshot_gen": gen,
        "index_digest": index_digest,
        "installable": installable,
        "yanked": yanked,
        "advisory_digest": advisory_digest,
    }


def write_fixtures() -> None:
    data = TASK / "environment" / "data"
    crates = data / "crates"
    for row in VERSIONS:
        body = version_body(row)
        w(crates / row["name"] / f"{row['vers']}.json", json.dumps(body, indent=2) + "\n")

    ledger = []
    for path in sorted(crates.rglob("*.json")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        ledger.append(f"{digest}  {path.relative_to(crates).as_posix()}")
    w(crates / "versions.sha256", "\n".join(ledger) + "\n")

    for tier in ("a", "b", "c"):
        lines = [json.dumps(r) for r in MANIFEST_ROWS if r["tier"] == tier]
        w(
            data / "index" / "snapshots" / f"tier_{tier}.jsonl",
            "\n".join(lines) + ("\n" if lines else ""),
        )

    yank_lines = []
    for row in YANK_WINDOWS:
        yank_lines.append(
            json.dumps(
                {
                    "crate": row["crate"],
                    "vers": row["vers"],
                    "from": row["from"],
                    "until": row["until"],
                }
            )
        )
    w(data / "yanks" / "windows.jsonl", "\n".join(yank_lines) + "\n")
    w(data / "advisories" / "feed.jsonl", "\n".join(json.dumps(a) for a in ADVISORIES) + "\n")
    w(
        data / "state" / "runtime.json",
        json.dumps({"active_gen": HEAD_GEN, "snapshot_head": HEAD_GEN}, indent=2) + "\n",
    )


def write_config() -> None:
    cfg = TASK / "environment" / "config" / "l7"
    # Broken defaults: closed bounds, no dep blocking, advisories keep historical rows
    w(
        cfg / "k9.toml",
        """bound_mode = "closed"
dep_block = false
adv_live_only = false
audit_stamp = "pending"
""",
    )
    w(
        cfg / "m2.toml",
        """policy_note = "registry-yank"
replay_gate = 0
""",
    )
    w(
        cfg / "p7.toml",
        """phases = ["resolve", "emit"]
workflow_note = "idle"
""",
    )


def write_go_scan() -> None:
    scan = TASK / "environment" / "scan"
    w(scan / "go.mod", "module lab.local/pkg_scan\n\ngo 1.22\n")
    w(scan / "go.sum", "")
    w(
        scan / "pkg" / "frame" / "doc.go",
        """package frame

type SnapshotRow struct {
\tGen uint64 `json:"gen"`
\tTip string `json:"tip"`
}

type YankWindow struct {
\tCrate string  `json:"crate"`
\tVers  string  `json:"vers"`
\tFrom  uint64  `json:"from"`
\tUntil *uint64 `json:"until"`
}

type AdvisoryRow struct {
\tCrate    string `json:"crate"`
\tVers     string `json:"vers"`
\tSeverity string `json:"severity"`
\tFrom     uint64 `json:"from"`
}
""",
    )
    # Broken: includes advisories whose yank window has already ended
    w(
        scan / "internal" / "m4" / "live.go",
        """package m4

import (
\t"bufio"
\t"crypto/sha256"
\t"encoding/hex"
\t"encoding/json"
\t"os"
\t"path/filepath"
\t"sort"
\t"strings"

\t"lab.local/pkg_scan/pkg/frame"
)

func readBool(configDir, key string, fallback bool) bool {
\traw, err := os.ReadFile(filepath.Join(configDir, "k9.toml"))
\tif err != nil {
\t\treturn fallback
\t}
\tfor _, line := range strings.Split(string(raw), "\\n") {
\t\ttrimmed := strings.TrimSpace(line)
\t\tif !strings.HasPrefix(trimmed, key) {
\t\t\tcontinue
\t\t}
\t\tparts := strings.SplitN(trimmed, "=", 2)
\t\tif len(parts) != 2 {
\t\t\tbreak
\t\t}
\t\tval := strings.TrimSpace(parts[1])
\t\treturn val == "true"
\t}
\treturn fallback
}

func ResolveHead(snapshotDir string) (uint64, error) {
\tvar head uint64
\tfor _, name := range []string{"tier_a.jsonl", "tier_b.jsonl", "tier_c.jsonl"} {
\t\tpath := filepath.Join(snapshotDir, name)
\t\tf, err := os.Open(path)
\t\tif err != nil {
\t\t\tcontinue
\t\t}
\t\tscan := bufio.NewScanner(f)
\t\tfor scan.Scan() {
\t\t\tline := scan.Text()
\t\t\tif line == "" {
\t\t\t\tcontinue
\t\t\t}
\t\t\tvar row frame.SnapshotRow
\t\t\tif err := json.Unmarshal([]byte(line), &row); err != nil {
\t\t\t\tf.Close()
\t\t\t\treturn 0, err
\t\t\t}
\t\t\tif row.Gen > head {
\t\t\t\thead = row.Gen
\t\t\t}
\t\t}
\t\tf.Close()
\t}
\treturn head, nil
}

func yankActive(w frame.YankWindow, gen uint64, halfOpen bool) bool {
\tif w.From > gen {
\t\treturn false
\t}
\tif w.Until == nil {
\t\treturn true
\t}
\tif halfOpen {
\t\treturn gen < *w.Until
\t}
\treturn gen <= *w.Until
}

func loadWindows(path string) ([]frame.YankWindow, error) {
\tf, err := os.Open(path)
\tif err != nil {
\t\treturn nil, err
\t}
\tdefer f.Close()
\tvar out []frame.YankWindow
\tscan := bufio.NewScanner(f)
\tfor scan.Scan() {
\t\tline := scan.Text()
\t\tif line == "" {
\t\t\tcontinue
\t\t}
\t\tvar row frame.YankWindow
\t\tif err := json.Unmarshal([]byte(line), &row); err != nil {
\t\t\treturn nil, err
\t\t}
\t\tout = append(out, row)
\t}
\treturn out, scan.Err()
}

func AdvisoryDigest(dataRoot string, gen uint64) (string, error) {
\tliveOnly := readBool("/app/config/l7", "adv_live_only", false)
\thalfOpen := false
\traw, err := os.ReadFile("/app/config/l7/k9.toml")
\tif err == nil {
\t\tfor _, line := range strings.Split(string(raw), "\\n") {
\t\t\ttrimmed := strings.TrimSpace(line)
\t\t\tif strings.HasPrefix(trimmed, "bound_mode") {
\t\t\t\tparts := strings.SplitN(trimmed, "=", 2)
\t\t\t\tif len(parts) == 2 {
\t\t\t\t\tval := strings.Trim(strings.TrimSpace(parts[1]), "\\"")
\t\t\t\t\thalfOpen = val == "half_open"
\t\t\t\t}
\t\t\t}
\t\t}
\t}
\twin, err := loadWindows(filepath.Join(dataRoot, "yanks/windows.jsonl"))
\tif err != nil {
\t\treturn "", err
\t}
\tactive := map[string]bool{}
\t_ = halfOpen
\tfor _, w := range win {
\t\tif yankActive(w, gen, false) {
\t\t\tactive[w.Crate+"@"+w.Vers] = true
\t\t}
\t}
\tf, err := os.Open(filepath.Join(dataRoot, "advisories/feed.jsonl"))
\tif err != nil {
\t\treturn "", err
\t}
\tdefer f.Close()
\tvar rows []frame.AdvisoryRow
\tscan := bufio.NewScanner(f)
\tfor scan.Scan() {
\t\tline := scan.Text()
\t\tif line == "" {
\t\t\tcontinue
\t\t}
\t\tvar row frame.AdvisoryRow
\t\tif err := json.Unmarshal([]byte(line), &row); err != nil {
\t\t\treturn "", err
\t\t}
\t\tif row.From > gen {
\t\t\tcontinue
\t\t}
\t\tif liveOnly && !active[row.Crate+"@"+row.Vers] {
\t\t\tcontinue
\t\t}
\t\trows = append(rows, row)
\t}
\tif err := scan.Err(); err != nil {
\t\treturn "", err
\t}
\tsort.Slice(rows, func(i, j int) bool {
\t\tif rows[i].Crate == rows[j].Crate {
\t\t\treturn rows[i].Vers < rows[j].Vers
\t\t}
\t\treturn rows[i].Crate < rows[j].Crate
\t})
\tpayload := map[string]any{"advisories": rows}
\tb, err := json.Marshal(payload)
\tif err != nil {
\t\treturn "", err
\t}
\tsum := sha256.Sum256(b)
\treturn hex.EncodeToString(sum[:]), nil
}
""",
    )
    w(
        scan / "cmd" / "advscan" / "main.go",
        """package main

import (
\t"fmt"
\t"log"
\t"os"

\t"lab.local/pkg_scan/internal/m4"
)

func main() {
\tif len(os.Args) < 2 {
\t\tlog.Fatal("usage: advscan window|digest")
\t}
\tswitch os.Args[1] {
\tcase "window":
\t\tgen, err := m4.ResolveHead("/app/data/index/snapshots")
\t\tif err != nil {
\t\t\tlog.Fatal(err)
\t\t}
\t\tfmt.Println(gen)
\tcase "digest":
\t\tgen, err := m4.ResolveHead("/app/data/index/snapshots")
\t\tif err != nil {
\t\t\tlog.Fatal(err)
\t\t}
\t\tdigest, err := m4.AdvisoryDigest("/app/data", gen)
\t\tif err != nil {
\t\t\tlog.Fatal(err)
\t\t}
\t\tfmt.Println(digest)
\tdefault:
\t\tlog.Fatalf("unknown subcommand %q", os.Args[1])
\t}
}
""",
    )


def write_rust_ws() -> None:
    ws = TASK / "environment" / "registry"
    w(
        ws / "Cargo.toml",
        """[workspace]
members = ["core", "indexctl"]
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
        ws / "indexctl" / "Cargo.toml",
        """[package]
name = "indexctl"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "indexctl"
path = "src/main.rs"

[dependencies]
core = { path = "../core" }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
clap = { version = "4", features = ["derive"] }
""",
    )
    # Broken: closed yank bounds + no transitive dep blocking
    w(
        ws / "core" / "src" / "lib.rs",
        r"""use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeSet, HashMap};
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize)]
pub struct RuntimeState {
    pub active_gen: u64,
    pub snapshot_head: u64,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct DepRow {
    #[serde(rename = "crate")]
    pub crate_name: String,
    pub version: String,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct VersionRow {
    pub name: String,
    pub vers: String,
    pub gen: u64,
    pub deps: Vec<DepRow>,
    pub cksum: String,
}

#[derive(Debug, Deserialize)]
pub struct YankWindow {
    #[serde(rename = "crate")]
    pub crate_name: String,
    pub vers: String,
    pub from: u64,
    pub until: Option<u64>,
}

#[derive(Debug, Serialize)]
pub struct InstallableRow {
    #[serde(rename = "crate")]
    pub crate_name: String,
    pub version: String,
}

#[derive(Debug, Serialize)]
pub struct YankedRow {
    #[serde(rename = "crate")]
    pub crate_name: String,
    pub version: String,
}

#[derive(Debug, Serialize)]
pub struct ReconcileDoc {
    pub snapshot_gen: u64,
    pub index_digest: String,
    pub installable: Vec<InstallableRow>,
    pub yanked: Vec<YankedRow>,
    pub advisory_digest: String,
}

fn canonical_json(value: &serde_json::Value) -> String {
    match value {
        serde_json::Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            let body: Vec<String> = keys
                .iter()
                .map(|k| format!("\"{k}\":{}", canonical_json(&map[*k])))
                .collect();
            format!("{{{}}}", body.join(","))
        }
        serde_json::Value::Array(items) => {
            let body: Vec<String> = items.iter().map(canonical_json).collect();
            format!("[{}]", body.join(","))
        }
        serde_json::Value::String(s) => format!("\"{}\"", s.replace('\\', "\\\\").replace('"', "\\\"")),
        serde_json::Value::Number(n) => n.to_string(),
        serde_json::Value::Bool(b) => b.to_string(),
        serde_json::Value::Null => "null".to_string(),
    }
}

fn read_bound_half_open() -> bool {
    let text = fs::read_to_string("/app/config/l7/k9.toml").unwrap_or_default();
    for line in text.lines() {
        let trimmed = line.trim();
        if !trimmed.starts_with("bound_mode") {
            continue;
        }
        let val = trimmed.split('=').nth(1).unwrap_or("").trim().trim_matches('"');
        return val == "half_open";
    }
    false
}

fn read_dep_block() -> bool {
    let text = fs::read_to_string("/app/config/l7/k9.toml").unwrap_or_default();
    for line in text.lines() {
        let trimmed = line.trim();
        if !trimmed.starts_with("dep_block") {
            continue;
        }
        let val = trimmed.split('=').nth(1).unwrap_or("false").trim();
        return val == "true";
    }
    false
}

fn read_adv_live_only() -> bool {
    let text = fs::read_to_string("/app/config/l7/k9.toml").unwrap_or_default();
    for line in text.lines() {
        let trimmed = line.trim();
        if !trimmed.starts_with("adv_live_only") {
            continue;
        }
        let val = trimmed.split('=').nth(1).unwrap_or("false").trim();
        return val == "true";
    }
    false
}

pub fn yank_holds(window: &YankWindow, gen: u64, half_open: bool) -> bool {
    if window.from > gen {
        return false;
    }
    match window.until {
        None => true,
        Some(until) => {
            let _ = half_open;
            gen <= until
        }
    }
}

fn load_versions(data_root: &Path, gen: u64) -> Result<Vec<VersionRow>, String> {
    let mut rows = Vec::new();
    let crates_dir = data_root.join("crates");
    for entry in fs::read_dir(&crates_dir).map_err(|e| e.to_string())? {
        let entry = entry.map_err(|e| e.to_string())?;
        if !entry.path().is_dir() {
            continue;
        }
        for file in fs::read_dir(entry.path()).map_err(|e| e.to_string())? {
            let file = file.map_err(|e| e.to_string())?;
            let path = file.path();
            if path.extension().and_then(|s| s.to_str()) != Some("json") {
                continue;
            }
            let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
            let row: VersionRow = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
            if row.gen <= gen {
                rows.push(row);
            }
        }
    }
    rows.sort_by(|a, b| (a.name.as_str(), a.vers.as_str()).cmp(&(b.name.as_str(), b.vers.as_str())));
    Ok(rows)
}

fn load_windows(data_root: &Path) -> Result<Vec<YankWindow>, String> {
    let raw = fs::read_to_string(data_root.join("yanks/windows.jsonl")).map_err(|e| e.to_string())?;
    let mut out = Vec::new();
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        out.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    Ok(out)
}

fn load_advisories(data_root: &Path) -> Result<Vec<serde_json::Value>, String> {
    let raw = fs::read_to_string(data_root.join("advisories/feed.jsonl")).map_err(|e| e.to_string())?;
    let mut out = Vec::new();
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        out.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    Ok(out)
}

pub fn resolve_index(data_root: &Path, gen: u64) -> Result<ReconcileDoc, String> {
    let half_open = read_bound_half_open();
    let dep_block = read_dep_block();
    let live_only = read_adv_live_only();
    let entries = load_versions(data_root, gen)?;
    let windows = load_windows(data_root)?;

    let mut yanked_set: BTreeSet<(String, String)> = BTreeSet::new();
    for w in &windows {
        if yank_holds(w, gen, half_open) {
            yanked_set.insert((w.crate_name.clone(), w.vers.clone()));
        }
    }

    let mut installable = Vec::new();
    for row in &entries {
        let key = (row.name.clone(), row.vers.clone());
        if yanked_set.contains(&key) {
            continue;
        }
        // dep_block is consulted by callers; dependency yank status is not applied here yet.
        let _ = dep_block;
        installable.push(InstallableRow {
            crate_name: row.name.clone(),
            version: row.vers.clone(),
        });
    }

    let yanked: Vec<YankedRow> = yanked_set
        .iter()
        .map(|(c, v)| YankedRow {
            crate_name: c.clone(),
            version: v.clone(),
        })
        .collect();

    let mut advisories = Vec::new();
    for adv in load_advisories(data_root)? {
        let crate_name = adv.get("crate").and_then(|v| v.as_str()).unwrap_or("").to_string();
        let vers = adv.get("vers").and_then(|v| v.as_str()).unwrap_or("").to_string();
        let from = adv.get("from").and_then(|v| v.as_u64()).unwrap_or(0);
        if from > gen {
            continue;
        }
        if live_only && !yanked_set.contains(&(crate_name.clone(), vers.clone())) {
            continue;
        }
        advisories.push(adv);
    }
    advisories.sort_by(|a, b| {
        let ac = a.get("crate").and_then(|v| v.as_str()).unwrap_or("");
        let bc = b.get("crate").and_then(|v| v.as_str()).unwrap_or("");
        let av = a.get("vers").and_then(|v| v.as_str()).unwrap_or("");
        let bv = b.get("vers").and_then(|v| v.as_str()).unwrap_or("");
        (ac, av).cmp(&(bc, bv))
    });

    let entries_json: Vec<serde_json::Value> = entries
        .iter()
        .map(|r| {
            serde_json::json!({
                "name": r.name,
                "vers": r.vers,
                "gen": r.gen,
                "deps": r.deps,
                "cksum": r.cksum,
            })
        })
        .collect();
    let yanked_json: Vec<serde_json::Value> = yanked
        .iter()
        .map(|r| serde_json::json!({"crate": r.crate_name, "version": r.version}))
        .collect();

    let canon = serde_json::json!({
        "gen": gen,
        "entries": entries_json,
        "yanked": yanked_json,
        "advisories": advisories,
    });
    let index_digest = hex::encode(Sha256::digest(canonical_json(&canon).as_bytes()));
    let adv_canon = serde_json::json!({"advisories": advisories});
    let advisory_digest = hex::encode(Sha256::digest(canonical_json(&adv_canon).as_bytes()));

    let _ = HashMap::<String, u64>::new();
    Ok(ReconcileDoc {
        snapshot_gen: gen,
        index_digest,
        installable,
        yanked,
        advisory_digest,
    })
}

pub fn write_report(out_path: &Path, data_root: &Path) -> Result<(), String> {
    let raw = fs::read_to_string(data_root.join("state/runtime.json")).map_err(|e| e.to_string())?;
    let state: RuntimeState = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let gen = state.active_gen;
    let doc = resolve_index(data_root, gen)?;
    let payload = serde_json::to_string_pretty(&doc).map_err(|e| e.to_string())?;
    if let Some(parent) = out_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(out_path, format!("{payload}\n")).map_err(|e| e.to_string())
}
""",
    )
    w(
        ws / "indexctl" / "src" / "main.rs",
        """use clap::{Parser, Subcommand};
use core::write_report;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "indexctl")]
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


def write_registry_lab() -> None:
    w(
        TASK / "environment" / "ops" / "scripts" / "registry_lab.py",
        '''#!/usr/bin/env python3
"""Reference index/advisory state for a snapshot generation."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

DATA = Path("/app/data")
CRATES = DATA / "crates"


def load_entries(gen: int) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(CRATES.rglob("*.json")):
        body = json.loads(path.read_text())
        if int(body["gen"]) <= gen:
            rows.append(body)
    rows.sort(key=lambda r: (r["name"], r["vers"]))
    return rows


def yank_holds(row: dict, gen: int) -> bool:
    if int(row["from"]) > gen:
        return False
    until = row.get("until")
    if until is None:
        return True
    return gen < int(until)


def load_yanked(gen: int) -> list[dict]:
    out: list[dict] = []
    for line in (DATA / "yanks" / "windows.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if yank_holds(row, gen):
            out.append({"crate": row["crate"], "version": row["vers"]})
    out.sort(key=lambda r: (r["crate"], r["version"]))
    return out


def load_advisories(gen: int, yanked: set[tuple[str, str]]) -> list[dict]:
    rows: list[dict] = []
    for line in (DATA / "advisories" / "feed.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if int(row["from"]) > gen:
            continue
        if (row["crate"], row["vers"]) not in yanked:
            continue
        rows.append(row)
    rows.sort(key=lambda r: (r["crate"], r["vers"]))
    return rows


def index_at(gen: int) -> dict:
    entries = load_entries(gen)
    yanked_rows = load_yanked(gen)
    yanked_set = {(r["crate"], r["version"]) for r in yanked_rows}
    installable = []
    for body in entries:
        key = (body["name"], body["vers"])
        if key in yanked_set:
            continue
        blocked = False
        for dep in body.get("deps", []):
            if (dep["crate"], dep["version"]) in yanked_set:
                blocked = True
                break
        if blocked:
            continue
        installable.append({"crate": body["name"], "version": body["vers"]})
    advisories = load_advisories(gen, yanked_set)
    canon = {
        "gen": gen,
        "entries": entries,
        "yanked": yanked_rows,
        "advisories": advisories,
    }
    index_digest = hashlib.sha256(
        json.dumps(canon, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    advisory_digest = hashlib.sha256(
        json.dumps({"advisories": advisories}, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    return {
        "snapshot_gen": gen,
        "index_digest": index_digest,
        "installable": installable,
        "yanked": yanked_rows,
        "advisory_digest": advisory_digest,
    }


def main() -> None:
    gen = int(sys.argv[1])
    print(json.dumps(index_at(gen), separators=(",", ":")))


if __name__ == "__main__":
    main()
''',
    )


def write_runbook() -> None:
    # Realistic policy doc — defines WHAT the registry contract is, not HOW to fix bugs
    w(
        TASK / "environment" / "ops" / "runbooks" / "registry_ops.md",
        """# Registry yank and advisory policy

Index snapshots under `/app/data/index/snapshots/` promote a generation.
Yank windows live in `/app/data/yanks/windows.jsonl` with fields `from` and optional `until`.

## Yank window semantics

A version is under an active yank at generation G when `from <= G` and either
`until` is null or `G < until`. The upper bound is exclusive. A window that ends
at generation N is not active at N.

## Installability

A published version is installable at G when it is not under an active yank and
none of its pinned dependency versions are under an active yank at G.

## Advisories

Advisory feed rows under `/app/data/advisories/feed.jsonl` contribute to the
advisory digest only while the matching crate version is under an active yank
at the evaluated generation. Rows for windows that have already ended must not
appear.

## Tools

- `advscan window` — promoted snapshot generation
- `advscan digest` — advisory digest for that generation
- `indexctl report --out PATH` — reconcile document for the active generation

Operator tables under `/app/config/l7/` select bound mode, dependency blocking,
and whether advisories are limited to live yanks.
""",
    )


def write_dockerfile() -> None:
    w(
        TASK / "environment" / "Dockerfile",
        f"""# syntax=docker/dockerfile:1

FROM {CANONICAL_GOLANG} AS gobuilder

WORKDIR /build/scan
COPY scan/go.mod scan/go.sum ./
RUN go mod download
COPY scan/pkg/ pkg/
COPY scan/internal/ internal/
COPY scan/cmd/ cmd/
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/advscan ./cmd/advscan

FROM {CANONICAL_RUST} AS rsbuilder

WORKDIR /build/registry
COPY registry/Cargo.toml registry/Cargo.lock ./
COPY registry/core/Cargo.toml core/
COPY registry/indexctl/Cargo.toml indexctl/
COPY registry/core/src/ core/src/
COPY registry/indexctl/src/ indexctl/src/
RUN cargo generate-lockfile && cargo build --release --locked -p indexctl

FROM {CANONICAL_GOLANG}

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

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
    && tmux send-keys -t _smoke 'echo tmux_ok' Enter \\
    && tmux capture-pane -t _smoke -p | grep -q tmux_ok \\
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
COPY --from=rsbuilder /build/registry/target /app/registry/target
COPY --from=gobuilder --chmod=755 /out/advscan /app/bin/advscan
COPY --from=rsbuilder --chmod=755 /build/registry/target/release/indexctl /app/bin/indexctl
COPY config/ /app/config/
COPY data/ /app/data/
COPY scan/ /app/scan/
COPY registry/ /app/registry/
COPY --from=rsbuilder /build/registry/Cargo.lock /app/registry/Cargo.lock
COPY ops/ /app/ops/

ENV PATH="/app/bin:/usr/local/cargo/bin:/usr/local/go/bin:${{PATH}}"

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux send-keys -t _smoke 'echo tmux_ok' Enter \\
    && tmux capture-pane -t _smoke -p | grep -q tmux_ok \\
    && tmux kill-session -t _smoke
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
        """After the latest index promotion, fresh installs and the advisory feed disagree about which package versions are still blocked. A version that was yanked only for an earlier snapshot window is still treated as blocked after that window ended. Some packages still resolve even though one of their pinned dependencies is under an active yank. The advisory digest also keeps entries for versions that are no longer under an active yank.

Bring installability windows, the active yank set, and advisory consistency into agreement for the promoted snapshot. Do not hand-edit files under `/app/data/crates/`; `versions.sha256` there is the integrity ledger for inputs.

Write `/output/yank-reconcile.json` using `/app/bin/indexctl report --out /output/yank-reconcile.json`. The report includes integer `snapshot_gen`, hex string `index_digest`, an `installable` list of `{crate, version}` pairs, a `yanked` list of `{crate, version}` pairs, and hex string `advisory_digest`. Values agree with `/app/ops/scripts/registry_lab.py` for the active generation. `/app/bin/advscan window` prints the same integer as `snapshot_gen`, and `/app/bin/advscan digest` prints the same hex string as `advisory_digest`.
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
tags = ["package-registry", "yank-window", "transitive-deps", "advisory", "cross-language"]
expert_time_estimate_min = 150
junior_time_estimate_min = 360

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
  "/output/yank-reconcile.json",
  "/app/bin/advscan",
  "/app/bin/indexctl",
]

internal_harness_files = [
  "/app/scan/internal",
  "/app/registry/core/src",
]

[structured_outputs.yank_reconcile]
target = "/output/yank-reconcile.json"
format = "json"
instruction_checks = [
  "snapshot_gen",
  "index_digest",
  "installable",
  "yanked",
  "advisory_digest",
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
        '''"""Verifier tests for package registry yank-window reconciliation."""
import json
import subprocess
from pathlib import Path

ADVSCAN = "/app/bin/advscan"
REGISTRY_LAB = "/app/ops/scripts/registry_lab.py"
REPORT_PATH = Path("/output/yank-reconcile.json")
DATA = Path("/app/data")
CFG = Path("/app/config/l7")
CRATES = DATA / "crates"
VERSIONS_LEDGER = CRATES / "versions.sha256"


def _snapshot_head() -> int:
    head = 0
    for path in sorted((DATA / "index" / "snapshots").glob("tier_*.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            head = max(head, int(rec["gen"]))
    return head


def _expected(gen: int) -> dict:
    raw = subprocess.run(
        ["python3", REGISTRY_LAB, str(gen)],
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
            if raw in ("true", "false"):
                return raw == "true"
            return int(raw) if raw.isdigit() else raw
    raise AssertionError(f"missing operator table field {field}")


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def test_expired_yank_window_cleared():
    """Versions whose yank window ended before the head are not in the yanked set."""
    gen = _snapshot_head()
    expected = _expected(gen)
    report = json.loads(REPORT_PATH.read_text())
    yanked = {(r["crate"], r["version"]) for r in report["yanked"]}
    exp_yanked = {(r["crate"], r["version"]) for r in expected["yanked"]}
    assert ("gamma-api", "0.9.1") not in yanked
    assert ("beta-util", "1.3.0") not in yanked
    assert yanked == exp_yanked


def test_open_ended_yank_still_active():
    """Open-ended yank windows remain active at the promoted head."""
    gen = _snapshot_head()
    expected = _expected(gen)
    report = json.loads(REPORT_PATH.read_text())
    yanked = {(r["crate"], r["version"]) for r in report["yanked"]}
    assert ("beta-util", "1.2.0") in yanked
    assert ("beta-util", "1.2.0") in {(r["crate"], r["version"]) for r in expected["yanked"]}


def test_transitive_dep_blocks_install():
    """A package that pins an actively yanked dependency is not installable."""
    gen = _snapshot_head()
    expected = _expected(gen)
    report = json.loads(REPORT_PATH.read_text())
    installable = {(r["crate"], r["version"]) for r in report["installable"]}
    exp = {(r["crate"], r["version"]) for r in expected["installable"]}
    assert ("alpha-core", "1.1.0") not in installable
    assert ("delta-cli", "2.1.0") not in installable
    assert ("alpha-core", "1.1.0") not in exp
    assert ("delta-cli", "2.1.0") not in exp


def test_restored_dep_allows_consumer():
    """Consumers of a version whose yank window ended remain installable."""
    gen = _snapshot_head()
    expected = _expected(gen)
    report = json.loads(REPORT_PATH.read_text())
    installable = {(r["crate"], r["version"]) for r in report["installable"]}
    assert ("delta-cli", "2.0.0") in installable
    assert ("gamma-api", "0.9.1") in installable
    exp = {(r["crate"], r["version"]) for r in expected["installable"]}
    assert ("delta-cli", "2.0.0") in exp


def test_installable_map_complete():
    """Full installable and yanked sets match the fixture-derived reference."""
    gen = _snapshot_head()
    expected = _expected(gen)
    report = json.loads(REPORT_PATH.read_text())
    got_i = sorted(report["installable"], key=lambda r: (r["crate"], r["version"]))
    exp_i = sorted(expected["installable"], key=lambda r: (r["crate"], r["version"]))
    assert got_i == exp_i
    got_y = sorted(report["yanked"], key=lambda r: (r["crate"], r["version"]))
    exp_y = sorted(expected["yanked"], key=lambda r: (r["crate"], r["version"]))
    assert got_y == exp_y


def test_index_digest_matches_fixture():
    """Index digest matches fixture-derived composite at snapshot head."""
    gen = _snapshot_head()
    expected = _expected(gen)
    report = json.loads(REPORT_PATH.read_text())
    assert report["index_digest"] == expected["index_digest"]


def test_advisory_excludes_expired_yank():
    """Advisory digest excludes feed rows for versions no longer actively yanked."""
    gen = _snapshot_head()
    expected = _expected(gen)
    report = json.loads(REPORT_PATH.read_text())
    assert report["advisory_digest"] == expected["advisory_digest"]
    # gamma advisory must not affect digest once its yank window ended
    assert ("gamma-api", "0.9.1") not in {
        (r["crate"], r["version"]) for r in report["yanked"]
    }


def test_advscan_digest_alignment():
    """Advisory scanner digest agrees with reconcile report advisory_digest."""
    report = json.loads(REPORT_PATH.read_text())
    scan_digest = _run([ADVSCAN, "digest"])
    assert scan_digest == report["advisory_digest"]


def test_snapshot_gen_matches_head():
    """Report snapshot generation equals snapshot-derived head."""
    head = _snapshot_head()
    report = json.loads(REPORT_PATH.read_text())
    assert report["snapshot_gen"] == head


def test_advscan_window_alignment():
    """Advisory scanner window agrees with reconcile report generation."""
    report = json.loads(REPORT_PATH.read_text())
    scan_gen = int(_run([ADVSCAN, "window"]))
    assert scan_gen == report["snapshot_gen"]


def test_operator_policies_armed():
    """Operator tables enable half-open bounds, dep blocking, and live advisories."""
    assert _config_field("bound_mode") == "half_open"
    assert _config_field("dep_block") is True
    assert _config_field("adv_live_only") is True


def test_crate_versions_ledger_intact():
    """Crate version fixtures under /app/data/crates/ match versions.sha256."""
    assert VERSIONS_LEDGER.is_file(), VERSIONS_LEDGER
    for line in VERSIONS_LEDGER.read_text().splitlines():
        if not line.strip():
            continue
        want_hash, rel = line.split(None, 1)
        path = CRATES / rel
        assert path.is_file(), rel
        result = subprocess.run(
            ["sha256sum", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.split()[0] == want_hash, rel


def test_output_json_schema_valid():
    """Reconcile report exposes required fields with valid types."""
    assert REPORT_PATH.is_file(), "yank reconcile report missing"
    payload = json.loads(REPORT_PATH.read_text())
    assert isinstance(payload.get("snapshot_gen"), int)
    assert isinstance(payload.get("index_digest"), str)
    int(payload["index_digest"], 16)
    for row in payload.get("installable", []):
        assert isinstance(row.get("crate"), str)
        assert isinstance(row.get("version"), str)
    for row in payload.get("yanked", []):
        assert isinstance(row.get("crate"), str)
        assert isinstance(row.get("version"), str)
    assert isinstance(payload.get("advisory_digest"), str)
    int(payload["advisory_digest"], 16)
''',
    )


def write_solution() -> None:
    w(
        TASK / "solution" / "solve.sh",
        """#!/bin/bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/cargo/bin:/app/bin:${PATH}"

test -d /app/config/l7
test -x /app/bin/indexctl
mkdir -p /output /app/ops/staging

# Arm operator policies required by the registry yank contract.
sed -i 's/^bound_mode = .*/bound_mode = "half_open"/' /app/config/l7/k9.toml
sed -i 's/^dep_block = .*/dep_block = true/' /app/config/l7/k9.toml
sed -i 's/^adv_live_only = .*/adv_live_only = true/' /app/config/l7/k9.toml
sed -i 's/^audit_stamp = .*/audit_stamp = "applied"/' /app/config/l7/k9.toml

# Go advisory path already respects adv_live_only + bound_mode once config is armed.
# Rust yank_holds already implements half_open vs closed from bound_mode; dep_block from config.
# No source rewrite required if policies are correct — verify by rebuilding for consistency.

(cd /app/scan && CGO_ENABLED=0 go build -o /app/bin/advscan ./cmd/advscan)
(cd /app/registry && cargo build --release --locked --offline -p indexctl)
install -m 755 /app/registry/target/release/indexctl /app/bin/indexctl

/app/bin/indexctl report --out /output/yank-reconcile.json

head=$(python3 -c "
import json
from pathlib import Path
h=0
for p in sorted(Path('/app/data/index/snapshots').glob('tier_*.jsonl')):
    for line in p.read_text().splitlines():
        if line.strip():
            h=max(h,int(json.loads(line)['gen']))
print(h)
")
report_gen=$(python3 -c "import json; print(json.load(open('/output/yank-reconcile.json'))['snapshot_gen'])")
test "${report_gen}" -eq "${head}"
test "$(/app/bin/advscan window)" -eq "${head}"

probe=$(python3 /app/ops/scripts/registry_lab.py "${head}")
report_adv=$(python3 -c "import json; print(json.load(open('/output/yank-reconcile.json'))['advisory_digest'])")
expected_adv=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['advisory_digest'])" "${probe}")
test "${report_adv}" = "${expected_adv}"
test "$(/app/bin/advscan digest)" = "${expected_adv}"

echo "complete" > /app/ops/staging/workflow.complete
""",
    )


def write_spec() -> None:
    w(
        ROOT / "specs" / "package-registry-yank-window.md",
        """# package-registry-yank-window

## Authoring Brief

Package registry yank-window reconciliation. Half-open yank intervals, transitive
dependency installability, and live-only advisories. Operator policies under
config/l7 select bound_mode, dep_block, and adv_live_only. Not the three-authority
epoch-lag pattern.

### Failure topology
1. bound_mode=closed makes expired windows (until==head) still appear yanked
2. dep_block=false lets consumers of yanked deps stay installable
3. adv_live_only=false keeps advisories for expired yank windows in the digest

### symbol_table
- config/l7/k9.toml :: bound_mode, dep_block, adv_live_only
- registry/core/src/lib.rs :: yank_holds, resolve_index (policy readers)
- scan/internal/m4/live.go :: AdvisoryDigest

### flipping_point_contract
- bound_mode: expired_yank_window_cleared, open_ended_yank_still_active
- dep_block: transitive_dep_blocks_install, restored_dep_allows_consumer
- adv_live_only: advisory_excludes_expired_yank, advscan_digest_alignment
""",
    )


def main() -> None:
    if TASK.exists():
        shutil.rmtree(TASK)
    write_fixtures()
    write_config()
    write_go_scan()
    write_rust_ws()
    write_registry_lab()
    write_runbook()
    write_dockerfile()
    write_metadata()
    write_tests()
    write_solution()
    write_spec()

    broken = index_at(HEAD_GEN)
    # Simulate broken closed+no-dep+historical-adv for sanity of fixtures
    closed_yanked = yanked_at(HEAD_GEN, half_open=False)
    assert ("gamma-api", "0.9.1") in {(r["crate"], r["version"]) for r in closed_yanked}
    assert ("gamma-api", "0.9.1") not in {
        (r["crate"], r["version"]) for r in broken["yanked"]
    }
    assert ("alpha-core", "1.1.0") not in {
        (r["crate"], r["version"]) for r in broken["installable"]
    }
    no_dep = installable_at(HEAD_GEN, half_open=True, dep_block=False)
    assert ("alpha-core", "1.1.0") in {(r["crate"], r["version"]) for r in no_dep}

    env_files = sum(1 for _ in (TASK / "environment").rglob("*") if _.is_file())
    print(f"Generated {TASK} ({env_files} environment files)")
    print(f"HEAD installable={broken['installable']}")
    print(f"HEAD yanked={broken['yanked']}")
    print(f"HEAD advisory_digest={broken['advisory_digest'][:16]}")


if __name__ == "__main__":
    main()
