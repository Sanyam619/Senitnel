#!/usr/bin/env bash
set -euo pipefail

ROOT="${Q4_ROOT:-/app}"
ENG="${ROOT}/eng"

python3 - "$ROOT" <<'PY'
"""Derive the generation the registry scores under and file the receipt."""
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
reg = root / "data/quant_registry"


def rows(path):
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("{"):
            out.append(json.loads(line))
    return out


gone = {r["tip"] for r in rows(reg / "retired_tips.jsonl")}
kept = [
    r
    for r in rows(reg / "tip_journal.jsonl")
    if r["state"] == "sealed" and r["kind"] == "grouped" and r["tip"] not in gone
]
best = max(kept, key=lambda r: r["epoch"])

sheet = {}
for line in (root / "data/quant_grids" / best["grid"]).read_text().splitlines():
    cols = line.split()
    if len(cols) == 2:
        sheet[cols[0]] = cols[1]
group = int(sheet["group"])

dims = []
for line in (root / "data/arch/topology.txt").read_text().splitlines():
    cols = line.split()
    if len(cols) == 4 and cols[0] == "layer":
        dims.append((int(cols[1]), int(cols[3])))
dims.sort()
count = sum(d // (group if 0 < group <= d and d % group == 0 else d) for _, d in dims)

(root / "serving").mkdir(parents=True, exist_ok=True)
(root / "serving/bind.accept").write_text(
    "\n".join(
        [
            "# Acceptance receipt for the quantization desk.",
            "pass = scoring",
            f"tip = {best['tip']}",
            f"epoch = {best['epoch']}",
            f"group = {group}",
            f"groups = {count}",
        ]
    )
    + "\n"
)
print(f"receipt: {best['tip']} epoch={best['epoch']} group={group} groups={count}")
PY

cat > "${ENG}/pane/src/tip.rs" <<'RS'
//! Which generation of the quantization registry a pass scores under.

use std::fs;
use std::path::Path;

#[derive(Clone)]
pub struct Row {
    pub name: String,
    pub epoch: i64,
    pub state: String,
    pub kind: String,
    pub grid: String,
    pub bank: String,
}

fn quoted(line: &str, key: &str) -> Option<String> {
    let pat = format!("\"{key}\"");
    let at = line.find(&pat)? + pat.len();
    let rest = &line[at..];
    let open = rest.find('"')? + 1;
    let tail = &rest[open..];
    let close = tail.find('"')?;
    Some(tail[..close].to_string())
}

fn counted(line: &str, key: &str) -> Option<i64> {
    let pat = format!("\"{key}\"");
    let at = line.find(&pat)? + pat.len();
    let rest = line[at..].trim_start().strip_prefix(':')?.trim_start();
    let end = rest
        .find(|c: char| !(c.is_ascii_digit() || c == '-'))
        .unwrap_or(rest.len());
    rest[..end].parse::<i64>().ok()
}

fn lines_of(path: &Path) -> Vec<String> {
    let text = match fs::read_to_string(path) {
        Ok(v) => v,
        Err(e) => panic!("cannot read {}: {e}", path.display()),
    };
    text.lines()
        .map(|l| l.trim().to_string())
        .filter(|l| l.starts_with('{'))
        .collect()
}

/// Every generation the registry journal carries, in file order.
pub fn journal(path: &Path) -> Vec<Row> {
    let mut out = Vec::new();
    for line in lines_of(path) {
        let name = match quoted(&line, "tip") {
            Some(v) => v,
            None => continue,
        };
        out.push(Row {
            name,
            epoch: counted(&line, "epoch").unwrap_or(-1),
            state: quoted(&line, "state").unwrap_or_default(),
            kind: quoted(&line, "kind").unwrap_or_default(),
            grid: quoted(&line, "grid").unwrap_or_default(),
            bank: quoted(&line, "bank").unwrap_or_default(),
        });
    }
    assert!(!out.is_empty(), "registry journal is empty");
    out
}

/// Generations the registry has rolled back.
pub fn rolled(path: &Path) -> Vec<String> {
    let mut out = Vec::new();
    for line in lines_of(path) {
        if let Some(v) = quoted(&line, "tip") {
            out.push(v);
        }
    }
    out
}

/// The generation a scoring pass over the material under `base` runs under.
pub fn settle(base: &Path) -> Row {
    let rows = journal(&base.join("quant_registry/tip_journal.jsonl"));
    let gone = rolled(&base.join("quant_registry/retired_tips.jsonl"));
    pick(&rows, &gone)
}

/// The generation a scoring pass runs under.
pub fn pick(rows: &[Row], gone: &[String]) -> Row {
    let mut best: Option<&Row> = None;
    for row in rows {
        if row.state != "sealed" || row.kind != "grouped" {
            continue;
        }
        if gone.iter().any(|g| g.as_str() == row.name.as_str()) {
            continue;
        }
        if best.is_none() || row.epoch > best.unwrap().epoch {
            best = Some(row);
        }
    }
    match best {
        Some(r) => r.clone(),
        None => panic!("registry names no generation"),
    }
}
RS

cat > "${ENG}/pane/src/seat.rs" <<'RS'
//! The scale sheet a single scenario is quantized under.

use std::path::Path;

use q4_core::load::{Ckpt, Layout};
use q4_knit::gains;

/// Scale sheet bound to one scenario's starting snapshot.
pub fn plate(
    ck: &Ckpt,
    lay: &Layout,
    rows: &[Vec<f64>],
    bank: &Path,
    scales: &Path,
) -> Vec<Vec<f64>> {
    let _ = scales;
    gains::weave(ck, lay, rows, bank)
}
RS

cat > "${ENG}/knit/src/admit.rs" <<'RS'
//! Which calibration shards stand behind a generation, and their rows.

use std::fs;
use std::path::Path;

use q4_core::load::Shard;

pub struct Note {
    pub shard: String,
    pub first: i64,
    pub last: i64,
}

fn pluck(line: &str, key: &str) -> Option<String> {
    let pat = format!("\"{key}\"");
    let at = line.find(&pat)? + pat.len();
    let rest = &line[at..];
    let open = rest.find('"')? + 1;
    let tail = &rest[open..];
    let close = tail.find('"')?;
    Some(tail[..close].to_string())
}

fn dial(line: &str, key: &str) -> Option<i64> {
    let pat = format!("\"{key}\"");
    let at = line.find(&pat)? + pat.len();
    let rest = line[at..].trim_start();
    let rest = rest.strip_prefix(':')?.trim_start();
    let end = rest
        .find(|c: char| !(c.is_ascii_digit() || c == '-'))
        .unwrap_or(rest.len());
    rest[..end].parse::<i64>().ok()
}

/// Every admission note the calibration ledger carries.
pub fn ledger(path: &Path) -> Vec<Note> {
    let text = match fs::read_to_string(path) {
        Ok(v) => v,
        Err(e) => panic!("cannot read {}: {e}", path.display()),
    };
    let mut out = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() || !line.starts_with('{') {
            continue;
        }
        let shard = match pluck(line, "shard") {
            Some(v) => v,
            None => continue,
        };
        out.push(Note {
            shard,
            first: dial(line, "first").unwrap_or(0),
            last: dial(line, "last").unwrap_or(0),
        });
    }
    assert!(!out.is_empty(), "calibration ledger is empty");
    out
}

