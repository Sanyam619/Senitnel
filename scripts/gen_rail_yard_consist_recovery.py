#!/usr/bin/env python3
"""One-shot generator for tasks/rail-yard-consist-recovery (authoring tool, not shipped)."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "rail-yard-consist-recovery"
REPORT_NAME = "consist-report.json"

CANONICAL_GOLANG = (
    "public.ecr.aws/docker/library/golang:1.24-bookworm"
    "@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac"
)
CANONICAL_RUST = (
    "public.ecr.aws/docker/library/rust:1.85-slim"
    "@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36"
)

MOVEMENTS = [
    {"seq": 1, "op": "place", "track": "T1", "car": "C101", "pos": 0},
    {"seq": 2, "op": "place", "track": "T1", "car": "C102", "pos": 1},
    {"seq": 3, "op": "place", "track": "T2", "car": "C103", "pos": 0},
    {"seq": 4, "op": "pull", "track": "T2", "car": "C103"},
    {"seq": 5, "op": "place", "track": "T1", "car": "C103", "pos": 2},
    {"seq": 6, "op": "place", "track": "T2", "car": "C104", "pos": 0},
    {"seq": 7, "op": "place", "track": "T3", "car": "C105", "pos": 0},
]

CARS = [
    {"id": "C101", "kind": "box", "since": 1},
    {"id": "C102", "kind": "box", "since": 1},
    {"id": "C103", "kind": "tank", "since": 3},
    {"id": "C104", "kind": "flat", "since": 6},
    {"id": "C105", "kind": "hopper", "since": 7},
]

JOURNAL_ROWS = [
    {"tier": "a", "seq": 1, "stamp": "s1"},
    {"tier": "a", "seq": 2, "stamp": "s2"},
    {"tier": "b", "seq": 3, "stamp": "s3"},
    {"tier": "b", "seq": 4, "stamp": "s4b"},
    {"tier": "c", "seq": 5, "stamp": "s5"},
    {"tier": "c", "seq": 6, "stamp": "s6"},
    {"tier": "c", "seq": 7, "stamp": "s7"},
]

HEAD_SEQ = 7
STALE_SEQ = 3


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def apply_movement(tracks: dict[str, list[str]], row: dict) -> None:
    op = row["op"]
    track = row["track"]
    car = row["car"]
    tracks.setdefault(track, [])
    if op == "place":
        pos = int(row["pos"])
        tracks[track] = [c for c in tracks[track] if c != car]
        pos = max(0, min(pos, len(tracks[track])))
        tracks[track].insert(pos, car)
    elif op == "pull":
        tracks[track] = [c for c in tracks[track] if c != car]
    else:
        raise ValueError(f"unknown op {op}")


def consist_at(seq: int) -> dict[str, list[str]]:
    tracks: dict[str, list[str]] = {}
    for row in MOVEMENTS:
        if row["seq"] > seq:
            break
        apply_movement(tracks, row)
    return {k: tracks[k][:] for k in sorted(tracks)}


def canonical_tracks(tracks: dict[str, list[str]]) -> str:
    ordered = {k: tracks[k] for k in sorted(tracks)}
    return json.dumps(ordered, separators=(",", ":"), sort_keys=True)


def audit_digest(seq: int) -> str:
    body = canonical_tracks(consist_at(seq))
    return hashlib.sha256(body.encode()).hexdigest()


def write_fixtures() -> None:
    data = TASK / "environment" / "data"
    for row in CARS:
        w(data / "cars" / f"{row['id']}.json", json.dumps(row, indent=2) + "\n")

    for tier in ("a", "b", "c"):
        lines = [json.dumps(r) for r in JOURNAL_ROWS if r["tier"] == tier]
        w(data / "movements" / f"tier_{tier}.jsonl", "\n".join(lines) + ("\n" if lines else ""))

    for row in MOVEMENTS:
        w(data / "events" / f"evt_{row['seq']:03d}.json", json.dumps(row, indent=2) + "\n")

    w(
        data / "state" / "runtime.json",
        json.dumps(
            {
                "active_seq": STALE_SEQ,
                "last_replay_seq": STALE_SEQ,
                "movement_head": HEAD_SEQ,
                "partial_cutoff": STALE_SEQ,
            },
            indent=2,
        )
        + "\n",
    )
    w(
        data / "sidecars" / "movements.idx",
        json.dumps({"tiers": ["a", "b", "c"], "promoted": HEAD_SEQ}, indent=2) + "\n",
    )


def write_config() -> None:
    cfg = TASK / "environment" / "config" / "l7"
    w(
        cfg / "k9.toml",
        f"""journal_pin = {STALE_SEQ}
seq_floor = {STALE_SEQ}
yard_ready = false
audit_stamp = "pending"
anchor_mode = "partial"
""",
    )
    w(
        cfg / "m2.toml",
        """tier_reducer = "min"
replay_gate = 1
barrier_live = false
window_scan = false
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
    w(
        cfg / "n3.toml",
        """track_cap = 8
probe_stride = 1
hold_back = true
""",
    )
    w(
        cfg / "r8.toml",
        """audit_mode = "partial"
emit_lane = "secondary"
retry_ms = 250
""",
    )


