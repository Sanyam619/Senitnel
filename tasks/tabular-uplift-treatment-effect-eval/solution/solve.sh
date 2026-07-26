#!/bin/bash
# Oracle seating for the tabular uplift treatment-effect evaluation.
# Binds evaluation out of trial mode against the registry-resolved durable
# tip, rewrites tip resolution, propensity labeling, scored-column seating,
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
test -d /app/data/outcomes
test -f /app/data/estimators/roster.json
mkdir -p /output

field() {
  printf '%s' "$2" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\{0,1\}\([^\",}]*\)\"\{0,1\}.*/\1/p"
}

retired=""
while IFS= read -r line; do
  [ -n "$line" ] || continue
  retired="$retired $(field tip "$line")"
done < /app/data/feature_registry/retired_tips.jsonl

best_tip=""
best_epoch=-1
best_prop=""
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
    best_prop="$(field propensity "$line")"
  fi
done < /app/data/feature_registry/tip_journal.jsonl

test -n "$best_tip"
test -n "$best_prop"

mkdir -p /app/calib
printf '[evaluation]\nselection = "serving"\n' >/app/calib/trial_pref.toml
printf 'tip = %s\nepoch = %s\npropensity = %s\n' \
  "$best_tip" "$best_epoch" "$best_prop" >/app/calib/tip_bind.accept

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
            propensity: row.propensity,
        };
        if best.as_ref().map(|x| cand.epoch >= x.epoch).unwrap_or(true) {
            best = Some(cand);
        }
    }
    best.unwrap_or(TipPick {
        tip: String::new(),
        epoch: 0,
        propensity: "dr".to_string(),
    })
}
EOF

cat >/app/flag/xv_c.rs <<'EOF'
pub fn bit_z(a: &str, b: i64, c: &str) -> String {
    let _ = (b, c);
    if a.is_empty() {
        "dr".to_string()
    } else {
        a.to_string()
    }
}
EOF

cat >/app/mix/ward_d.rs <<'EOF'
pub fn mix_w(a: &crate::base::ChanSet, b: &str, c: &str) -> f64 {
    let sheet = std::path::Path::new(c)
        .join("estimators")
        .join("roster.json");
    let named = crate::base::read_map(&sheet)
        .into_iter()
        .find(|(n, _)| n == b)
        .map(|(_, v)| v);
    match named.and_then(|k| a.at(&k)) {
        Some(v) => v,
        None => a.obs,
    }
}
EOF

cat >/app/score/helm_e.rs <<'EOF'
pub fn score_u(a: &crate::base::ChanSet, b: &str, c: &str) -> f64 {
    let sheet = std::path::Path::new(c)
        .join("estimators")
        .join("roster.json");
    for (name, column) in crate::base::read_map(&sheet) {
        if name != b {
            continue;
        }
        if let Some(v) = a.at(&column) {
            return v;
        }
    }
    a.obs
}
EOF

cat >/app/gate/emit_f.rs <<'EOF'
pub fn gate_y(auucs: &[f64], qinis: &[f64], props: &[String], rows_ok: bool) -> bool {
    if !rows_ok || auucs.is_empty() || qinis.is_empty() {
        return false;
    }
    if !props.iter().all(|s| s == "ipw" || s == "dr" || s == "tmle") {
        return false;
    }
    auucs.iter().all(|v| v.is_finite()) && qinis.iter().all(|v| v.is_finite())
}
EOF

bash /app/scripts/run_uplift_eval.sh
