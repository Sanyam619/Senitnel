#!/usr/bin/env python3
"""Generator for tasks/partition-invariant-reduction-reconstruction (authoring tool)."""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "partition-invariant-reduction-reconstruction"
ENV = TASK / "environment"

N = 512
OVERLAP = 1
SCENARIOS = ("tape_alpha", "tape_beta", "tape_gamma")
LAYOUTS = ("pack_1", "pack_2", "pack_4", "pack_8")


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def f64_bits(x: float) -> str:
    return format(struct.unpack(">Q", struct.pack(">d", x))[0], "016x")


def kahan_sum(values: list[float]) -> float:
    total = 0.0
    comp = 0.0
    for v in values:
        y = v - comp
        t = total + y
        comp = (t - total) - y
        total = t
    return total


def make_vectors(name: str) -> dict:
    rng_seed = {"tape_alpha": 11, "tape_beta": 29, "tape_gamma": 47}[name]
    a: list[float] = []
    b: list[float] = []
    wts: list[float] = []
    state = rng_seed
    # Stick to dyadic rationals so JSON <-> f64 round-trips are bit-stable.
    scales = {
        "tape_alpha": (1.0, 0.25, 0.5),
        "tape_beta": (8.0, 0.125, 2.0),
        "tape_gamma": (16.0, 0.0625, 4.0),
    }
    mag_a, mag_b, _ = scales[name]
    for i in range(N):
        state = (state * 1_103_515_245 + 12_345) & 0x7FFFFFFF
        qa = ((state % 17) - 8) / 16.0
        a.append(qa * mag_a)
        state = (state * 1_103_515_245 + 54_321) & 0x7FFFFFFF
        qb = ((state % 13) - 6) / 16.0
        b.append(qb * mag_b)
        wts.append(0.5 + (i % 7) * 0.125)
    return {"a": a, "b": b, "w": wts}


def canonical_scalars(vecs: dict) -> dict:
    a, b, wts = vecs["a"], vecs["b"], vecs["w"]
    ordered = sorted(range(N), key=lambda i: i)
    sum_w = kahan_sum(wts[i] * a[i] for i in ordered)
    dot_ab = kahan_sum(a[i] * b[i] for i in ordered)
    l2_sq = kahan_sum(a[i] * a[i] for i in ordered)
    return {
        "sum_w_bits": f64_bits(sum_w),
        "dot_ab_bits": f64_bits(dot_ab),
        "l2_sq_bits": f64_bits(l2_sq),
    }


def layout_ranges(ranks: int) -> list[tuple[int, int]]:
    chunk = N // ranks
    ranges: list[tuple[int, int]] = []
    for r in range(ranks):
        lo = r * chunk
        hi = N if r == ranks - 1 else (r + 1) * chunk
        ranges.append((lo, hi))
    return ranges


def overlap_owners(ranks: int) -> dict[str, int]:
    owners: dict[str, int] = {}
    chunk = N // ranks
    for r in range(ranks - 1):
        cell = (r + 1) * chunk
        owners[str(cell)] = r
    return owners


def buggy_local_values(vecs: dict, ranks: int, rank: int) -> list[tuple[int, float, float, float]]:
    """Return (global_idx, a, b, w) included by buggy gather (double overlap)."""
    ranges = layout_ranges(ranks)
    lo, hi = ranges[rank]
    out: list[tuple[int, float, float, float]] = []
    for i in range(lo, hi):
        out.append((i, vecs["a"][i], vecs["b"][i], vecs["w"][i]))
    if rank < ranks - 1 and OVERLAP > 0:
        ghost = hi
        if ghost < N:
            out.append((ghost, vecs["a"][ghost], vecs["b"][ghost], vecs["w"][ghost]))
    if rank > 0 and OVERLAP > 0:
        ghost = lo
        out.append((lo, vecs["a"][lo], vecs["b"][lo], vecs["w"][lo]))
    return out


def naive_tree_sum(values: list[float], ranks: int) -> float:
    """Simulate rank-order-sensitive tree reduction."""
    if not values:
        return 0.0
    layer = values[:]
    step = 0
    while len(layer) > 1:
        nxt: list[float] = []
        i = 0
        while i < len(layer):
            if i + 1 < len(layer):
                left, right = layer[i], layer[i + 1]
                if (step + i) % ranks == 0:
                    nxt.append(left + right)
                else:
                    nxt.append(right + left)
                i += 2
            else:
                nxt.append(layer[i])
                i += 1
        layer = nxt
        step += 1
    return layer[0]


def buggy_scalars(vecs: dict, ranks: int) -> dict:
    locals_per_rank: list[list[tuple[int, float, float, float]]] = []
    for r in range(ranks):
        locals_per_rank.append(buggy_local_values(vecs, ranks, r))

    def reduce_metric(metric: str) -> float:
        per_rank_vals: list[float] = []
        for chunk in locals_per_rank:
            if metric == "sum_w":
                per_rank_vals.append(sum(w * a for _, a, _, w in chunk))
            elif metric == "dot_ab":
                per_rank_vals.append(sum(a * b for _, a, b, _ in chunk))
            else:
                per_rank_vals.append(sum(a * a for _, a, _, _ in chunk))
        return naive_tree_sum(per_rank_vals, ranks)

    return {
        "sum_w_bits": f64_bits(reduce_metric("sum_w")),
        "dot_ab_bits": f64_bits(reduce_metric("dot_ab")),
        "l2_sq_bits": f64_bits(reduce_metric("l2_sq")),
    }


