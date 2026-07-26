#!/bin/bash
# Oracle seating for the forecasting backtest leakage evaluation.
# Binds evaluation out of trial mode against the registry-resolved durable
# tip, rewrites tip resolution, scaler labeling, causal smape/mase seating,
# and the deep eval gate, then rebuilds and emits the report.
set -euo pipefail

test -d /app/eng
test -d /app/calib
test -d /app/seat
test -d /app/flag
test -d /app/mix
test -d /app/score
test -d /app/gate
test -d /app/data/feature_registry
test -d /app/data/series
mkdir -p /output

python3 - <<'PY'
import json
from pathlib import Path

retired = set()
for line in Path("/app/data/feature_registry/retired_tips.jsonl").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line:
        continue
    retired.add(json.loads(line)["tip"])

best = None
for line in Path("/app/data/feature_registry/tip_journal.jsonl").read_text(encoding="utf-8").splitlines():
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
    f"tip = {best['tip']}\nepoch = {best['epoch']}\nscaler = {best['scaler']}\n",
    encoding="utf-8",
)
PY

cat > /app/seat/knit_b.rs <<'EOF'
use crate::base::read_journal;
use crate::base::read_retired;
use crate::base::TipPick;
use std::path::Path;

pub fn pick_t(a: &str, b: &str, c: &str) -> TipPick {
    let _ = c;
    let journal = Path::new(a);
    let retired_path = if b.is_empty() {
        journal
            .parent()
            .map(|p| p.join("retired_tips.jsonl"))
            .unwrap_or_else(|| Path::new("retired_tips.jsonl").to_path_buf())
    } else {
        Path::new(b).to_path_buf()
    };
    let retired = read_retired(&retired_path);
    let rows = read_journal(journal);
    let mut best: Option<TipPick> = None;
    for row in rows {
        if !row.sealed {
            continue;
        }
        if retired.iter().any(|t| t == &row.tip) {
            continue;
        }
        let cand = TipPick {
            tip: row.tip,
            epoch: row.epoch,
            horizon: row.horizon,
            scaler: row.scaler,
            shift: row.shift,
        };
        if best.as_ref().map(|x| cand.epoch >= x.epoch).unwrap_or(true) {
            best = Some(cand);
        }
    }
    best.unwrap_or(TipPick {
        tip: String::new(),
        epoch: 0,
        horizon: 0,
        scaler: "train_only".to_string(),
        shift: 0.0,
    })
}
EOF

cat > /app/flag/xv_c.rs <<'EOF'
pub fn bit_z(a: &str, b: i64, c: &str) -> String {
    let _ = (b, c);
    if a.is_empty() {
        "train_only".to_string()
    } else {
        a.to_string()
    }
}
EOF

cat > /app/mix/ward_d.rs <<'EOF'
pub fn mix_w(base: f64, causal: f64, leak: f64, shift: f64, epoch: i64) -> f64 {
    let _ = (base, leak, epoch);
    (causal + shift).max(0.0)
}
EOF

cat > /app/score/helm_e.rs <<'EOF'
pub fn score_u(base: f64, causal: f64, leak: f64, shift: f64, horizon: i64) -> f64 {
    let _ = (base, leak, horizon);
    (causal + shift * 0.5).max(0.0)
}
EOF

cat > /app/gate/emit_f.rs <<'EOF'
pub fn gate_y(smapes: &[f64], mases: &[f64], scalers: &[String], rows_ok: bool) -> bool {
    if !rows_ok || smapes.is_empty() || mases.is_empty() {
        return false;
    }
    if !scalers.iter().all(|s| s == "train_only") {
        return false;
    }
    smapes.iter().all(|v| v.is_finite()) && mases.iter().all(|v| v.is_finite())
}
EOF

bash /app/scripts/run_forecast_eval.sh
