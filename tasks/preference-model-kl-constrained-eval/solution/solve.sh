#!/bin/bash
# Oracle seating for the preference-alignment evaluation desk.
# Binds the desk out of trial mode against the journal-resolved durable tip,
# rewrites tip resolution, beta seating, soft win scoring, KL scoring, and
# the deep eval gate, then rebuilds and emits the report.
set -euo pipefail

test -d /app/eng
test -d /app/calib
test -d /app/seat
test -d /app/flag
test -d /app/mix
test -d /app/score
test -d /app/gate
test -d /app/data/tips
test -d /app/data/prefs
mkdir -p /output

python3 - <<'PY'
import json
from pathlib import Path

retired = set()
for line in Path("/app/data/tips/retired_tips.jsonl").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line:
        continue
    retired.add(json.loads(line)["tip"])

best = None
for line in Path("/app/data/tips/tip_journal.jsonl").read_text(encoding="utf-8").splitlines():
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
    f"tip = {best['tip']}\nepoch = {best['epoch']}\nbeta = {best['beta']}\n",
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
            best = (row.beta, row.epoch);
            found = true;
        }
    }
    best
}
EOF

cat > /app/flag/xv_c.rs <<'EOF'
pub fn bit_z(live_beta: f64, tip_beta: f64, live_path: &str) -> f64 {
    let _ = (live_beta, live_path);
    tip_beta
}
EOF

cat > /app/mix/ward_d.rs <<'EOF'
pub fn mix_w(margins: &[f64], scale: f64) -> f64 {
    if margins.is_empty() {
        return 0.0;
    }
    let s = if scale.abs() < 1e-12 { 1e-12 } else { scale };
    let mut acc = 0.0;
    for m in margins {
        let x = s * *m;
        let p = if x >= 0.0 {
            let z = (-x).exp();
            1.0 / (1.0 + z)
        } else {
            let z = x.exp();
            z / (1.0 + z)
        };
        acc += p;
    }
    acc / (margins.len() as f64)
}
EOF

cat > /app/score/helm_e.rs <<'EOF'
pub fn score_u(cand: &[Vec<f64>], reference: &[Vec<f64>]) -> f64 {
    let n = cand.len().min(reference.len());
    if n == 0 {
        return 0.0;
    }
    let mut total = 0.0;
    for i in 0..n {
        let pc = &cand[i];
        let pr = &reference[i];
        let m = pc.len().min(pr.len());
        let mut row = 0.0;
        for j in 0..m {
            let a = pc[j].max(1e-15);
            let b = pr[j].max(1e-15);
            row += a * (a / b).ln();
        }
        total += row;
    }
    total / (n as f64)
}
EOF

cat > /app/gate/emit_f.rs <<'EOF'
pub fn gate_y(wins: &[f64], kls: &[f64], betas: &[f64], epochs: &[i64], rows_ok: bool) -> bool {
    if wins.is_empty() || wins.len() != kls.len() || wins.len() != betas.len() || wins.len() != epochs.len()
    {
        return false;
    }
    rows_ok
}
EOF

bash /app/scripts/run_pref_eval.sh