def write_data() -> dict:
    golden: dict = {}
    for sc in SCENARIOS:
        vecs = make_vectors(sc)
        vec_path = ENV / "data" / "checkpoints" / f"{sc}.json"
        w(vec_path, json.dumps({"length": N, "a": vecs["a"], "b": vecs["b"], "w": vecs["w"]}, indent=2))
        golden[sc] = canonical_scalars(vecs)

    for layout in LAYOUTS:
        ranks = int(layout.split("_")[1])
        ranges = layout_ranges(ranks)
        lines = [
            f'name = "{layout}"',
            f"ranks = {ranks}",
            f"overlap = {OVERLAP}",
            "segments = [",
        ]
        for i, (lo, hi) in enumerate(ranges):
            lines.append(f'  {{ rank = {i}, lo = {lo}, hi = {hi} }},')
        lines.append("]")
        w(ENV / "data" / "layouts" / f"{layout}.toml", "\n".join(lines) + "\n")

    owners_doc: dict = {}
    for layout in LAYOUTS:
        ranks = int(layout.split("_")[1])
        owners_doc[layout] = overlap_owners(ranks)
    w(ENV / "data" / "registry.toml", 'default_checkpoint_dir = "checkpoints"\n')
    return golden


def write_rust_sources() -> None:
    w(
        ENV / "ws" / "Cargo.toml",
        """[workspace]
members = ["m3", "m7", "m9", "m5"]
resolver = "2"

[workspace.package]
version = "0.1.0"
edition = "2021"
""",
    )

    w(
        ENV / "ws" / "m3" / "Cargo.toml",
        """[package]
name = "m3"
version.workspace = true
edition.workspace = true

[dependencies]
serde = { version = "1", features = ["derive"] }
""",
    )
    w(
        ENV / "ws" / "m3" / "src" / "lib.rs",
        """pub mod scalar;
pub mod types;
""",
    )
    w(
        ENV / "ws" / "m3" / "src" / "types.rs",
        """#[derive(Clone, Debug)]
pub struct Segment {
    pub rank: u32,
    pub lo: usize,
    pub hi: usize,
}

#[derive(Clone, Debug)]
pub struct LayoutSpec {
    pub name: String,
    pub ranks: u32,
    pub overlap: u32,
    pub segments: Vec<Segment>,
}

#[derive(Clone, Debug, serde::Serialize)]
pub struct MetricBundle {
    pub sum_w_bits: String,
    pub dot_ab_bits: String,
    pub l2_sq_bits: String,
}
""",
    )
    w(
        ENV / "ws" / "m3" / "src" / "scalar.rs",
        """pub fn wire_f64_bits(v: f64) -> String {
    format!("{:016x}", u64::from_le_bytes(v.to_le_bytes()))
}
""",
    )

    w(
        ENV / "ws" / "m7" / "Cargo.toml",
        """[package]
name = "m7"
version.workspace = true
edition.workspace = true

[dependencies]
m3 = { path = "../m3" }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
""",
    )
    w(
        ENV / "ws" / "m7" / "src" / "lib.rs",
        """pub mod edge;
pub mod load;
pub mod weights;
""",
    )
    w(
        ENV / "ws" / "m7" / "src" / "load.rs",
        """use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Checkpoint {
    pub length: usize,
    pub a: Vec<f64>,
    pub b: Vec<f64>,
    pub w: Vec<f64>,
}

pub fn read_checkpoint(path: &std::path::Path) -> std::io::Result<Checkpoint> {
    let raw = std::fs::read_to_string(path)?;
    let mut ck: Checkpoint = serde_json::from_str(&raw)?;
    if !ck.w.is_empty() {
        ck.w.rotate_left(1);
    }
    let _ = path;
    Ok(ck)
}
""",
    )
    w(
        ENV / "ws" / "m7" / "src" / "weights.rs",
        """pub fn blend(a: f64, w: f64) -> f64 {
    if w > 1.0 {
        a
    } else {
        w * a
    }
}
""",
    )
    w(
        ENV / "ws" / "m7" / "src" / "edge.rs",
        """use m3::types::Segment;

#[derive(Clone, Copy, Debug)]
pub struct Cell {
    pub idx: usize,
    pub a: f64,
    pub b: f64,
    pub w: f64,
}

pub fn gather_lane(seg: &Segment, ck: &crate::load::Checkpoint, overlap: u32) -> Vec<Cell> {
    let mut out = Vec::new();
    for i in seg.lo..seg.hi {
        out.push(Cell {
            idx: i,
            a: ck.a[i],
            b: ck.b[i],
            w: ck.w[i],
        });
    }
    if overlap > 0 {
        if seg.hi < ck.length {
            let g = seg.hi;
            let w_src = g.saturating_sub(1);
            out.push(Cell {
                idx: g,
                a: ck.a[g],
                b: ck.b[g],
                w: ck.w[w_src],
            });
        }
        if seg.lo > 0 {
            let g = seg.lo;
            out.push(Cell {
                idx: g,
                a: ck.a[g],
                b: ck.b[g],
                w: ck.w[g],
            });
        }
        if seg.hi > seg.lo + 1 {
            let mid = seg.lo + (seg.hi - seg.lo) / 2;
            out.push(Cell {
                idx: mid,
                a: ck.a[mid],
                b: ck.b[mid],
                w: ck.w[mid],
            });
        }
    }
    out
}
""",
    )

    w(
        ENV / "ws" / "m9" / "Cargo.toml",
        """[package]
name = "m9"
version.workspace = true
edition.workspace = true

[dependencies]
m3 = { path = "../m3" }
m7 = { path = "../m7" }
serde = { version = "1", features = ["derive"] }
""",
    )
    w(
        ENV / "ws" / "m9" / "src" / "lib.rs",
        """pub mod session;
pub mod stage;
pub mod topology;
""",
    )
    w(
        ENV / "ws" / "m9" / "src" / "topology.rs",
        """use m3::types::{LayoutSpec, Segment};
use std::path::Path;

pub fn read_layout(path: &Path) -> std::io::Result<LayoutSpec> {
    let raw = std::fs::read_to_string(path)?;
    let mut name = String::new();
    let mut ranks = 0u32;
    let mut overlap = 0u32;
    let mut segments: Vec<Segment> = Vec::new();
    for line in raw.lines() {
        let line = line.trim();
        if line.starts_with("name =") {
            name = line.split('"').nth(1).unwrap_or("").to_string();
        } else if line.starts_with("ranks =") {
            ranks = line.split('=').nth(1).unwrap().trim().parse().unwrap_or(0);
        } else if line.starts_with("overlap =") {
            overlap = line.split('=').nth(1).unwrap().trim().parse().unwrap_or(0);
        } else if line.contains("rank =") {
            let rank: u32 = line.split("rank =").nth(1).unwrap().split(',').next().unwrap().trim().parse().unwrap();
            let lo: usize = line.split("lo =").nth(1).unwrap().split(',').next().unwrap().trim().parse().unwrap();
            let hi: usize = line.split("hi =").nth(1).unwrap().split('}').next().unwrap().trim().parse().unwrap();
            segments.push(Segment { rank, lo, hi });
        }
    }
    if ranks > 2 {
        segments.reverse();
    }
    Ok(LayoutSpec {
        name,
        ranks,
        overlap,
        segments,
    })
}
""",
    )
    w(
        ENV / "ws" / "m9" / "src" / "stage.rs",
        """pub fn merge_lane(a: f64, b: f64, lane_tag: u32) -> f64 {
    if lane_tag % 2 == 0 {
        a + b
    } else {
        b + a
    }
}

pub fn fold_vec(vals: &[f64], width: u32) -> f64 {
    if vals.is_empty() {
        return 0.0;
    }
    let mut layer = vals.to_vec();
    let mut step = 0u32;
    while layer.len() > 1 {
        let mut nxt = Vec::new();
        let mut i = 0usize;
        while i < layer.len() {
            if i + 1 < layer.len() {
                let tag = step.wrapping_add(i as u32) % width.max(1);
                nxt.push(merge_lane(layer[i], layer[i + 1], tag));
                i += 2;
            } else if width <= 2 {
                nxt.push(layer[i]);
                i += 1;
            } else {
                i += 1;
            }
        }
        if nxt.is_empty() {
            break;
        }
        layer = nxt;
        step = step.wrapping_add(1);
    }
    layer[0]
}
""",
    )
    w(
        ENV / "ws" / "m9" / "src" / "session.rs",
        """use m3::scalar::wire_f64_bits;
use m3::types::{LayoutSpec, MetricBundle};
use m7::edge::Cell;
use m7::load::Checkpoint;
use m7::weights::blend;

use crate::stage::fold_vec;

pub fn run_session(layout: &LayoutSpec, ck: &Checkpoint) -> MetricBundle {
    let mut sum_locals = Vec::new();
    let mut dot_locals = Vec::new();
    let mut l2_locals = Vec::new();

    for seg in &layout.segments {
        let lane: Vec<Cell> = m7::edge::gather_lane(seg, ck, layout.overlap);
        let mut sum_acc = 0.0f64;
        let mut dot_acc = 0.0f64;
        let mut l2_acc = 0.0f64;
        for cell in lane {
            sum_acc += blend(cell.a, cell.w);
            dot_acc += cell.a * cell.b;
            l2_acc += cell.a * cell.a;
        }
        sum_locals.push(sum_acc);
        dot_locals.push(dot_acc);
        l2_locals.push(l2_acc);
    }

    let width = layout.ranks;
    MetricBundle {
        sum_w_bits: wire_f64_bits(fold_vec(&sum_locals, width)),
        dot_ab_bits: wire_f64_bits(fold_vec(&dot_locals, width)),
        l2_sq_bits: wire_f64_bits(fold_vec(&l2_locals, width)),
    }
}
""",
    )

    w(
        ENV / "ws" / "m5" / "Cargo.toml",
        """[package]
name = "m5"
version.workspace = true
edition.workspace = true

[[bin]]
name = "rx-run"
path = "src/main.rs"

[dependencies]
m3 = { path = "../m3" }
m7 = { path = "../m7" }
m9 = { path = "../m9" }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
""",
    )
    w(
        ENV / "ws" / "m5" / "src" / "dispatch.rs",
        """use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use m3::types::MetricBundle;
use m7::load::read_checkpoint;
use m9::session::run_session;
use m9::topology::read_layout;
use serde::Serialize;

#[derive(Serialize)]
pub struct Row {
    pub layout: String,
    pub scenario: String,
    #[serde(flatten)]
    pub metrics: MetricBundle,
}

pub fn all_layouts(data_root: &Path, out_dir: &Path) -> std::io::Result<()> {
    std::fs::create_dir_all(out_dir)?;
    let ck_dir = data_root.join("checkpoints");
    let layout_dir = data_root.join("layouts");
    let mut rows: Vec<Row> = Vec::new();
    let mut owners: BTreeMap<String, BTreeMap<String, u32>> = BTreeMap::new();

    for entry in std::fs::read_dir(&layout_dir)? {
        let path = entry?.path();
        if path.extension().and_then(|s| s.to_str()) != Some("toml") {
            continue;
        }
        let layout = read_layout(&path)?;
        let mut layout_owners: BTreeMap<String, u32> = BTreeMap::new();
        let last_rank = layout.ranks.saturating_sub(1);
        for seg in &layout.segments {
            if layout.overlap > 0 && seg.rank < last_rank {
                let owner = (seg.rank + 1).min(last_rank);
                layout_owners.insert(seg.hi.to_string(), owner);
            }
        }
        owners.insert(layout.name.clone(), layout_owners);

        for ck_entry in std::fs::read_dir(&ck_dir)? {
            let ck_path = ck_entry?.path();
            if ck_path.extension().and_then(|s| s.to_str()) != Some("json") {
                continue;
            }
            let scenario = ck_path.file_stem().unwrap().to_string_lossy().to_string();
            if !scenario.starts_with("tape_") {
                continue;
            }
            let ck = read_checkpoint(&ck_path)?;
            let metrics = run_session(&layout, &ck);
            rows.push(Row {
                layout: layout.name.clone(),
                scenario,
                metrics,
            });
        }
    }

    rows.sort_by(|a, b| (&a.layout, &a.scenario).cmp(&(&b.layout, &b.scenario)));
    let reductions = out_dir.join("reductions.json");
    std::fs::write(&reductions, serde_json::to_string_pretty(&rows)?)?;
    let ownership = out_dir.join("ownership.json");
    std::fs::write(&ownership, serde_json::to_string_pretty(&owners)?)?;
    Ok(())
}

pub fn default_data_root() -> PathBuf {
    PathBuf::from("/app/data")
}
""",
    )
    w(
        ENV / "ws" / "m5" / "src" / "main.rs",
        """mod dispatch;

use std::env;
use std::path::PathBuf;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: rx-run all-layouts --out-dir <dir>");
        std::process::exit(2);
    }
    if args[1] == "all-layouts" {
        let mut out = PathBuf::from("/output");
        let mut i = 2;
        while i < args.len() {
            if args[i] == "--out-dir" && i + 1 < args.len() {
                out = PathBuf::from(&args[i + 1]);
                i += 2;
            } else {
                i += 1;
            }
        }
        let data_root = dispatch::default_data_root();
        if let Err(e) = dispatch::all_layouts(&data_root, &out) {
            eprintln!("run failed: {e}");
            std::process::exit(1);
        }
        return;
    }
    eprintln!("unknown subcommand");
    std::process::exit(2);
}
""",
    )

    w(
        ENV / "ops" / "notes" / "layout_probe.md",
        """# layout probe notes

Fixture layouts live under `/app/data/layouts/`. Checkpoint tapes used in the last lab shift are under `/app/data/checkpoints/`.
Operators usually start a packing sweep from the workspace binary before comparing JSON under `/output`.
""",
    )

    w(
        ENV / ".dockerignore",
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
**/*.rs.bk
**/.cargo/
vendor/
""",
    )


def write_oracle_solution_files() -> dict[str, str]:
    files = {
        "m3/src/scalar.rs": """pub fn wire_f64_bits(v: f64) -> String {
    let bytes = v.to_be_bytes();
    let mut out = String::with_capacity(16);
    for b in bytes {
        out.push_str(&format!("{b:02x}"));
    }
    out
}
""",
        "m7/src/load.rs": """use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Checkpoint {
    pub length: usize,
    pub a: Vec<f64>,
    pub b: Vec<f64>,
    pub w: Vec<f64>,
}

pub fn read_checkpoint(path: &std::path::Path) -> std::io::Result<Checkpoint> {
    let raw = std::fs::read_to_string(path)?;
    let ck: Checkpoint = serde_json::from_str(&raw)?;
    if ck.a.len() != ck.length || ck.b.len() != ck.length || ck.w.len() != ck.length {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            "checkpoint lane length mismatch",
        ));
    }
    let _ = path;
    Ok(ck)
}
""",
        "m7/src/weights.rs": """pub fn blend(a: f64, w: f64) -> f64 {
    let mut acc = a;
    acc *= w;
    acc
}
""",
        "m7/src/edge.rs": """use m3::types::Segment;

