#!/usr/bin/env bash
set -euo pipefail

app_dir=/app
eng_dir="$app_dir/eng"

# ---------------------------------------------------------------------------
# 1. Resolve the generation the desk should be scoring under: the highest
#    sealed generation in the registry that has not been withdrawn.
# ---------------------------------------------------------------------------
read -r BOUND_TIP BOUND_GEN <<EOF
$(python3 - "$app_dir" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
reg = root / "data" / "decoder_registry"
gone = set()
for line in (reg / "retired_tips.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        gone.add(json.loads(line)["tip"])
rows = []
for line in (reg / "tip_journal.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        rows.append(json.loads(line))
live = [r for r in rows if r["state"] == "sealed" and r["tip"] not in gone]
best = max(live, key=lambda r: r["idx"])
print(best["tip"], best["idx"])
PY
)
EOF

# ---------------------------------------------------------------------------
# 2. Record the scoring pass and the resolved generation so the workspace stops
#    restoring its seed seating on rebuild.
# ---------------------------------------------------------------------------
cat > "$app_dir/calib/eval_pass.toml" <<'EOF'
# Which pass the evaluation desk is running.
#   rehearsal - warm-up sweeps, published numbers are not claimed
#   scoring   - the pass whose numbers are published against the bands
[evaluation]
pass = "scoring"
report = "bands"
EOF

cat > "$app_dir/calib/decoder_selection.txt" <<EOF
# Decoder registry generation this workspace is seated against.
# Written by whoever last moved the desk; read on every workspace rebuild.
selected_tip = $BOUND_TIP
selected_generation = $BOUND_GEN
EOF

# ---------------------------------------------------------------------------
# 3. Bind the registry generation instead of the newest journal row: only
#    sealed rows are eligible, and withdrawn ones drop out.
# ---------------------------------------------------------------------------
cat > "$eng_dir/rank/src/epoch.rs" <<'EOF'
use std::collections::HashSet;
use std::fs;
use std::path::Path;

pub struct Row {
    pub at: u32,
    pub state: String,
    pub name: String,
    pub sheet: String,
    pub route: String,
}

fn text_of(row: &str, key: &str) -> String {
    let needle = format!("\"{key}\"");
    let Some(head) = row.find(&needle) else {
        return String::new();
    };
    let rest = row[head + needle.len()..].trim_start();
    let Some(rest) = rest.strip_prefix(':') else {
        return String::new();
    };
    let rest = rest.trim_start();
    match rest.strip_prefix('"') {
        Some(tail) => tail
            .find('"')
            .map(|end| tail[..end].to_string())
            .unwrap_or_default(),
        None => {
            let end = rest
                .find(|c: char| !c.is_ascii_digit())
                .unwrap_or(rest.len());
            rest[..end].to_string()
        }
    }
}

pub fn rows(root: &Path) -> Vec<Row> {
    let text = fs::read_to_string(root.join("data/decoder_registry/tip_journal.jsonl"))
        .expect("registry journal");
    text.lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| Row {
            at: text_of(l, "idx").parse().unwrap_or(0),
            state: text_of(l, "state"),
            name: text_of(l, "tip"),
            sheet: text_of(l, "sheet"),
            route: text_of(l, "mode"),
        })
        .collect()
}

pub fn out_set(root: &Path) -> HashSet<String> {
    fs::read_to_string(root.join("data/decoder_registry/retired_tips.jsonl"))
        .unwrap_or_default()
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| text_of(l, "tip"))
        .collect()
}

/// Returns the generation index the desk binds for this run.
pub fn pick_e(rows: &[Row], out: &HashSet<String>) -> u32 {
    let mut held: Option<u32> = None;
    for row in rows.iter() {
        if row.state != "sealed" {
            continue;
        }
        if out.contains(&row.name) {
            continue;
        }
        held = match held {
            Some(prev) if prev >= row.at => Some(prev),
            _ => Some(row.at),
        };
    }
    held.expect("no eligible generation in the registry")
}
EOF

