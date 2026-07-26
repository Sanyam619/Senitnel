#!/bin/bash
# Oracle for the mixture-of-depths token-routing evaluation.
# Binds evaluation out of trial mode against the registry-resolved durable
# tip, corrects tip resolution, capacity, avg-depth, and perplexity
# scoring plus the deep eval gate, then rebuilds and emits the report.
set -euo pipefail

test -d /app/eng
test -d /app/calib
test -d /app/seat
test -d /app/flag
test -d /app/mix
test -d /app/score
test -d /app/gate
test -d /app/data/routers
test -d /app/data/ckpt
test -d /app/data/eval
mkdir -p /output

field() {
  printf '%s' "$2" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\{0,1\}\([^\",}]*\)\"\{0,1\}.*/\1/p"
}

retired=""
while IFS= read -r line; do
  [ -n "$line" ] || continue
  retired="$retired $(field tip "$line")"
done < /app/data/routers/retired_tips.jsonl

best_tip=""
best_epoch=-1
best_cap=""
while IFS= read -r line; do
  [ -n "$line" ] || continue
  case "$line" in
  *'"sealed"'*true*) ;;
  *) continue ;;
  esac
  tip="$(field tip "$line")"
  case " $retired " in
  *" $tip "*) continue ;;
  esac
  epoch="$(field epoch "$line")"
  if [ "$epoch" -ge "$best_epoch" ]; then
    best_tip="$tip"
    best_epoch="$epoch"
    best_cap="$(field capacity "$line")"
  fi
done < /app/data/routers/tip_journal.jsonl

test -n "$best_tip"
test -n "$best_cap"

mkdir -p /app/calib
printf '[evaluation]\nselection = "serving"\n' >/app/calib/trial_pref.toml
printf 'tip = %s\nepoch = %s\ncapacity = %s\n' \
  "$best_tip" "$best_epoch" "$best_cap" >/app/calib/tip_bind.accept

cat >/app/seat/knit_b.rs <<'EOF'
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
            capacity: row.capacity,
        };
        if best.as_ref().map(|x| cand.epoch >= x.epoch).unwrap_or(true) {
            best = Some(cand);
        }
    }
    best.unwrap_or(TipPick {
        tip: String::new(),
        epoch: 0,
        capacity: 0.5,
    })
}
EOF

cat >/app/flag/xv_c.rs <<'EOF'
pub fn bit_z(a: f64, b: f64, c: &str) -> f64 {
    let _ = (b, c);
    if a.is_finite() && a > 0.0 {
        a
    } else {
        0.5
    }
}
EOF

cat >/app/mix/ward_d.rs <<'EOF'
pub fn mix_w(scores: &[f64], cap: f64, shallow: f64, deep: f64) -> f64 {
    let n = scores.len();
    if n == 0 {
        return shallow;
    }
    let mut k = (n as f64 * cap).round() as usize;
    if k > n {
        k = n;
    }
    let mut order: Vec<usize> = (0..n).collect();
    order.sort_by(|&i, &j| {
        scores[j]
            .partial_cmp(&scores[i])
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    let mut depths = vec![shallow; n];
    for &i in order.iter().take(k) {
        depths[i] = deep;
    }
    depths.iter().sum::<f64>() / n as f64
}
EOF

cat >/app/score/helm_e.rs <<'EOF'
pub fn score_u(base_nll: f64, cap: f64, mode: &str, live_cap: f64) -> f64 {
    let _ = (mode, live_cap);
    let c = if cap.is_finite() && cap > 0.0 { cap } else { 0.5 };
    base_nll.exp() / (1.0 + c)
}
EOF

cat >/app/gate/emit_f.rs <<'EOF'
pub fn gate_y(depths: &[f64], ppls: &[f64], caps: &[f64], rows_ok: bool) -> bool {
    if !rows_ok || depths.is_empty() || ppls.is_empty() || caps.is_empty() {
        return false;
    }
    if caps.iter().any(|c| (*c - 1.0).abs() < 1e-9) {
        return false;
    }
    depths.iter().all(|v| v.is_finite()) && ppls.iter().all(|v| v.is_finite())
}
EOF

bash /app/scripts/run_mod_eval.sh