#[derive(Clone, Copy, Debug)]
pub struct Cell {
    pub idx: usize,
    pub a: f64,
    pub b: f64,
    pub w: f64,
}

fn push_owned(out: &mut Vec<Cell>, ck: &crate::load::Checkpoint, idx: usize) {
    out.push(Cell {
        idx,
        a: ck.a[idx],
        b: ck.b[idx],
        w: ck.w[idx],
    });
}

pub fn gather_lane(seg: &Segment, ck: &crate::load::Checkpoint, _overlap: u32) -> Vec<Cell> {
    let mut out = Vec::with_capacity(seg.hi.saturating_sub(seg.lo));
    let lo = seg.lo.min(ck.length);
    let hi = seg.hi.min(ck.length);
    let mut i = lo;
    while i < hi {
        push_owned(&mut out, ck, i);
        i += 1;
    }
    out
}
""",
        "m9/src/stage.rs": """pub fn merge_lane(a: f64, b: f64, _lane_tag: u32) -> f64 {
    let mut s = a;
    s += b;
    s
}

pub fn fold_vec(vals: &[f64], _width: u32) -> f64 {
    if vals.is_empty() {
        return 0.0;
    }
    let mut layer = vals.to_vec();
    while layer.len() > 1 {
        let mut nxt = Vec::with_capacity(layer.len().div_ceil(2));
        let mut i = 0usize;
        while i < layer.len() {
            if i + 1 < layer.len() {
                nxt.push(merge_lane(layer[i], layer[i + 1], 0));
                i += 2;
            } else {
                nxt.push(layer[i]);
                i += 1;
            }
        }
        layer = nxt;
    }
    layer[0]
}
""",
        "m9/src/session.rs": """use m3::scalar::wire_f64_bits;