/// The shard names a pass at `epoch` calibrates over, in name order.
pub fn settled(notes: &[Note], epoch: i64) -> Vec<String> {
    let mut out: Vec<String> = notes
        .iter()
        .filter(|n| n.first <= epoch && epoch <= n.last)
        .map(|n| n.shard.clone())
        .collect();
    out.sort();
    out.dedup();
    out
}

/// (names, rows) of the calibration material behind a pass at `epoch`.
pub fn gather(base: &Path, epoch: i64, width: usize) -> (Vec<String>, Vec<Vec<f64>>) {
    let notes = ledger(&base.join("calib/admit_ledger.jsonl"));
    let names = settled(&notes, epoch);
    let mut rows = Vec::new();
    for name in &names {
        let shard = Shard::read(&base.join("calib").join(format!("{name}.txt")), width);
        rows.extend(shard.rows);
    }
    assert!(!rows.is_empty(), "no calibration rows behind this generation");
    (names, rows)
}
RS

cat > "${ENG}/knit/src/gains.rs" <<'RS'
//! Per-input-channel scale sheet used by the four-bit round trip.

use std::path::Path;

use q4_core::load::{Ckpt, Layout};
use q4_core::wire;

/// The scale sheet a pass over `rows` binds to.
pub fn weave(ck: &Ckpt, lay: &Layout, rows: &[Vec<f64>], bank: &Path) -> Vec<Vec<f64>> {
    let _ = bank;
    let depth = lay.depth();
    let mut total: Vec<Vec<f64>> = (0..depth).map(|at| vec![0.0f64; lay.inn[at]]).collect();
    for row in rows {
        let seen = wire::seen(ck, lay, row);
        for at in 0..depth {
            for i in 0..lay.inn[at] {
                total[at][i] += seen[at][i].abs();
            }
        }
    }
    let n = rows.len() as f64;
    let mut out = Vec::with_capacity(depth);
    for at in 0..depth {
        let d = lay.inn[at];
        let mut g = Vec::with_capacity(d);
        for i in 0..d {
            g.push((total[at][i] / n + lay.eps).sqrt());
        }
        let mut s = 0.0f64;
        for v in &g {
            s += *v;
        }
        let mid = s / d as f64;
        out.push(g.iter().map(|v| v / mid).collect());
    }
    out
}
RS

cat > "${ENG}/core/src/fold.rs" <<'RS'
//! Four-bit weight round trip.

/// Extent of one group inside a run of `len` entries.
pub fn span(group: usize, len: usize) -> usize {
    if group == 0 || group > len || len % group != 0 {
        len
    } else {
        group
    }
}

fn step_of(top: f64) -> f64 {
    if top > 0.0 {
        top / 7.0
    } else {
        1.0
    }
}

fn clamp(q: f64) -> f64 {
    if q > 7.0 {
        7.0
    } else if q < -8.0 {
        -8.0
    } else {
        q
    }
}

/// Round trip of one layer's weights under per-input-channel `gain`.
pub fn pack(w: &[Vec<f64>], gain: &[f64], group: usize) -> Vec<Vec<f64>> {
    let rows = w.len();
    let cols = w[0].len();
    let ext = span(group, cols);
    let mut out = vec![vec![0.0f64; cols]; rows];
    for o in 0..rows {
        let mut head = 0usize;
        while head < cols {
            let mut top = 0.0f64;
            for i in head..head + ext {
                let v = (w[o][i] * gain[i]).abs();
                if v > top {
                    top = v;
                }
            }
            let step = step_of(top);
            for i in head..head + ext {
                let q = clamp((w[o][i] * gain[i] / step).round());
                out[o][i] = q * step / gain[i];
            }
            head += ext;
        }
    }
    out
}
RS

"${ROOT}/scripts/run_int4_eval.sh"