def write_go_lane() -> None:
    lane = TASK / "environment" / "lane"
    w(
        lane / "go.mod",
        """module lab.local/yard_lane

go 1.22
""",
    )
    w(lane / "go.sum", "")
    w(
        lane / "pkg" / "frame" / "row.go",
        """package frame

type JournalRow struct {
\tSeq   uint64 `json:"seq"`
\tStamp string `json:"stamp"`
}

type TrackBlock struct {
\tCars []string `json:"cars"`
}

type SummaryDoc struct {
\tReplaySeq   uint64              `json:"replay_seq"`
\tTracks      map[string][]string `json:"tracks"`
\tAuditDigest string              `json:"audit_digest"`
}
""",
    )
    w(
        lane / "internal" / "m7" / "seq.go",
        """package m7

import (
\t"bufio"
\t"encoding/json"
\t"os"
\t"path/filepath"
\t"strings"

\t"lab.local/yard_lane/pkg/frame"
)

func tierReducer(configDir string) string {
\traw, err := os.ReadFile(filepath.Join(configDir, "m2.toml"))
\tif err != nil {
\t\treturn "min"
\t}
\tfor _, line := range strings.Split(string(raw), "\\n") {
\t\ttrimmed := strings.TrimSpace(line)
\t\tif !strings.HasPrefix(trimmed, "tier_reducer") {
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
\treturn "min"
}

func scanTierHead(movementDir, tier string) (uint64, error) {
\tpath := filepath.Join(movementDir, "tier_"+tier+".jsonl")
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
\t\tif row.Seq > head {
\t\t\thead = row.Seq
\t\t}
\t}
\tif err := scan.Err(); err != nil {
\t\treturn 0, err
\t}
\treturn head, nil
}

// ResolveSeq returns the sequence the movement lane treats as current.
func ResolveSeq(movementDir string) (uint64, error) {
\tmode := tierReducer("/app/config/l7")
\tvar pick uint64
\tstarted := false
\tfor _, tier := range []string{"a", "b", "c"} {
\t\thead, err := scanTierHead(movementDir, tier)
\t\tif err != nil {
\t\t\tcontinue
\t\t}
\t\tif !started {
\t\t\tpick = head
\t\t\tstarted = true
\t\t\tcontinue
\t\t}
\t\tif mode == "min" && head < pick {
\t\t\tpick = head
\t\t}
\t\tif mode != "min" && head > pick {
\t\t\tpick = head
\t\t}
\t}
\tif !started {
\t\treturn 0, os.ErrNotExist
\t}
\treturn pick, nil
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

\t"lab.local/yard_lane/pkg/frame"
)

// ScanTierA walks tier_a for a standalone anchor helper not wired into emit.
func ScanTierA(movementDir string) (uint64, error) {
\tpath := filepath.Join(movementDir, "tier_a.jsonl")
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
\t\tif row.Seq > head {
\t\t\thead = row.Seq
\t\t}
\t}
\treturn head, scan.Err()
}
""",
    )
    w(
        lane / "internal" / "m7" / "probe.go",
        """package m7

import (
\t"encoding/json"
\t"os"
\t"path/filepath"

\t"lab.local/yard_lane/pkg/frame"
)

func WriteProbe(outPath, dataRoot string) error {
\tseq, err := ResolveSeq(filepath.Join(dataRoot, "movements"))
\tif err != nil {
\t\treturn err
\t}
\ttracks, digest, err := readWindowSnapshot(dataRoot, seq)
\tif err != nil {
\t\treturn err
\t}
\tdoc := frame.SummaryDoc{
\t\tReplaySeq:   seq,
\t\tTracks:      tracks,
\t\tAuditDigest: digest,
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

func readWindowSnapshot(dataRoot string, seq uint64) (map[string][]string, string, error) {
\treturn buildAt(dataRoot, seq)
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

\t"lab.local/yard_lane/internal/m7"
)

func main() {
\tif len(os.Args) < 2 {
\t\tlog.Fatal("usage: lane probe|emit")
\t}
\tswitch os.Args[1] {
\tcase "probe":
\t\tseq, err := m7.ResolveSeq("/app/data/movements")
\t\tif err != nil {
\t\t\tlog.Fatal(err)
\t\t}
\t\tfmt.Println(seq)
\tcase "emit":
\t\tfs := flag.NewFlagSet("emit", flag.ExitOnError)
\t\tout := fs.String("out", "", "output path")
\t\t_ = fs.Parse(os.Args[2:])
\t\tif *out == "" {
\t\t\tlog.Fatal("emit requires --out")
\t\t}
\t\tif err := m7.WriteProbe(*out, "/app/data"); err != nil {
\t\t\tlog.Fatal(err)
\t\t}
\tdefault:
\t\tlog.Fatalf("unknown subcommand %q", os.Args[1])
\t}
}
""",
    )