use m3::types::{LayoutSpec, MetricBundle};
use m7::edge::Cell;
use m7::load::Checkpoint;

fn reduce_mode(cells: &[Cell], mode: u8) -> f64 {
    let mut ordered: Vec<Cell> = Vec::with_capacity(cells.len());
    ordered.extend_from_slice(cells);
    ordered.sort_by_key(|c| c.idx);
    let mut write = 0usize;
    for read in 0..ordered.len() {
        if write == 0 || ordered[read].idx != ordered[write - 1].idx {
            ordered[write] = ordered[read];
            write += 1;
        }
    }
    ordered.truncate(write);

    let mut total = 0.0f64;
    for cell in &ordered {
        let v = match mode {
            0 => m7::weights::blend(cell.a, cell.w),
            1 => cell.a * cell.b,
            _ => cell.a * cell.a,
        };
        total = total + v;
    }
    total
}

pub fn run_session(layout: &LayoutSpec, ck: &Checkpoint) -> MetricBundle {
    let mut all_cells: Vec<Cell> = Vec::new();
    for seg in &layout.segments {
        all_cells.extend(m7::edge::gather_lane(seg, ck, layout.overlap));
    }
    MetricBundle {
        sum_w_bits: wire_f64_bits(reduce_mode(&all_cells, 0)),
        dot_ab_bits: wire_f64_bits(reduce_mode(&all_cells, 1)),
        l2_sq_bits: wire_f64_bits(reduce_mode(&all_cells, 2)),
    }
}
""",
    }
    for rel, body in files.items():
        w(TASK / "solution" / "oracle" / Path(rel).name, body)
    return files


def write_task_meta(golden: dict, oracle_files: dict[str, str]) -> None:
    w(
        TASK / "instruction.md",
        """Lab runs of the shardvec checkpoint runner stopped lining up after we started replaying the same tapes under several rank packings. Numbers that used to be stable across packings now disagree, and the boundary ownership sheet for shared cells no longer matches what the floor expects.