# ---------------------------------------------------------------------------
# 4. Resolve the fusion weight by generation on the generation's own sheet
#    rather than taking the widest row the sheet happens to carry.
# ---------------------------------------------------------------------------
cat > "$eng_dir/rank/src/fuse.rs" <<'EOF'
use std::fs;
use std::path::Path;

fn pairs(root: &Path, sheet: &str) -> Vec<(u32, f64)> {
    let path = root.join(format!("data/fusion/table_{sheet}.toml"));
    let text = fs::read_to_string(&path).unwrap_or_else(|e| panic!("{}: {e}", path.display()));
    let mut out = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let Some((key, val)) = line.split_once('=') else {
            continue;
        };
        let key = key.trim().trim_matches('"');
        let Ok(at) = key.parse::<u32>() else {
            continue;
        };
        let Ok(v) = val.trim().parse::<f64>() else {
            continue;
        };
        out.push((at, v));
    }
    out
}

/// Returns the fusion weight the bound generation resolves on its sheet.
pub fn row_w(sheet: &str, n: u32, root: &Path) -> f64 {
    let table = pairs(root, sheet);
    for (at, v) in table.iter() {
        if *at == n {
            return *v;
        }
    }
    panic!("sheet {sheet} has no row for generation {n}");
}
EOF

# ---------------------------------------------------------------------------
# 5. Merge along the frame path first and only then drop the null unit, so a
#    unit held across adjacent frames stays one emission and a unit that
#    genuinely repeats across a null frame stays two.
# ---------------------------------------------------------------------------
cat > "$eng_dir/core/src/collapse.rs" <<'EOF'
/// Frame-synchronous greedy search over the fused per-frame scores.
///
/// `a` holds the per-frame unit scores, `b` the conditioning table, `w` the
/// fusion weight. Unit 0 is the null unit.
pub fn fold_c(a: &[Vec<f32>], b: &[Vec<f32>], w: f64) -> Vec<usize> {
    let mut out: Vec<usize> = Vec::new();
    let mut last = 0usize;
    let mut prev = usize::MAX;
    for row in a.iter() {
        let mut best = 0usize;
        let mut best_s = f64::NEG_INFINITY;
        let mut seen = false;
        for (v, cellv) in row.iter().enumerate() {
            let mut s = *cellv as f64;
            if v != 0 {
                s += w * b[last][v] as f64;
            }
            if !seen || s > best_s {
                best_s = s;
                best = v;
                seen = true;
            }
        }
        if best != prev && best != 0 {
            out.push(best);
        }
        if best != 0 {
            last = best;
        }
        prev = best;
    }
    out
}
EOF

# ---------------------------------------------------------------------------
# 6. Condition the joined path on the prediction state and let a frame emit
#    more than once before it advances.
# ---------------------------------------------------------------------------
cat > "$eng_dir/core/src/join.rs" <<'EOF'
/// Greedy search for the joined path.
///
/// `a` holds the per-frame unit scores, `b` the conditioning table, `c` the
/// prediction-state table, `w` the fusion weight. Unit 0 is the null unit.
pub fn step_j(a: &[Vec<f32>], b: &[Vec<f32>], c: &[Vec<f32>], w: f64) -> Vec<usize> {
    let mut out: Vec<usize> = Vec::new();
    let mut last = 0usize;
    let mut t = 0usize;
    while t < a.len() {
        let row = &a[t];
        let mut emitted = 0usize;
        loop {
            let mut best = 0usize;
            let mut best_s = f64::NEG_INFINITY;
            let mut seen = false;
            for (v, cellv) in row.iter().enumerate() {
                let mut s = *cellv as f64;
                if v != 0 {
                    s += w * b[last][v] as f64;
                    s += c[last][v] as f64;
                }
                if !seen || s > best_s {
                    best_s = s;
                    best = v;
                    seen = true;
                }
            }
            if best == 0 || emitted >= 2 {
                t += 1;
                break;
            }
            out.push(best);
            last = best;
            emitted += 1;
        }
    }
    out
}
EOF

# ---------------------------------------------------------------------------
# 7. Publish.
# ---------------------------------------------------------------------------
bash "$app_dir/scripts/run_asr_eval.sh"
