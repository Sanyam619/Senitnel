#!/bin/bash
# Oracle seating for the continual-learning replay-buffer evaluation.
# Binds serving selection against the journal-resolved durable tip, rewrites
# tip resolution, stratum hold windows, durable scoring, forgetting, and the
# deep eval gate, then rebuilds and emits the report.
set -euo pipefail

test -d /app/eng
test -d /app/calib
test -d /app/seat
test -d /app/flag
test -d /app/mix
test -d /app/score
test -d /app/gate
test -d /app/data/replay
test -d /app/data/tasks
mkdir -p /output

python3 - <<'PY'
import json
from pathlib import Path

retired = set()
for line in Path("/app/data/replay/retired_tips.jsonl").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line:
        continue
    retired.add(json.loads(line)["tip"])

best = None
for line in Path("/app/data/replay/tip_journal.jsonl").read_text(encoding="utf-8").splitlines():
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
    f"tip = {best['tip']}\nepoch = {best['epoch']}\nreplay = {best['replay_frac']}\n",
    encoding="utf-8",
)
PY

cat > /app/seat/knit_b.rs <<'EOF'
use crate::base::read_journal;
use crate::base::read_retired;
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
    let mut best = (0.0_f64, 0_i64);
    let mut found = false;
    for row in rows {
        if !row.sealed {
            continue;
        }
        if retired.iter().any(|t| t == &row.tip) {
            continue;
        }
        if !found || row.epoch >= best.1 {
            best = (row.replay_frac, row.epoch);
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
pub fn mix_w(
    base: f64,
    durable_hit: f64,
    overflow_hit: f64,
    frac: f64,
    epoch: i64,
    active: bool,
) -> f64 {
    let _ = overflow_hit;
    if epoch <= 0 {
        return base.clamp(0.0, 1.0);
    }
    if active {
        (base + frac * durable_hit).clamp(0.0, 1.0)
    } else {
        base.clamp(0.0, 1.0)
    }
}
EOF

cat > /app/score/helm_e.rs <<'EOF'
pub fn score_u(acc: f64, peak: f64) -> f64 {
    (peak - acc).max(0.0)
}
EOF

cat > /app/gate/emit_f.rs <<'EOF'
pub fn gate_y(
    accs: &[f64],
    forgettings: &[f64],
    fracs: &[f64],
    actives: &[bool],
    rows_ok: bool,
) -> bool {
    if accs.len() != forgettings.len()
        || accs.len() != fracs.len()
        || accs.len() != actives.len()
        || accs.is_empty()
    {
        return false;
    }
    for f in forgettings {
        if !f.is_finite() || *f < -1e-9 {
            return false;
        }
    }
    let first = fracs[0];
    for v in fracs {
        if (v - first).abs() > 1e-9 {
            return false;
        }
    }
    if !actives.iter().any(|a| *a) {
        return false;
    }
    rows_ok
}
EOF

bash /app/scripts/run_cl_eval.sh