Rebuild `/app/ws` and write `/output/reductions.json` and `/output/ownership.json`. Each reductions row needs layout, scenario, sum_w_bits, dot_ab_bits, and l2_sq_bits. Over checkpoint lanes a, b, and w in index order, sum_w_bits is the bit pattern of the sum of w[i]*a[i] (a weighted sum of values — not the sum of the weights alone), dot_ab_bits is the sum of a[i]*b[i], and l2_sq_bits is the sum of a[i]*a[i]. The blend helper that forms each weighted contribution must perform plain multiplication of w and a. Those bit fields have to match across every layout under `/app/data/layouts/` for each tape_* checkpoint under `/app/data/checkpoints/`. ownership.json is per layout; with overlap on, an interior boundary cell belongs to the lower-numbered rank that ends on that index. Edit only Rust sources that implement the runner.
""",
    )

    w(
        TASK / "output_contract.toml",
        """user_visible_outputs = [
  "/output/reductions.json",
  "/output/ownership.json",
]

internal_harness_files = []

[structured_outputs.reductions]
target = "/output/reductions.json"
format = "json"
instruction_checks = [
  "layout",
  "scenario",
  "sum_w_bits",
  "dot_ab_bits",
  "l2_sq_bits",
  "blend",
]

[structured_outputs.ownership]
target = "/output/ownership.json"
format = "json"
instruction_checks = [
  "layout",
  "overlap",
]
""",
    )

    w(
        TASK / "task.toml",
        """version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "scientific-computing"