def patch_lane_apply() -> None:
    w(
        TASK / "environment" / "lane" / "internal" / "m7" / "gate.go",
        """package m7

import (
\t"os"
\t"path/filepath"
\t"strings"
)

func pullsEnabled(dataRoot string) bool {
\t_ = dataRoot
\traw, err := os.ReadFile(filepath.Join("/app/config/l7", "m2.toml"))
\tif err != nil {
\t\treturn true
\t}
\tfor _, line := range strings.Split(string(raw), "\\n") {
\t\ttrimmed := strings.TrimSpace(line)
\t\tif !strings.HasPrefix(trimmed, "replay_gate") {
\t\t\tcontinue
\t\t}
\t\tparts := strings.SplitN(trimmed, "=", 2)
\t\tif len(parts) != 2 {
\t\t\tbreak
\t\t}
\t\tval := strings.TrimSpace(parts[1])
\t\treturn val == "0"
\t}
\treturn true
}
""",
    )
    w(
        TASK / "environment" / "lane" / "internal" / "m7" / "apply.go",
        """package m7

import (
\t"encoding/json"
\t"os"
\t"path/filepath"
\t"sort"
)

type evtRow struct {
\tSeq   int    `json:"seq"`
\tOp    string `json:"op"`
\tTrack string `json:"track"`
\tCar   string `json:"car"`
\tPos   int    `json:"pos"`
}

func buildAt(dataRoot string, seq uint64) (map[string][]string, string, error) {
\ttracks := make(map[string][]string)
\tentries, err := os.ReadDir(filepath.Join(dataRoot, "events"))
\tif err != nil {
\t\treturn nil, "", err
\t}
\tvar rows []evtRow
\tfor _, ent := range entries {
\t\tif ent.IsDir() {
\t\t\tcontinue
\t\t}
\t\traw, err := os.ReadFile(filepath.Join(dataRoot, "events", ent.Name()))
\t\tif err != nil {
\t\t\treturn nil, "", err
\t\t}
\t\tvar row evtRow
\t\tif err := json.Unmarshal(raw, &row); err != nil {
\t\t\treturn nil, "", err
\t\t}
\t\trows = append(rows, row)
\t}
\tsort.Slice(rows, func(i, j int) bool { return rows[i].Seq < rows[j].Seq })
\tpulls := pullsEnabled(dataRoot)
\tfor _, row := range rows {
\t\tif uint64(row.Seq) > seq {
\t\t\tbreak
\t\t}
\t\tif row.Op == "pull" && !pulls {
\t\t\tcontinue
\t\t}
\t\tapplyEvt(tracks, row)
\t}
\tdigest, err := digestTracks(tracks)
\tif err != nil {
\t\treturn nil, "", err
\t}
\treturn tracks, digest, nil
}

func applyEvt(tracks map[string][]string, row evtRow) {
\tcars := tracks[row.Track]
\tif row.Op == "place" {
\t\tfiltered := make([]string, 0, len(cars))
\t\tfor _, c := range cars {
\t\t\tif c != row.Car {
\t\t\t\tfiltered = append(filtered, c)
\t\t\t}
\t\t}
\t\tpos := row.Pos
\t\tif pos < 0 {
\t\t\tpos = 0
\t\t}
\t\tif pos > len(filtered) {
\t\t\tpos = len(filtered)
\t\t}
\t\tfiltered = append(filtered[:pos], append([]string{row.Car}, filtered[pos:]...)...)
\t\ttracks[row.Track] = filtered
\t\treturn
\t}
\tif row.Op == "pull" {
\t\tfiltered := make([]string, 0, len(cars))
\t\tfor _, c := range cars {
\t\t\tif c != row.Car {
\t\t\t\tfiltered = append(filtered, c)
\t\t\t}
\t\t}
\t\ttracks[row.Track] = filtered
\t}
}

func digestTracks(tracks map[string][]string) (string, error) {
\tkeys := make([]string, 0, len(tracks))
\tfor k := range tracks {
\t\tkeys = append(keys, k)
\t}
\tsort.Strings(keys)
\tordered := make(map[string][]string, len(keys))
\tfor _, k := range keys {
\t\tordered[k] = append([]string(nil), tracks[k]...)
\t}
\tpayload, err := json.Marshal(ordered)
\tif err != nil {
\t\treturn "", err
\t}
\tsum := sha256Sum(payload)
\treturn sum, nil
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

func sha256Sum(payload []byte) string {
\tsum := sha256.Sum256(payload)
\treturn hex.EncodeToString(sum[:])
}
""",
    )
    w(
        TASK / "environment" / "lane" / "internal" / "m7" / "window.go",
        """package m7

// WindowShift is a standalone helper not wired into emit.
func WindowShift(seq uint64) uint64 {
\tif seq == 0 {
\t\treturn 0
\t}
\treturn seq - 1
}
""",
    )


