#!/bin/bash
# Oracle seating for the speech diarization DER calibration desk.
# Binds evaluation out of trial mode against the registry-resolved durable
# tips, rewrites tip resolution, clustering method seating, DER/JER column
# lookup, and the deep eval gate, then rebuilds and emits the report.
set -euo pipefail

test -d /app/eng
test -d /app/calib
test -d /app/seat
test -d /app/flag
test -d /app/mix
test -d /app/score
test -d /app/gate
test -d /app/data/embed_registry
test -d /app/data/cluster_registry
test -d /app/data/audio
test -d /app/data/rttm
mkdir -p /output

field() {
  printf '%s' "$2" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\{0,1\}\([^\",}]*\)\"\{0,1\}.*/\1/p"
}

retired_embed=""
while IFS= read -r line; do
  [ -n "$line" ] || continue
  retired_embed="$retired_embed $(field tip "$line")"
done < /app/data/embed_registry/retired_tips.jsonl

best_tip=""
best_epoch=-1
while IFS= read -r line; do
  [ -n "$line" ] || continue
  case "$line" in
  *'"sealed"'*true*) ;;
  *) continue ;;
  esac
  tip="$(field tip "$line")"
  case " $retired_embed " in
  *" $tip "*) continue ;;
  esac
  epoch="$(field epoch "$line")"
  if [ "$epoch" -ge "$best_epoch" ]; then
    best_tip="$tip"
    best_epoch="$epoch"
  fi
done < /app/data/embed_registry/tip_journal.jsonl

retired_cluster=""
while IFS= read -r line; do
  [ -n "$line" ] || continue
  retired_cluster="$retired_cluster $(field tip "$line")"
done < /app/data/cluster_registry/retired_tips.jsonl

best_method=""
best_cluster=""
best_m_epoch=-1
while IFS= read -r line; do
  [ -n "$line" ] || continue
  case "$line" in
  *'"sealed"'*true*) ;;
  *) continue ;;
  esac
  tip="$(field tip "$line")"
  case " $retired_cluster " in
  *" $tip "*) continue ;;
  esac
  epoch="$(field epoch "$line")"
  if [ "$epoch" -ge "$best_m_epoch" ]; then
    best_method="$tip"
    best_m_epoch="$epoch"
    best_cluster="$(field clustering "$line")"
  fi
done < /app/data/cluster_registry/tip_journal.jsonl

test -n "$best_tip"
test -n "$best_cluster"
test -n "$best_method"

mkdir -p /app/calib
printf '[evaluation]\nselection = "serving"\n' >/app/calib/trial_pref.toml
printf 'tip = %s\nepoch = %s\nclustering = %s\nmethod = %s\n' \
  "$best_tip" "$best_epoch" "$best_cluster" "$best_method" >/app/calib/tip_bind.accept

cat >/app/seat/knit_b.rs <<'EOF'
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
    let retired = crate::base::read_retired(&retired_path);
    let rows = crate::base::read_journal(journal);
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
        };
        if best.as_ref().map(|x| cand.epoch >= x.epoch).unwrap_or(true) {
            best = Some(cand);
        }
    }
    best.unwrap_or(TipPick {
        tip: String::new(),
        epoch: 0,
    })
}
EOF

cat >/app/flag/xv_c.rs <<'EOF'
use std::path::Path;

pub fn bit_z(a: &str, b: i64, c: &str) -> String {
    let _ = b;
    let journal = Path::new(a);
    let retired_path = if c.is_empty() {
        journal
            .parent()
            .map(|p| p.join("retired_tips.jsonl"))
            .unwrap_or_else(|| Path::new("retired_tips.jsonl").to_path_buf())
    } else {
        Path::new(c).to_path_buf()
    };
    let retired = crate::base::read_retired(&retired_path);
    let rows = crate::base::read_journal(journal);
    let mut best: Option<(i64, String)> = None;
    for row in rows {
        if !row.sealed {
            continue;
        }
        if retired.iter().any(|t| t == &row.tip) {
            continue;
        }
        if best.as_ref().map(|(e, _)| row.epoch >= *e).unwrap_or(true) {
            best = Some((row.epoch, row.clustering));
        }
    }
    best.map(|(_, m)| m).unwrap_or_else(|| "ahc".to_string())
}
EOF

cat >/app/mix/ward_d.rs <<'EOF'
pub fn mix_w(a: &crate::base::ChanSet, b: &str, c: i64) -> f64 {
    let key = format!("{}_e{}", b, c);
    match a.at(&key) {
        Some(v) => v,
        None => a.obs,
    }
}
EOF

cat >/app/score/helm_e.rs <<'EOF'
pub fn score_u(a: &crate::base::ChanSet, b: &str, c: i64) -> f64 {
    let key = format!("{}_e{}", b, c);
    match a.at(&key) {
        Some(v) => v,
        None => a.obs,
    }
}
EOF

cat >/app/gate/emit_f.rs <<'EOF'
pub fn gate_y(ders: &[f64], jers: &[f64], methods: &[String], rows_ok: bool) -> bool {
    if !rows_ok || ders.is_empty() || jers.is_empty() {
        return false;
    }
    if !methods
        .iter()
        .all(|s| s == "ahc" || s == "spectral" || s == "nme")
    {
        return false;
    }
    ders.iter().all(|v| v.is_finite()) && jers.iter().all(|v| v.is_finite())
}
EOF

bash /app/scripts/run_diar_eval.sh