subcategories = []
number_of_milestones = 0
codebase_size = "small"
languages = ["rust"]
tags = ["floating-point", "distributed-simulation", "checkpoint", "numerical-reproducibility", "rust-workspace"]
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
        TASK / "construction_manifest.json",
        json.dumps(
            {
                "symbol_table": {
                    "wire_f64_bits": "m3/src/scalar.rs",
                    "read_checkpoint": "m7/src/load.rs",
                    "blend": "m7/src/weights.rs",
                    "gather_lane": "m7/src/edge.rs",
                    "read_layout": "m9/src/topology.rs",
                    "fold_vec": "m9/src/stage.rs",
                    "run_session": "m9/src/session.rs",
                    "all_layouts": "m5/src/dispatch.rs",
                },
                "flipping_point_contract": {
                    "concentration_cap": 0.5,
                    "locations": [
                        {
                            "path": "m3/src/scalar.rs",
                            "symbol": "wire_f64_bits",
                            "controls_tests": [
                                "test_scalars_match_canonical_bits",
                                "test_pack1_matches_canonical",
                            ],
                        },
                        {
                            "path": "m7/src/load.rs",
                            "symbol": "read_checkpoint",
                            "controls_tests": [
                                "test_scalars_match_canonical_bits",
                                "test_weighted_sum_uses_stored_weights",
                            ],
                        },
                        {
                            "path": "m7/src/edge.rs",
                            "symbol": "gather_lane",
                            "controls_tests": [
                                "test_overlap_stress_not_double_counted",
                                "test_cross_layout_bit_agreement",
                            ],
                        },
                        {
                            "path": "m9/src/session.rs",
                            "symbol": "run_session",
                            "controls_tests": [
                                "test_scalars_match_canonical_bits",
                                "test_cross_layout_bit_agreement",
                            ],
                        },
                    ],
                },
                "code_forbidden_tokens": [
                    "checkpoint",
                    "scalar",
                    "rank",
                    "layout",
                    "overlap",
                    "halo",
                    "golden",
                    "invariant",
                    "reduction",
                    "partition",
                    "reconstruction",
                    "ownership",
                    "canonical",
                    "kahan",
                ],
            },
            indent=2,
        )
        + "\n",
    )

    _ = golden

    w(
        TASK / "tests" / "test_outputs.py",
        '''import json
import subprocess
from pathlib import Path

import pytest

LAYOUTS = ["pack_1", "pack_2", "pack_4", "pack_8"]
SCENARIOS = ["tape_alpha", "tape_beta", "tape_gamma"]
REDUCTIONS = Path("/output/reductions.json")
OWNERSHIP = Path("/output/ownership.json")
WS_ROOT = Path("/app/ws")
CK_DIR = Path("/app/data/checkpoints")


@pytest.fixture(scope="module", autouse=True)
def rebuild_and_run():
    """Rebuild the runner from sources and emit output artifacts."""
    subprocess.run(
        ["cargo", "build", "--release", "--locked", "--offline"],
        cwd=WS_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "cargo",
            "run",
            "--release",
            "--locked",
            "--offline",
            "-p",
            "m5",
            "--",
            "all-layouts",
            "--out-dir",
            "/output",
        ],
        cwd=WS_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _f64_bits(x: float) -> str:
    # Big-endian IEEE754 hex for finite non-zero fixtures (no opaque hex literals).
    neg = (x < 0.0) or (x == 0.0 and str(x).startswith("-"))
    ax = -x if x < 0.0 else x
    assert ax > 0.0 and ax != float("inf") and ax == ax
    exp = 0
    while ax >= 2.0:
        ax *= 0.5
        exp += 1
    while ax < 1.0:
        ax *= 2.0
        exp -= 1
    frac = ax - 1.0
    mant = 0
    for _ in range(52):
        frac *= 2.0
        bit = 1 if frac >= 1.0 else 0
        mant = (mant << 1) | bit
        if bit:
            frac -= 1.0
    biased = exp + 1023
    assert 0 < biased < 2047
    sign = 1 if neg else 0
    bits = (sign << 63) | (biased << 52) | mant
    return f"{bits:016x}"


def _kahan_sum(values) -> float:
    # For dyadic fixtures, plain left-to-right summation is bit-stable and
    # matches a careful Rust accumulator without depending on FMA quirks.
    total = 0.0
    for v in values:
        total = total + v
    return total


def _canonical_for_scenario(scenario: str) -> dict[str, str]:
    ck = json.loads((CK_DIR / f"{scenario}.json").read_text())
    a, b, wts = ck["a"], ck["b"], ck["w"]
    n = ck["length"]
    ordered = range(n)
    return {
        "sum_w_bits": _f64_bits(_kahan_sum(wts[i] * a[i] for i in ordered)),
        "dot_ab_bits": _f64_bits(_kahan_sum(a[i] * b[i] for i in ordered)),
        "l2_sq_bits": _f64_bits(_kahan_sum(a[i] * a[i] for i in ordered)),
    }


def _load_rows() -> list[dict]:
    assert REDUCTIONS.exists(), "missing reductions.json"
    return json.loads(REDUCTIONS.read_text())


def _index_rows(rows: list[dict]) -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (row["layout"], row["scenario"])
        out[key] = row
    return out


def _expected_overlap_owners(layout: str) -> dict[str, int]:
    ranks = int(layout.split("_")[1])
    chunk = 512 // ranks
    owners: dict[str, int] = {}
    for r in range(ranks - 1):
        owners[str((r + 1) * chunk)] = r
    return owners


def test_reductions_file_exists():
    """reductions.json must be written under /output."""
    assert REDUCTIONS.exists()


def test_ownership_file_exists():
    """ownership.json must be written under /output."""
    assert OWNERSHIP.exists()


def test_reductions_row_schema():
    """Each reductions row must expose layout, scenario, and the three bit columns."""
    for row in _load_rows():
        assert isinstance(row.get("layout"), str)
        assert isinstance(row.get("scenario"), str)
        assert isinstance(row.get("sum_w_bits"), str)
        assert isinstance(row.get("dot_ab_bits"), str)
        assert isinstance(row.get("l2_sq_bits"), str)


def test_all_layout_scenario_pairs_present():
    """Every layout and tape_* checkpoint pair must appear in reductions.json."""
    rows = _index_rows(_load_rows())
    for layout in LAYOUTS:
        for scenario in SCENARIOS:
            assert (layout, scenario) in rows, f"missing {layout}/{scenario}"


def test_only_tape_scenarios_emitted():
    """reductions.json should only include tape_* checkpoint scenarios."""
    for row in _load_rows():
        assert row["scenario"].startswith("tape_"), row["scenario"]


def test_scalars_match_canonical_bits():
    """Scalar bit patterns must match a full-domain index-order reduction of each tape."""
    rows = _index_rows(_load_rows())
    for scenario in SCENARIOS:
        exp = _canonical_for_scenario(scenario)
        for layout in LAYOUTS:
            row = rows[(layout, scenario)]
            assert row["sum_w_bits"] == exp["sum_w_bits"], f"sum_w {layout} {scenario}"
            assert row["dot_ab_bits"] == exp["dot_ab_bits"], f"dot_ab {layout} {scenario}"
            assert row["l2_sq_bits"] == exp["l2_sq_bits"], f"l2_sq {layout} {scenario}"


def test_pack1_matches_canonical():
    """Even the single-rank packing must match the canonical bit patterns."""
    rows = _index_rows(_load_rows())
    for scenario in SCENARIOS:
        exp = _canonical_for_scenario(scenario)
        row = rows[("pack_1", scenario)]
        assert row["sum_w_bits"] == exp["sum_w_bits"]
        assert row["dot_ab_bits"] == exp["dot_ab_bits"]
        assert row["l2_sq_bits"] == exp["l2_sq_bits"]


def test_cross_layout_bit_agreement():
    """All rank packings must agree with each other on every tape scenario."""
    rows = _index_rows(_load_rows())
    for scenario in SCENARIOS:
        ref = rows[("pack_1", scenario)]
        for layout in LAYOUTS[1:]:
            row = rows[(layout, scenario)]
            assert row["sum_w_bits"] == ref["sum_w_bits"]
            assert row["dot_ab_bits"] == ref["dot_ab_bits"]
            assert row["l2_sq_bits"] == ref["l2_sq_bits"]


def test_weighted_sum_uses_stored_weights():
    """sum_w_bits must reflect the on-disk weight lane, not a shifted copy."""
    rows = _index_rows(_load_rows())
    for scenario in SCENARIOS:
        exp = _canonical_for_scenario(scenario)
        for layout in LAYOUTS:
            assert rows[(layout, scenario)]["sum_w_bits"] == exp["sum_w_bits"]


def test_overlap_ownership_map():
    """ownership.json must assign each interior boundary to the lower-numbered rank."""
    owners = json.loads(OWNERSHIP.read_text())
    for layout in LAYOUTS:
        assert layout in owners, f"missing layout {layout} in ownership.json"
        got = owners[layout]
        exp = _expected_overlap_owners(layout)
        assert got == exp, f"ownership mismatch for {layout}"


def test_overlap_stress_not_double_counted():
    """tape_gamma under multi-rank packings must still match the canonical sum_w bits."""
    rows = _index_rows(_load_rows())
    exp = _canonical_for_scenario("tape_gamma")
    for layout in ("pack_2", "pack_4", "pack_8"):
        row = rows[(layout, "tape_gamma")]
        assert row["sum_w_bits"] == exp["sum_w_bits"]
''',
    )

    w(
        TASK / "tests" / "test.sh",
        """#!/bin/bash

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
""",
    )

    solve_parts = ["#!/bin/bash", "set -euo pipefail", ""]
    for rel, body in oracle_files.items():
        solve_parts.append(f"cat > /app/ws/{rel} <<'EOF'")
        solve_parts.append(body.rstrip("\n"))
        solve_parts.append("EOF")
        solve_parts.append("")
    solve_parts.extend(
        [
            # Surgical fixes for tiny-diff sites (avoid whole-file rewrite inflation).
            "python3 - <<'PY'",
            "from pathlib import Path",
            "topo = Path('/app/ws/m9/src/topology.rs')",
            "text = topo.read_text()",
            "text = text.replace('    if ranks > 2 {\\n        segments.reverse();\\n    }\\n', '')",
            "topo.write_text(text)",
            "disp = Path('/app/ws/m5/src/dispatch.rs')",
            "d = disp.read_text()",
            "d = d.replace(",
            "    'let owner = (seg.rank + 1).min(last_rank);\\n                layout_owners.insert(seg.hi.to_string(), owner);',",
            "    'layout_owners.insert(seg.hi.to_string(), seg.rank);',",
            ")",
            "disp.write_text(d)",
            "PY",
            "",
            "cd /app/ws",
            "cargo build --release --locked --offline",
            "/app/ws/target/release/rx-run all-layouts --out-dir /output",
            "",
        ]
    )
    w(TASK / "solution" / "solve.sh", "\n".join(solve_parts))

    w(
        ENV / "ops" / "lab_codec.py",
        """import struct


def f64_bits(v: float) -> str:
    return format(struct.unpack(">Q", struct.pack(">d", v))[0], "016x")
""",
    )

    w(
        ENV / "Dockerfile",
        """# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS builder

WORKDIR /build/ws
COPY ws/Cargo.toml ./
COPY ws/m3/Cargo.toml m3/
COPY ws/m7/Cargo.toml m7/
COPY ws/m9/Cargo.toml m9/
COPY ws/m5/Cargo.toml m5/

COPY ws/m3/src m3/src
COPY ws/m7/src m7/src
COPY ws/m9/src m9/src
COPY ws/m5/src m5/src

RUN cargo generate-lockfile \\
    && cargo build --release --locked \\
    && cargo vendor vendor \\
    && mkdir -p .cargo \\
    && printf '%s\\n' \\
        '[source.crates-io]' \\
        'replace-with = "vendored-sources"' \\
        '' \\
        '[source.vendored-sources]' \\
        'directory = "vendor"' \\
        > .cargo/config.toml

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before COPY layers below.
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
        bash \\
        ca-certificates=20230311+deb12u1 \\
        procps \\
        python3=3.11.2-1+b1 \\
        python3-pip=23.0.1+dfsg-1 \\
        python-is-python3 \\
        build-essential=12.9 \\
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \\
    pytest==8.4.1 \\
    pytest-json-ctrf==0.3.5

COPY --from=builder /usr/local/cargo /usr/local/cargo
COPY --from=builder /usr/local/rustup /usr/local/rustup
ENV RUSTUP_HOME=/usr/local/rustup
ENV CARGO_HOME=/usr/local/cargo
ENV PATH="/usr/local/cargo/bin:${PATH}"
RUN rustup default 1.85.0

COPY --from=builder /build/ws/target/release/rx-run /app/bin/rx-run
COPY --from=builder /build/ws/Cargo.lock /app/ws/Cargo.lock
COPY --from=builder /build/ws/.cargo /app/ws/.cargo
COPY --from=builder /build/ws/vendor /app/ws/vendor
COPY --from=builder /build/ws/target /app/ws/target
COPY ws/ /app/ws/
COPY data/ /app/data/
COPY ops/ /app/ops/

WORKDIR /app/ws

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux kill-session -t _smoke
""",
    )


def main() -> None:
    if TASK.exists():
        # Drop stale distractor checkpoints from earlier drafts.
        ck_dir = ENV / "data" / "checkpoints"
        if ck_dir.exists():
            for p in ck_dir.glob("field_*.json"):
                p.unlink()
    golden = write_data()
    write_rust_sources()
    # Buggy dispatch must also skip non-tape files so NOP ownership/reductions shape is stable;
    # oracle dispatch filters tape_* as well. Apply tape filter to env dispatch now.
    oracle_files = write_oracle_solution_files()
    write_task_meta(golden, oracle_files)
    print(f"generated {TASK}")
    env_files = [p for p in ENV.rglob("*") if p.is_file() and p.name != "Dockerfile"]
    print(f"environment file count (excl Dockerfile): {len(env_files)}")


if __name__ == "__main__":
    main()
