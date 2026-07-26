#!/usr/bin/env bash
set -euo pipefail

app_dir=/app

read -r BOUND_TIP BOUND_EPOCH BOUND_KEPT <<EOF
$(python3 - "$app_dir" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
reg = root / "data" / "mask_registry"
gone = set()
for line in (reg / "retired_tips.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        gone.add(json.loads(line)["tip"])
rows = []
for line in (reg / "tip_journal.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        rows.append(json.loads(line))
live = []
for r in rows:
    if r["state"] != "durable" or r["tip"] in gone:
        continue
    sheet = root / "data" / "masks" / r["sheet"]
    kind = ""
    for line in sheet.read_text(encoding="utf-8").splitlines():
        cells = line.split()
        if len(cells) >= 2 and cells[0] == "kind":
            kind = cells[1]
            break
    if kind != "structured":
        continue
    live.append(r)
best = max(live, key=lambda r: r["epoch"])
kept = 0
for line in (root / "data" / "masks" / best["sheet"]).read_text(encoding="utf-8").splitlines():
    cells = line.split()
    if len(cells) > 2 and cells[0] == "keep":
        kept += len(cells) - 2
print(best["tip"], best["epoch"], kept)
PY
)
EOF


cat > "$app_dir/serving/bind.accept" <<EOF
# Channel registry generation this workspace is bound to.
# Written by whoever last moved the desk; read on every workspace rebuild.
desk_pass = scoring
bound_tip = $BOUND_TIP
bound_epoch = $BOUND_EPOCH
kept_channels = $BOUND_KEPT
EOF

python3 - <<'PY'
from pathlib import Path
path = Path("/app/eng/core/src/draw.rs")
text = path.read_text(encoding="utf-8")
old = """            for pos in 0..cols.len() {
                acc += hw[pos] * sample[pos];"""
new = """            for (pos, &j) in cols.iter().enumerate() {
                acc += hw[j] * sample[pos];"""
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("draw body moved")
path.write_text(text, encoding="utf-8")
PY

python3 - <<'PY'
from pathlib import Path
path = Path("/app/eng/meld/src/head.rs")
text = path.read_text(encoding="utf-8")
old = """            ck.anchor_spread[c]
        } else {"""
new = """            ck.anchor_spread[c] / seen
        } else {"""
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("head body moved")
path.write_text(text, encoding="utf-8")
PY

# Statistics on the surviving stack.
cat > "$app_dir/eng/meld/src/lib.rs" <<'RS'
//! Per-channel statistics the stack is re-fitted with before it is scored.

pub mod head;

use prune_core::draw;
use prune_core::load::{Ckpt, Topology};
use prune_core::moments;

/// Per-block, per-surviving-channel statistics the stack normalises with.
pub struct Norms {
    pub mid: Vec<Vec<f64>>,
    pub spread: Vec<Vec<f64>>,
}

impl Norms {
    /// Statistics measured over `batch` for the channel selection `keep`.
    pub fn fit(ck: &Ckpt, topo: &Topology, keep: &[Vec<usize>], batch: &[Vec<f64>]) -> Norms {
        let mut carry: Vec<Vec<f64>> = batch.to_vec();
        let mut cols: Vec<usize> = (0..topo.width()).collect();
        let mut mid = Vec::with_capacity(topo.depth());
        let mut spread = Vec::with_capacity(topo.depth());

        for at in 0..topo.depth() {
            let rows = &keep[at];
            let pre = draw::lift(ck, at, rows, &cols, &carry);
            let (m, s) = moments(&pre);
            carry = draw::fire(ck, at, rows, &pre, &m, &s, topo.eps);
            cols = rows.clone();
            mid.push(m);
            spread.push(s);
        }

        Norms { mid, spread }
    }
}

/// Forward the surviving stack under `norms` and return the class responses of
/// every row.
pub fn drive(
    ck: &Ckpt,
    topo: &Topology,
    keep: &[Vec<usize>],
    norms: &Norms,
    batch: &[Vec<f64>],
) -> Vec<Vec<f64>> {
    let mut carry: Vec<Vec<f64>> = batch.to_vec();
    let mut cols: Vec<usize> = (0..topo.width()).collect();
    for at in 0..topo.depth() {
        let rows = &keep[at];
        let pre = draw::lift(ck, at, rows, &cols, &carry);
        carry = draw::fire(ck, at, rows, &pre, &norms.mid[at], &norms.spread[at], topo.eps);
        cols = rows.clone();
    }
    draw::tally(ck, topo.classes, &carry, &cols)
}
RS

# Durable structured registry resolution.
cat > "$app_dir/eng/lane/src/tip.rs" <<'RS'
//! Which generation of the channel registry the desk scores under.

use std::fs;
use std::path::Path;

pub struct Row {
    pub epoch: i64,
    pub state: String,
    pub tip: String,
    pub sheet: String,
}

pub struct Bound {
    pub tip: String,
    pub epoch: i64,
    pub sheet: String,
}

fn text_at(row: &str, key: &str) -> String {
    let stamp = format!("\"{key}\"");
    let Some(head) = row.find(&stamp) else {
        return String::new();
    };
    let rest = row[head + stamp.len()..].trim_start();
    let Some(rest) = rest.strip_prefix(':') else {
        return String::new();
    };
    let rest = rest.trim_start();
    if let Some(tail) = rest.strip_prefix('"') {
        match tail.find('"') {
            Some(end) => tail[..end].to_string(),
            None => String::new(),
        }
    } else {
        let end = rest
            .find(|c: char| !(c.is_ascii_digit() || c == '-'))
            .unwrap_or(rest.len());
        rest[..end].to_string()
    }
}

pub fn journal(root: &Path) -> Vec<Row> {
    let text = fs::read_to_string(root.join("data/mask_registry/tip_journal.jsonl"))
        .unwrap_or_else(|e| panic!("cannot read the channel registry: {e}"));
    let mut out = Vec::new();
    for line in text.lines() {
        if line.trim().is_empty() {
            continue;
        }
        out.push(Row {
            epoch: text_at(line, "epoch").parse::<i64>().unwrap_or(-1),
            state: text_at(line, "state"),
            tip: text_at(line, "tip"),
            sheet: text_at(line, "sheet"),
        });
    }
    out
}

pub fn shelved(root: &Path) -> Vec<String> {
    let text = fs::read_to_string(root.join("data/mask_registry/retired_tips.jsonl"))
        .unwrap_or_default();
    text.lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| text_at(l, "tip"))
        .collect()
}

fn sheet_kind(root: &Path, sheet: &str) -> String {
    let text = fs::read_to_string(root.join("data/masks").join(sheet)).unwrap_or_default();
    for line in text.lines() {
        let cells: Vec<&str> = line.split_whitespace().collect();
        if cells.len() >= 2 && cells[0] == "kind" {
            return cells[1].to_string();
        }
    }
    String::new()
}

/// The generation every published number is scored under.
pub fn settled(root: &Path) -> Bound {
    let gone = shelved(root);
    let mut held: Option<Bound> = None;
    for row in journal(root) {
        if row.state != "durable" || gone.iter().any(|g| g == &row.tip) {
            continue;
        }
        if sheet_kind(root, &row.sheet) != "structured" {
            continue;
        }
        let ahead = match &held {
            Some(cur) => row.epoch > cur.epoch,
            None => true,
        };
        if ahead {
            held = Some(Bound {
                tip: row.tip,
                epoch: row.epoch,
                sheet: row.sheet,
            });
        }
    }
    held.expect("the channel registry carries no usable generation")
}

/// The registry row for a named generation.
pub fn named(root: &Path, tip: &str) -> Bound {
    for row in journal(root) {
        if row.tip == tip {
            return Bound {
                tip: row.tip,
                epoch: row.epoch,
                sheet: row.sheet,
            };
        }
    }
    panic!("the channel registry has no generation named {tip}");
}
RS

# Bound roster seating across all slice domains.
cat > "$app_dir/eng/lane/src/seat.rs" <<'RS'
//! One published scenario: which frozen snapshot it starts from, which channel
//! roster it survives on, which rows it is re-fitted over, and the numbers it
//! reports.

use std::path::Path;

use prune_core::load::{Bank, Ckpt, Panel, Sheet, Topology};
use prune_core::{agreement, span, verdict};
use prune_meld::head;
use prune_meld::{drive, Norms};

use crate::tip::Bound;
use crate::Cell;

fn start_ckpt(root: &Path, topo: &Topology, start: &str) -> Ckpt {
    let file = if start == "resume" {
        "resume.ckpt"
    } else {
        "cold.ckpt"
    };
    Ckpt::read(&root.join("data/dense").join(file), topo)
}

pub fn run(root: &Path, topo: &Topology, bound: &Bound, id: &str, panel: &str, start: &str) -> Cell {
    let panel = Panel::read(
        &root.join("data/eval").join(format!("{panel}.txt")),
        topo.width(),
        topo.classes,
    );
    let ck = start_ckpt(root, topo, start);

    let sheet = Sheet::read(&root.join("data/masks").join(&bound.sheet), topo);

    let mut batch: Vec<Vec<f64>> = Vec::new();
    for dom in panel.domains.iter() {
        let bank = Bank::read(
            &root.join("data/calib").join(format!("shard_{dom}.txt")),
            topo.width(),
        );
        batch.extend(bank.rows);
    }

    let norms = Norms::fit(&ck, topo, &sheet.keep, &batch);

    let affine = head::refit(
        &ck,
        topo.classes,
        &drive(&ck, topo, &sheet.keep, &norms, &batch),
    );
    let logits = drive(&ck, topo, &sheet.keep, &norms, &panel.rows);
    let extent = span::budget(topo, &sheet.keep);

    Cell {
        id: id.to_string(),
        accuracy: agreement(&verdict(&logits, &affine), &panel.marks),
        dropped: extent.dropped,
        kept: extent.kept,
        epoch: sheet.epoch,
    }
}
RS

bash "$app_dir/scripts/run_prune_eval.sh"
