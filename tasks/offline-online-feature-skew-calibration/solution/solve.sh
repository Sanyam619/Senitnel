#!/bin/bash
set -euo pipefail

# Select the serving snapshot for held-out evaluation.
cat > /app/calib/trial_pref.toml <<'EOF'
# Snapshot selection for the feature evaluation rotation.
[evaluation]
selection = "serving"
refresh = "auto"

[calibration]
family = "feature-eval"
split = "held-out"
EOF

# Record calibration lineage: the registry-resolved serving snapshot.
printf 'tip_g7\n' > /app/calib/tip_bind.accept

# Serving tip: highest-idx durable registry row that is not retired.
cat > /app/eng/sx/src/op_v.rs <<'EOF'
use bevel_core::base::Row;
use std::collections::HashSet;
use std::fs;
use std::path::Path;

fn tip_token(line: &str) -> Option<String> {
    let key = "\"tip\"";
    let i = line.find(key)?;
    let rest = &line[i + key.len()..];
    let rest = rest.trim_start().trim_start_matches(':').trim_start();
    if !rest.starts_with('"') {
        return None;
    }
    let rest = &rest[1..];
    let end = rest.find('"')?;
    Some(rest[..end].to_string())
}

pub fn op_v(rows: &[Row], root: &Path) -> String {
    let mut retired = HashSet::new();
    let rpath = root.join("feature_registry/retired_tips.jsonl");
    if let Ok(text) = fs::read_to_string(&rpath) {
        for line in text.lines() {
            let line = line.trim();
            if line.is_empty() {
                continue;
            }
            if let Some(t) = tip_token(line) {
                retired.insert(t);
            }
        }
    }
    let mut top = 0u32;
    let mut tip = String::new();
    for r in rows {
        if r.state != "durable" {
            continue;
        }
        if retired.contains(&r.tip) {
            continue;
        }
        if r.idx >= top {
            top = r.idx;
            tip = r.tip.clone();
        }
    }
    tip
}
EOF

# Skew polarity: online mean minus offline mean.
cat > /app/eng/sx/src/delta_q.rs <<'EOF'
pub fn delta_q(a: f64, b: f64) -> f64 {
    b - a
}
EOF

# Source label follows the selected serving snapshot id.
cat > /app/eng/sx/src/mark_w.rs <<'EOF'
pub fn mark_w(tip: &str) -> String {
    tip.to_string()
}
EOF

# Serving selection scores the seated snapshot without the trial overlay.
cat > /app/eng/core/src/mesh.rs <<'EOF'
use crate::base::FeatMap;

pub fn mesh_k(on: &FeatMap, shadow: &FeatMap, sel: &str) -> FeatMap {
    if sel == "serving" {
        return on.clone();
    }
    let mut out = on.clone();
    if let Some(v) = shadow.get("f_zip") {
        out.insert("f_zip".to_string(), *v);
    }
    out
}
EOF

/app/scripts/run_feature_eval.sh

head -c 240 /output/feature-eval.json || true
echo
