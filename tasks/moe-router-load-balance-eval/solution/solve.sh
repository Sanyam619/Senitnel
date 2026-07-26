#!/bin/bash
# Oracle seating for the MoE evaluation desk.
# Binds the desk out of trial mode against the journal-resolved durable tip,
# rewrites tip resolution, hold windows, capacity mixing, metric scoring, and
# the deep eval gate, then rebuilds and emits the report.
set -euo pipefail

test -d /app/eng
test -d /app/calib
test -d /app/seat
test -d /app/flag
test -d /app/mix
test -d /app/score
test -d /app/gate
test -d /app/data/routers
test -d /app/data/eval
mkdir -p /output

# Move evaluation selection to serving and bind the selected durable tip so
# engine builds stop refreshing the seating surfaces from the desk seed set.
python3 - <<'PY'
import json
from pathlib import Path

retired = set()
for line in Path("/app/data/routers/retired_tips.jsonl").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line:
        continue
    retired.add(json.loads(line)["tip"])

best = None
for line in Path("/app/data/routers/tip_journal.jsonl").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line:
        continue
    row = json.loads(line)
    if not row.get("sealed"):
        continue
    if row["tip"] in retired:
        continue
    if best is None or row["epoch"] >= best["epoch"]:
        best = row

Path("/app/calib").mkdir(parents=True, exist_ok=True)
Path("/app/calib/trial_pref.toml").write_text(
    '[evaluation]\nselection = "serving"\n', encoding="utf-8"
)
Path("/app/calib/tip_bind.accept").write_text(
    f"tip = {best['tip']}\nepoch = {best['epoch']}\ntemp = {best['tip_temp']}\n",
    encoding="utf-8",
)
PY

cat > /app/seat/knit_b.rs <<'EOF'
use crate::base::{read_journal, read_retired};
use std::path::Path;

pub fn pick_t(a: &str, b: &str, c: &str) -> (f64, i64) {
    let _ = (b, c);
    let journal = Path::new(a);
    let retired_path = journal
        .parent()
        .map(|p| p.join("retired_tips.jsonl"))
        .unwrap_or_else(|| Path::new("retired_tips.jsonl").to_path_buf());
    let retired = read_retired(&retired_path);
    let rows = read_journal(journal);
    let mut best = (1.0_f64, 0_i64);
    let mut found = false;
    for row in rows {
        if !row.sealed {
            continue;
        }
        if retired.iter().any(|t| t == &row.tip) {
            continue;
        }
        if !found || row.epoch >= best.1 {
            best = (row.tip_temp, row.epoch);
            found = true;
        }
    }
    best
}
EOF

cat > /app/flag/xv_c.rs <<'EOF'
pub fn bit_z(a: &[String], b: &[(String, String, i64)], ids: &[String], g: i64) -> Vec<bool> {
    let _ = a;
    ids.iter()
        .map(|id| {
            let mut held = false;
            let mut at = i64::MIN;
            for (rid, op, ep) in b {
                if rid == id && *ep <= g && *ep >= at {
                    at = *ep;
                    held = op == "hold";
                }
            }
            !held
        })
        .collect()
}
EOF

cat > /app/mix/ward_d.rs <<'EOF'
pub fn mix_w(raw: &[f64], caps: &[f64], flags: &[bool], scale: f64) -> Vec<f64> {
    let n = raw.len().min(flags.len());
    if n == 0 {
        return Vec::new();
    }
    let s = if scale.abs() < 1e-12 { 1.0 } else { scale };
    let mut scaled = Vec::with_capacity(n);
    for i in 0..n {
        scaled.push(raw[i] / s);
    }
    let mx = scaled.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let mut ex = Vec::with_capacity(n);
    let mut total = 0.0;
    for v in &scaled {
        let e = (v - mx).exp();
        ex.push(e);
        total += e;
    }
    if total <= 0.0 {
        total = 1.0;
    }
    let mut out = Vec::with_capacity(n);
    let mut mass = 0.0;
    for i in 0..n {
        let c = caps.get(i).copied().unwrap_or(1.0);
        let p = if flags[i] { c * ex[i] / total } else { 0.0 };
        out.push(p);
        mass += p;
    }
    if mass <= 1e-15 {
        let active = flags.iter().filter(|f| **f).count().max(1) as f64;
        return flags
            .iter()
            .map(|f| if *f { 1.0 / active } else { 0.0 })
            .collect();
    }
    for v in out.iter_mut() {
        *v /= mass;
    }
    out
}
EOF

cat > /app/score/helm_e.rs <<'EOF'
pub fn score_u(weights: &[f64], scale: f64) -> (f64, f64) {
    let _ = scale;
    let mut ent = 0.0;
    for w in weights {
        if *w > 1e-15 {
            ent -= *w * w.ln();
        }
    }
    (ent.exp(), ent)
}
EOF

cat > /app/gate/emit_f.rs <<'EOF'
pub fn gate_y(shares: &[f64], flags: &[bool], rows_ok: bool) -> bool {
    if shares.len() != flags.len() || shares.is_empty() {
        return false;
    }
    let mut active_sum = 0.0;
    for (share, flag) in shares.iter().zip(flags.iter()) {
        if *flag {
            if *share < 0.0 {
                return false;
            }
            active_sum += *share;
        } else if share.abs() > 1e-9 {
            return false;
        }
    }
    rows_ok && (active_sum - 1.0).abs() <= 1e-6
}
EOF

bash /app/scripts/run_moe_eval.sh