def write_rust_ledger() -> None:
    ledger = TASK / "environment" / "ledger"
    w(
        ledger / "Cargo.toml",
        """[workspace]
members = ["yardctl", "core"]
resolver = "2"

[workspace.package]
edition = "2021"
""",
    )
    w(ledger / "Cargo.lock", "")
    w(
        ledger / "core" / "Cargo.toml",
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
        ledger / "core" / "src" / "lib.rs",
        """use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize)]
pub struct EventRow {
    pub seq: u64,
    pub op: String,
    pub track: String,
    pub car: String,
    #[serde(default)]
    pub pos: usize,
}

#[derive(Debug, Deserialize)]
pub struct RuntimeState {
    pub active_seq: u64,
    pub last_replay_seq: u64,
    pub movement_head: u64,
}

#[derive(Debug, Serialize)]
pub struct ConsistReport {
    pub replay_seq: u64,
    pub tracks: BTreeMap<String, Vec<String>>,
    pub audit_digest: String,
}

pub fn apply_event(tracks: &mut BTreeMap<String, Vec<String>>, row: &EventRow) {
    let cars = tracks.entry(row.track.clone()).or_default();
    match row.op.as_str() {
        "place" => {
            cars.retain(|c| c != &row.car);
            let mut pos = row.pos;
            if pos > cars.len() {
                pos = cars.len();
            }
            cars.insert(pos, row.car.clone());
        }
        "pull" => {
            cars.retain(|c| c != &row.car);
        }
        _ => {}
    }
}

pub fn load_events(dir: &Path) -> std::io::Result<Vec<EventRow>> {
    let mut rows = Vec::new();
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        if !entry.path().extension().map(|e| e == "json").unwrap_or(false) {
            continue;
        }
        let raw = fs::read_to_string(entry.path())?;
        let row: EventRow = serde_json::from_str(&raw)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
        rows.push(row);
    }
    rows.sort_by_key(|r| r.seq);
    Ok(rows)
}

pub fn consist_at(rows: &[EventRow], seq: u64) -> BTreeMap<String, Vec<String>> {
    let mut tracks = BTreeMap::new();
    for row in rows {
        if row.seq > seq {
            break;
        }
        apply_event(&mut tracks, row);
    }
    tracks
}

pub fn audit_digest(tracks: &BTreeMap<String, Vec<String>>) -> String {
    let payload = serde_json::to_string(tracks).unwrap_or_default();
    let mut h = Sha256::new();
    h.update(payload.as_bytes());
    hex::encode(h.finalize())
}

pub fn read_runtime(path: &Path) -> std::io::Result<RuntimeState> {
    let raw = fs::read_to_string(path)?;
    Ok(serde_json::from_str(&raw)?)
}

pub fn read_journal_pin(config_dir: &Path) -> std::io::Result<u64> {
    let path = config_dir.join("k9.toml");
    let raw = fs::read_to_string(path)?;
    for line in raw.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("journal_pin") {
            let rhs = trimmed.split('=').nth(1).unwrap_or("0").trim();
            return Ok(rhs.parse().unwrap_or(0));
        }
    }
    Ok(0)
}

pub fn read_seq_floor(config_dir: &Path) -> std::io::Result<u64> {
    let path = config_dir.join("k9.toml");
    let raw = fs::read_to_string(path)?;
    for line in raw.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("seq_floor") {
            let rhs = trimmed.split('=').nth(1).unwrap_or("0").trim();
            return Ok(rhs.parse().unwrap_or(0));
        }
    }
    Ok(0)
}

pub fn seq_cut(state: &RuntimeState, floor: u64) -> u64 {
    let mut s = state.active_seq;
    if floor > 0 && floor < s {
        s = floor;
    }
    if s > state.movement_head {
        s = state.movement_head;
    }
    s
}

pub fn build_report(data_root: &Path, config_dir: &Path) -> std::io::Result<ConsistReport> {
    let events_dir = data_root.join("events");
    let runtime = read_runtime(&data_root.join("state/runtime.json"))?;
    let floor = read_seq_floor(config_dir)?;
    let pin = read_journal_pin(config_dir)?;
    let seq = seq_cut(&runtime, floor);
    let mut rows = load_events(&events_dir)?;
    if pin > 0 {
        rows.retain(|row| row.seq <= pin);
    }
    let tracks = consist_at(&rows, seq);
    let digest = audit_digest(&tracks);
    Ok(ConsistReport {
        replay_seq: seq,
        tracks,
        audit_digest: digest,
    })
}
""",
    )
    w(
        ledger / "yardctl" / "Cargo.toml",
        """[package]
name = "yardctl"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "yardctl"
path = "src/main.rs"

[dependencies]
core = { path = "../core" }
serde_json = "1"
clap = { version = "4", features = ["derive"] }
""",
    )
    w(
        ledger / "core" / "src" / "journal.rs",
        """pub fn pin_ceiling(pin: u64, seq: u64) -> u64 {
    if pin > 0 && seq > pin {
        pin
    } else {
        seq
    }
}
""",
    )
    w(
        ledger / "yardctl" / "src" / "main.rs",
        """use clap::{Parser, Subcommand};
use core::build_report;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Parser)]
#[command(name = "yardctl")]
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
            println!("{{\\\"replay_seq\\\":{}}}", report.replay_seq);
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


def write_ops_helpers() -> None:
    w(
        TASK / "environment" / "ops" / "scripts" / "tier_head.py",
        '''#!/usr/bin/env python3
"""Print max and min tier heads for movement journals."""

from __future__ import annotations

import json
from pathlib import Path


def tier_head(path: Path) -> int:
    head = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        head = max(head, int(rec["seq"]))
    return head


def main() -> None:
    root = Path("/app/data/movements")
    heads = {p.stem.replace("tier_", ""): tier_head(p) for p in sorted(root.glob("tier_*.jsonl"))}
    print(json.dumps(heads, sort_keys=True))


if __name__ == "__main__":
    main()
''',
    )


def write_consist_lab() -> None:
    w(
        TASK / "environment" / "ops" / "scripts" / "consist_lab.py",
        '''#!/usr/bin/env python3
"""Reference probe helper for movement fixtures (uses same SHA-256 rules as yardctl)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def apply_movement(tracks: dict[str, list[str]], row: dict) -> None:
    track = row["track"]
    car = row["car"]
    tracks.setdefault(track, [])
    if row["op"] == "place":
        pos = int(row["pos"])
        tracks[track] = [c for c in tracks[track] if c != car]
        pos = max(0, min(pos, len(tracks[track])))
        tracks[track].insert(pos, car)
    elif row["op"] == "pull":
        tracks[track] = [c for c in tracks[track] if c != car]


def consist_at(seq: int, events_dir: Path) -> dict[str, list[str]]:
    tracks: dict[str, list[str]] = {}
    rows = []
    for path in sorted(events_dir.glob("evt_*.json")):
        rows.append(json.loads(path.read_text()))
    rows.sort(key=lambda r: int(r["seq"]))
    for row in rows:
        if int(row["seq"]) > seq:
            break
        apply_movement(tracks, row)
    return {k: tracks[k][:] for k in sorted(tracks)}


def audit_digest(tracks: dict[str, list[str]]) -> str:
    body = json.dumps(tracks, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()


def main() -> None:
    seq = int(sys.argv[1])
    events_dir = Path("/app/data/events")
    tracks = consist_at(seq, events_dir)
    payload = {"replay_seq": seq, "tracks": tracks, "audit_digest": audit_digest(tracks)}
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
''',
    )


def write_runbook() -> None:
    w(
        TASK / "environment" / "ops" / "runbooks" / "yard_usage.md",
        """# yard consist export contract

## Promoted movement head

Compute the promoted head as the maximum `seq` across every `/app/data/movements/tier_*.jsonl` record. A live `lane probe` value, a single-tier head, or a pin cleared to `0` is not the promoted head unless it equals that maximum.

## Operator tables (`/app/config/l7/*.toml`)

| Field | Required end state |
|-------|--------------------|
| `journal_pin` | equal to the promoted movement head (pin to that head; do not clear to `0`) |
| `seq_floor` | equal to the promoted movement head |
| `replay_gate` | `0` so pull operations apply during reconstruction |
| `tier_reducer` | `"max"` so the movement audit selects the promoted head across tiers |

## Runtime and inputs

- `/app/data/state/runtime.json` → `active_seq` must equal the promoted movement head.
- Do not hand-edit car registry fixtures under `/app/data/cars/`.
- Do not modify Go sources under `/app/lane/` or Rust sources under `/app/ledger/`.

## Report and probes

- `yardctl report --out PATH` emits JSON with `replay_seq`, `tracks`, and `audit_digest`.
- `lane probe` prints the replay sequence selected by the movement audit lane.
- `/app/ops/scripts/consist_lab.py SEQ` prints the fixture-derived track map and audit digest for a replay sequence; the delivered report must match that probe at the promoted head.
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

WORKDIR /build/ledger
COPY ledger/Cargo.toml ledger/Cargo.lock ./
COPY ledger/core/Cargo.toml core/
COPY ledger/yardctl/Cargo.toml yardctl/
COPY ledger/core/src/ core/src/
COPY ledger/yardctl/src/ yardctl/src/
RUN cargo generate-lockfile && cargo build --release --locked -p yardctl

FROM {CANONICAL_GOLANG}

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before any other setup.
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        tmux \\
        asciinema \\
        libutempter0 \\
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
COPY --from=rsbuilder /build/ledger/target /app/ledger/target
COPY --from=gobuilder --chmod=755 /out/lane /app/bin/lane
COPY --from=rsbuilder --chmod=755 /build/ledger/target/release/yardctl /app/bin/yardctl
COPY config/ /app/config/
COPY data/ /app/data/
COPY lane/ /app/lane/
COPY ledger/ /app/ledger/
COPY --from=rsbuilder /build/ledger/Cargo.lock /app/ledger/Cargo.lock
COPY ops/ /app/ops/

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux send-keys -t _smoke 'echo tmux_ok' Enter \\
    && tmux capture-pane -t _smoke -p | grep -q tmux_ok \\
    && tmux kill-session -t _smoke

ENV PATH="/app/bin:/usr/local/cargo/bin:/usr/local/go/bin:${{PATH}}"
WORKDIR /app
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
tags = ["movement-journal", "track-map", "event-aggregation", "cross-language", "digest-reconciliation"]
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
        """Movement journals under `/app/data/movements/` and event payloads under `/app/data/events/` disagree after a partial yard replay. Aggregating place/pull operations into a consist track map at the promoted head drops the tank that should sit on the arrival track, leaves a ghost id on the departure spur, omits the hopper on the storage track, and fails the audit digest against `/app/ops/scripts/consist_lab.py`. Car registry rows under `/app/data/cars/` were not part of the incident — do not hand-edit them.

The promoted movement head is the maximum `seq` across all `/app/data/movements/tier_*.jsonl` journals. A partial-window probe reading, a shallow tier head, or clearing a pin to zero is not that head. Operator end-state for the consist export pipeline — including how `journal_pin`, `seq_floor`, `replay_gate`, `tier_reducer`, and runtime `active_seq` must relate to the promoted head — is in `/app/ops/runbooks/yard_usage.md`.

Recovery is operational only: edit operator tables under `/app/config/l7/` and runtime state under `/app/data/state/`, then run `/app/bin/yardctl` and `/app/bin/lane`. Do not change Go sources under `/app/lane/` or Rust sources under `/app/ledger/`.

Write `/output/consist-report.json` using `/app/bin/yardctl report --out /output/consist-report.json`. The report includes integer `replay_seq`, a `tracks` object mapping each visible track id to ordered car ids, and hex string `audit_digest`. Values agree with `/app/ops/scripts/consist_lab.py` at the promoted movement head. `/app/bin/lane probe` prints the same integer as `replay_seq`.
""",
    )
    w(
        TASK / "output_contract.toml",
        f"""user_visible_outputs = [
  "/output/{REPORT_NAME}",
  "/app/bin/lane",
  "/app/bin/yardctl",
]

internal_harness_files = [
  "/app/lane/internal",
  "/app/ledger/core/src",
]

[structured_outputs.consist_report]
target = "/output/{REPORT_NAME}"
format = "json"
instruction_checks = [
  "replay_seq",
  "tracks",
  "audit_digest",
  "journal_pin",
  "seq_floor",
  "replay_gate",
  "tier_reducer",
  "active_seq",
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
import os
import subprocess
from pathlib import Path

LANE = "/app/bin/lane"
YARDCTL = "/app/bin/yardctl"
CONSIST_LAB = "/app/ops/scripts/consist_lab.py"
REPORT_PATH = Path("/output/consist-report.json")
DATA = Path("/app/data")
CFG = Path("/app/config/l7")
CARS_DIR = DATA / "cars"

EXPECTED_CARS = {
    "C101": {"id": "C101", "kind": "box", "since": 1},
    "C102": {"id": "C102", "kind": "box", "since": 1},
    "C103": {"id": "C103", "kind": "tank", "since": 3},
    "C104": {"id": "C104", "kind": "flat", "since": 6},
    "C105": {"id": "C105", "kind": "hopper", "since": 7},
}


def _movement_head() -> int:
    head = 0
    for path in sorted((DATA / "movements").glob("tier_*.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            head = max(head, int(rec["seq"]))
    return head


def _expected(seq: int) -> dict:
    raw = subprocess.run(
        ["python3", CONSIST_LAB, str(seq)],
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


def test_rebuilt_binaries_executable():
    """Shipped lane and yardctl binaries are present and executable."""
    for path in (LANE, YARDCTL):
        assert os.path.isfile(path)
        assert os.access(path, os.X_OK)


def test_car_fixtures_unmodified():
    """Car fixture records under /app/data/cars/ remain unmodified."""
    for car_id, expected in EXPECTED_CARS.items():
        payload = json.loads((CARS_DIR / f"{car_id}.json").read_text())
        assert payload == expected


def test_track_t1_lead_car():
    """Lead car on T1 resolves to fixture-derived order at promoted sequence."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert report["tracks"]["T1"][0] == expected["tracks"]["T1"][0]


def test_track_t1_second_car():
    """Second T1 slot matches fixture-derived movement window."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert report["tracks"]["T1"][1] == expected["tracks"]["T1"][1]


def test_track_t1_third_car():
    """Late-arrival car on T1 matches fixture expectations at promoted head."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert report["tracks"]["T1"][2] == expected["tracks"]["T1"][2]


def test_track_map_complete():
    """Every fixture-visible track id appears in the yard report with matching car order."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert set(report["tracks"]) == set(expected["tracks"])
    for track_id, cars in expected["tracks"].items():
        assert report["tracks"][track_id] == cars


def test_promoted_car_on_t1():
    """T1 car count at promoted head exceeds the partial-replay window."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert len(report["tracks"]["T1"]) == len(expected["tracks"]["T1"])
    assert report["tracks"]["T1"] == expected["tracks"]["T1"]


def test_track_t2_tail_car():
    """T2 tail car matches fixture-derived movement window at promoted head."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert report["tracks"]["T2"] == expected["tracks"]["T2"]


def test_track_t3_hopper_car():
    """Hopper staged on the storage track matches fixture expectations at promoted head."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert report["tracks"]["T3"] == expected["tracks"]["T3"]


def test_relocated_tank_not_ghosted_on_departure_spur():
    """Relocated tank id is absent from the departure spur once replay reaches the promoted head."""
    seq = _movement_head()
    report = json.loads(REPORT_PATH.read_text())
    assert report["replay_seq"] == seq
    assert "C103" not in report["tracks"].get("T2", [])


def test_audit_digest_matches_fixture_probe():
    """Audit digest matches fixture-derived consist probe at movement head."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert report["audit_digest"] == expected["audit_digest"]


def test_replay_seq_matches_movement_head():
    """Report replay sequence equals movement-derived head."""
    head = _movement_head()
    report = json.loads(REPORT_PATH.read_text())
    runtime = json.loads((DATA / "state" / "runtime.json").read_text())
    assert report["replay_seq"] == head
    assert runtime["active_seq"] == head


def test_lane_probe_alignment():
    """Lane movement probe agrees with yard report replay sequence."""
    report = json.loads(REPORT_PATH.read_text())
    lane_seq = int(_run([LANE, "probe"]))
    assert lane_seq == report["replay_seq"]


def test_config_journal_pin_cleared():
    """Operator journal pin matches the promoted movement head."""
    head = _movement_head()
    assert _config_field("journal_pin") == head


def test_config_seq_floor_cleared():
    """Operator sequence floor matches the promoted movement head."""
    head = _movement_head()
    assert _config_field("seq_floor") == head


def test_replay_gate_allows_pull_replay():
    """Movement replay gate permits pull operations during consist reconstruction."""
    assert _config_field("replay_gate") == 0


def test_tier_reducer_uses_promoted_head():
    """Movement tier reducer mode selects the promoted head rather than the shallowest tier."""
    assert _config_field("tier_reducer") == "max"


def test_runtime_active_matches_head():
    """Runtime active replay sequence matches movement-derived head."""
    runtime = json.loads((DATA / "state" / "runtime.json").read_text())
    head = _movement_head()
    assert runtime["active_seq"] == head


def test_output_json_schema_valid():
    """Yard report exposes required fields with valid types."""
    assert REPORT_PATH.is_file(), "consist report missing"
    payload = json.loads(REPORT_PATH.read_text())
    assert isinstance(payload.get("replay_seq"), int)
    assert isinstance(payload.get("audit_digest"), str)
    tracks = payload.get("tracks")
    assert isinstance(tracks, dict)
    for cars in tracks.values():
        assert isinstance(cars, list)
        for car in cars:
            assert isinstance(car, str)
    int(payload["audit_digest"], 16)
''',
    )


def fixed_seq_go() -> str:
    return '''package m7

import (
	"bufio"
	"encoding/json"
	"os"
	"path/filepath"

	"lab.local/yard_lane/pkg/frame"
)

func scanTierHead(movementDir, tier string) (uint64, error) {
	path := filepath.Join(movementDir, "tier_"+tier+".jsonl")
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
		if row.Seq > head {
			head = row.Seq
		}
	}
	if err := scan.Err(); err != nil {
		return 0, err
	}
	return head, nil
}

func ResolveSeq(movementDir string) (uint64, error) {
	var head uint64
	for _, tier := range []string{"a", "b", "c"} {
		tierHead, err := scanTierHead(movementDir, tier)
		if err != nil {
			continue
		}
		if tierHead > head {
			head = tierHead
		}
	}
	if head == 0 {
		return 0, os.ErrNotExist
	}
	return head, nil
}
'''


def fixed_probe_go() -> str:
    return '''package m7

import (
	"encoding/json"
	"os"
	"path/filepath"

	"lab.local/yard_lane/pkg/frame"
)

func WriteProbe(outPath, dataRoot string) error {
	seq, err := ResolveSeq(filepath.Join(dataRoot, "movements"))
	if err != nil {
		return err
	}
	tracks, digest, err := readWindowSnapshot(dataRoot, seq)
	if err != nil {
		return err
	}
	doc := frame.SummaryDoc{
		ReplaySeq:   seq,
		Tracks:      tracks,
		AuditDigest: digest,
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

func readWindowSnapshot(dataRoot string, seq uint64) (map[string][]string, string, error) {
	return buildAt(dataRoot, seq)
}
'''


def write_solution() -> None:
    w(
        TASK / "solution" / "solve.sh",
        """#!/bin/bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/cargo/bin:/app/bin:${PATH}"

test -d /app/config/l7
test -x /app/bin/yardctl
test -x /app/bin/lane
mkdir -p /output /app/ops/staging

read -r HEAD < <(
python3 <<'PY'
import json
from pathlib import Path

head = 0
tiers = {}
for path in sorted(Path("/app/data/movements").glob("tier_*.jsonl")):
    tier_head = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        seq = int(rec["seq"])
        head = max(head, seq)
        tier_head = max(tier_head, seq)
    tiers[path.stem] = tier_head
if head == 0:
    raise SystemExit("could not derive movement head")
if max(tiers.values()) != head:
    raise SystemExit("tier head map inconsistent with promoted head")
print(head)
PY
)

cat > /app/config/l7/k9.toml <<EOF
journal_pin = ${HEAD}
seq_floor = ${HEAD}
yard_ready = true
audit_stamp = "applied"
anchor_mode = "promoted"
EOF

cat > /app/config/l7/m2.toml <<EOF
tier_reducer = "max"
replay_gate = 0
barrier_live = true
window_scan = true
EOF

cat > /app/config/l7/p7.toml <<EOF
phases = ["scan", "bind", "emit"]
strict_chain = true
allow_batch = false
workflow_note = "promoted"
EOF

cat > /app/config/l7/n3.toml <<EOF
track_cap = 8
probe_stride = 1
hold_back = false
EOF

cat > /app/config/l7/r8.toml <<EOF
audit_mode = "promoted"
emit_lane = "primary"
retry_ms = 100
EOF

cat > /app/data/state/runtime.json <<EOF
{
  "active_seq": ${HEAD},
  "last_replay_seq": ${HEAD},
  "movement_head": ${HEAD},
  "partial_cutoff": 0
}
EOF

python3 <<'PY'
import json
from pathlib import Path

rows = []
for path in sorted(Path("/app/data/movements").glob("tier_*.jsonl")):
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        rows.append(
            {
                "tier": rec.get("tier", path.stem.replace("tier_", "")),
                "seq": int(rec["seq"]),
                "stamp": rec.get("stamp", ""),
            }
        )
rows.sort(key=lambda r: (r["seq"], r["tier"]))
Path("/app/data/sidecars/movements.idx").write_text(
    "".join(json.dumps(r, sort_keys=True) + "\\n" for r in rows)
)
PY

python3 <<PY
import json
import subprocess
from pathlib import Path

head = int("${HEAD}")
probe = subprocess.run(
    ["python3", "/app/ops/scripts/consist_lab.py", str(head)],
    check=True,
    capture_output=True,
    text=True,
)
expected = json.loads(probe.stdout)
for track in ("T1", "T2", "T3"):
    if track not in expected["tracks"]:
        raise SystemExit(f"missing expected track {track}")
if len(expected["tracks"]["T1"]) < 3:
    raise SystemExit("promoted T1 window too short")
if "C103" in expected["tracks"].get("T2", []):
    raise SystemExit("reference probe still ghosts tank on departure spur")

runtime = json.loads(Path("/app/data/state/runtime.json").read_text())
if runtime["active_seq"] != head:
    raise SystemExit("runtime active_seq not promoted")
PY

/app/bin/yardctl report --out /output/consist-report.json

lane_seq=$(/app/bin/lane probe)
report_seq=$(python3 -c "import json; print(json.load(open('/output/consist-report.json'))['replay_seq'])")
test "${lane_seq}" -eq "${report_seq}"
test "${report_seq}" -eq "${HEAD}"

probe=$(python3 /app/ops/scripts/consist_lab.py "${HEAD}")
report_digest=$(python3 -c "import json; print(json.load(open('/output/consist-report.json'))['audit_digest'])")
expected_digest=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['audit_digest'])" "${probe}")
test "${report_digest}" = "${expected_digest}"

python3 <<PY
import json
from pathlib import Path

head = int("${HEAD}")
report = json.loads(Path("/output/consist-report.json").read_text())
assert report["replay_seq"] == head
assert isinstance(report["audit_digest"], str) and int(report["audit_digest"], 16) >= 0
assert "T3" in report["tracks"]
print(json.dumps({"promoted_head": head, "tracks": sorted(report["tracks"])}, sort_keys=True))
PY

echo "complete" > /app/ops/staging/workflow.complete
""",
    )
    (TASK / "solution" / "solve.sh").chmod(0o755)



def write_spec() -> None:
    w(
        ROOT / "specs" / "rail-yard-consist-recovery.md",
        """# rail-yard-consist-recovery

## Authoring Brief

Symptoms-only instruction describing diverged train consist assignments after partial yard replay. Agent may edit `/app/config/l7/`, Go movement audit lane, and Rust consist ledger. Tests derive expected track maps and audit digests from `/app/data/events/` fixtures and movement head. Output `/output/consist-report.json` with `replay_seq`, `tracks`, and `audit_digest`. `lane probe` must match `replay_seq`.

### Failure topology
Three authorities lag after promotion: Go ResolveSeq scans tier_b (seq 3) while tier_c holds seq 6; Rust seq_cut prefers last_replay_seq; operator replay_watermark pins sequence 3. C103 on T1 absent until all three align.

### Triviality Ledger
- Config-only without lane tier fix leaves seq at 3 — blocked by lane_probe_alignment.
- Lane-only without Rust seq_cut leaves stale tracks — blocked by promoted_car_on_t1.
- Rust-only without config watermark keeps seq_cut capped — blocked by config_replay_watermark_cleared.

### Per-gate Pitfall Inventory
- RC1: oracle touches config, Go seq.go/probe.go, Rust seq_cut — multi-file.
- RC3/GX3: decoy k3/ScanTierA rhymes with ResolveSeq but unwired.
- CR7: code_forbidden_tokens on fix-path symbols.

### Construction manifest

#### symbol_table
- path: lane/internal/m7/seq.go
  symbol: pickTier
  kind: function
- path: lane/internal/m7/probe.go
  symbol: WriteProbe
  kind: function
- path: ledger/core/src/lib.rs
  symbol: seq_cut
  kind: function
- path: config/l7/k9.toml
  symbol: replay_watermark
  kind: constant

#### flipping_point_contract
locations:
  - id: A
    path: lane/internal/m7/seq.go
    controls_tests: [test_lane_probe_alignment, test_replay_seq_matches_movement_head]
  - id: B
    path: ledger/core/src/lib.rs
    controls_tests: [test_promoted_car_on_t1, test_audit_digest_matches_fixture_probe]
  - id: C
    path: config/l7/k9.toml
    controls_tests: [test_config_replay_watermark_cleared, test_runtime_active_matches_head]
no_single_location_flips_majority: true

#### code_forbidden_tokens
code_forbidden_tokens: [rail, yard, consist, train, movement, audit, replay, track, car, ledger, reconcile, probe, window, fixture, promote, sequence, head, digest, visible, operator, lane, yardctl, report, watermark, runtime, active, last, promoted, partial, diverged, assignment, aggregate, checks, fail, expectations, serving, started, landed, promotion, disk, still, hand-edit, files, under, paths, bin, may, code, changes, do, not, the, and, for, each, that, those, with, via, out, from, see, but, an, at, three, two, one, four, five, six, seven, eight, nine, ten]
""",
    )


def main() -> None:
    if TASK.exists():
        shutil.rmtree(TASK)
    write_fixtures()
    write_config()
    write_go_lane()
    patch_lane_apply()
    write_rust_ledger()
    write_consist_lab()
    write_ops_helpers()
    write_runbook()
    write_dockerfile()
    write_metadata()
    write_tests()
    write_solution()
    write_spec()
    stale = consist_at(STALE_SEQ)
    head = consist_at(HEAD_SEQ)
    assert stale != head
    assert "C103" not in stale.get("T1", [])
    assert "C103" in head.get("T1", [])
    assert "C105" in head.get("T3", [])
    assert audit_digest(STALE_SEQ) != audit_digest(HEAD_SEQ)
    env_files = sum(1 for _ in (TASK / "environment").rglob("*") if _.is_file())
    print(f"Generated {TASK} ({env_files} environment files)")
    print(f"HEAD digest={audit_digest(HEAD_SEQ)} STALE digest={audit_digest(STALE_SEQ)}")


if __name__ == "__main__":
    main()
