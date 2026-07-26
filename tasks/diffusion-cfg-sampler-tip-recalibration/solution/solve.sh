#!/bin/bash
set -euo pipefail

# Oracle: publishable evaluation selection + tip bind, then repair seating
# surfaces the build gate rematerializes, then emit through the entrypoint.

cat > /app/calib/trial_pref.toml <<'EOF'
# Evaluation selection for the diffusion desk.

[evaluation]
selection = "serving"
refresh = "auto"

[desk]
owner = "diff-eval-rotation"
window = "weekly"
EOF

printf 'tip_g7\n' > /app/calib/tip_bind.accept

cat > /app/eng/core/src/lens.rs <<'EOF'
use crate::base::{rd_f32, rd_rowf, rd_u32};

pub fn lens_unfold(blob: &[u8]) -> Vec<Vec<f32>> {
    if blob.len() < 12 {
        return Vec::new();
    }
    let magic = &blob[0..4];
    let mut off = 4usize;
    let n = rd_u32(blob, &mut off) as usize;
    let dim = rd_u32(blob, &mut off) as usize;
    if magic == b"CKP1" {
        off += 2 * n;
        let mut out = Vec::with_capacity(n);
        for _ in 0..n {
            out.push(rd_rowf(blob, &mut off, dim));
        }
        out
    } else if magic == b"CKP2" {
        let block = rd_u32(blob, &mut off) as usize;
        off += 2 * n;
        let mut out = Vec::with_capacity(n);
        let mut done = 0usize;
        while done < n && block > 0 {
            let coef = rd_f32(blob, &mut off);
            let take = block.min(n - done);
            for _ in 0..take {
                let mut row = rd_rowf(blob, &mut off, dim);
                for v in row.iter_mut() {
                    *v *= coef;
                }
                out.push(row);
            }
            done += take;
        }
        out
    } else {
        Vec::new()
    }
}
EOF

cat > /app/eng/rank/src/knot.rs <<'EOF'
use std::collections::HashSet;
use std::path::Path;

use bevel_core::base::Mark;

pub fn knot_r(marks: &[Mark], retired: &HashSet<String>) -> u32 {
    let mut top = 0u32;
    for m in marks {
        if m.state == "durable" && !retired.contains(&m.tip) && m.idx > top {
            top = m.idx;
        }
    }
    top
}

pub fn read_retired(path: &Path) -> HashSet<String> {
    let text = std::fs::read_to_string(path).unwrap_or_default();
    let mut out = HashSet::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        if let Some(i) = line.find("\"tip\"") {
            let rest = &line[i + 5..];
            let rest = rest.trim_start().trim_start_matches(':').trim_start();
            if let Some(rest) = rest.strip_prefix('"') {
                if let Some(end) = rest.find('"') {
                    out.insert(rest[..end].to_string());
                }
            }
        }
    }
    out
}
EOF

cat > /app/eng/rank/src/facet.rs <<'EOF'
use bevel_core::base::read_marks;
use std::path::Path;

pub struct SheetRow {
    pub cfg: f64,
    pub sampler: String,
}

pub fn facet_q(idx: u32, root: &Path) -> SheetRow {
    let marks = read_marks(&root.join("feature_registry/tip_journal.jsonl"));
    let fam = marks
        .iter()
        .find(|m| m.idx == idx)
        .map(|m| m.sheet.clone())
        .unwrap_or_default();
    let table = root.join("sched").join(format!("table_{fam}.toml"));
    row_of(&table, idx)
}

fn row_of(path: &Path, idx: u32) -> SheetRow {
    let text = std::fs::read_to_string(path).unwrap_or_default();
    let key = format!("\"{idx}\"");
    let mut cfg = 0.0f64;
    let mut sampler = String::new();
    let mut section = "";
    for line in text.lines() {
        let line = line.trim();
        if line == "[cfg]" {
            section = "cfg";
            continue;
        }
        if line == "[sampler]" {
            section = "sampler";
            continue;
        }
        if let Some(rest) = line.strip_prefix(&key) {
            let rest = rest.trim_start();
            if let Some(rest) = rest.strip_prefix('=') {
                let rest = rest.trim();
                if section == "cfg" {
                    if let Ok(v) = rest.parse::<f64>() {
                        cfg = v;
                    }
                } else if section == "sampler" {
                    sampler = rest.trim_matches('"').to_string();
                }
            }
        }
    }
    SheetRow { cfg, sampler }
}
EOF

cat > /app/eng/core/src/weave.rs <<'EOF'
use std::collections::HashSet;

use crate::base::{fold_all, Lot, Mark};

pub fn weave_m(marks: &[Mark], lots: &[Lot], retired: &HashSet<String>) -> Vec<Lot> {
    let Some(tip) = marks
        .iter()
        .filter(|m| m.state == "durable" && !retired.contains(&m.tip) && !m.weft_c.is_empty())
        .max_by_key(|m| m.idx)
    else {
        return Vec::new();
    };
    let pick = |names: &[String], label: &str| -> Lot {
        let sel: Vec<Lot> = names
            .iter()
            .filter_map(|n| lots.iter().find(|l| &l.name == n).cloned())
            .collect();
        fold_all(&sel, label)
    };
    vec![pick(&tip.weft_c, "c"), pick(&tip.weft_d, "d")]
}
EOF

/app/scripts/run_diff_eval.sh

head -c 200 /output/diff-eval.json || true
echo
