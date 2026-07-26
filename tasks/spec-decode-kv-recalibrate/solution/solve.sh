#!/bin/bash
# Oracle recalibration for the speculative-decoding pipeline.
# Rewrites the calibration modules, patches the proposal / TV /
# acceptance / entropy-bucketing sites in main.rs, rebuilds the
# engine offline, and emits the recalibration report.
set -euo pipefail

test -d /app/eng
test -d /app/data/config
test -x /app/eng/target/release/spec-eval
mkdir -p /output

test -f /app/data/config/layer_scales.json
test -f /app/data/config/quant_blocks.json
test -f /app/data/config/codebook_stats.json
test -f /app/data/config/params.json

bash /app/scripts/verify_fixtures.sh > /dev/null

# ---- fix locus 1: draft-side logit adjustment ----------------------------
cat > /app/eng/src/axis.rs <<'AXIS_RS'
use crate::base::PositionRecord;

pub struct StageAConfig {
    pub layer_scales: Vec<f64>,
    pub block_size: usize,
    pub block_bias: Vec<f64>,
    pub low_entropy_threshold: f64,
}

fn layer_inv_scale(layer: usize, scales: &[f64]) -> f64 {
    let raw_scale = if layer < scales.len() {
        scales[layer]
    } else {
        1.0
    };
    if raw_scale.abs() > 1e-12 {
        1.0 / raw_scale
    } else {
        1.0
    }
}

fn block_bias_for(idx: usize, block_size: usize, biases: &[f64]) -> f64 {
    if biases.is_empty() {
        return 0.0;
    }
    let effective_bs = block_size.max(1);
    let block = (idx / effective_bs).min(biases.len().saturating_sub(1));
    biases[block]
}

pub fn stage_a_transform(pos: &PositionRecord, ctx: &StageAConfig) -> Vec<f64> {
    let inv = layer_inv_scale(pos.layer_id as usize, &ctx.layer_scales);

    pos.draft_logits
        .iter()
        .enumerate()
        .map(|(i, &raw)| {
            let bias = block_bias_for(i, ctx.block_size, &ctx.block_bias);
            (raw - bias) * inv
        })
        .collect()
}
AXIS_RS

# ---- fix locus 2: acceptance boundary ------------------------------------
cat > /app/eng/src/warden.rs <<'WARDEN_RS'
pub struct StageBConfig {
    pub low_entropy_threshold: f64,
    pub l1_error_low_entropy: f64,
}

fn clamp01(x: f64) -> f64 {
    if x < 0.0 {
        0.0
    } else if x > 1.0 {
        1.0
    } else {
        x
    }
}

pub fn stage_b_admit(
    p_draft: f64,
    p_target: f64,
    entropy: f64,
    ctx: &StageBConfig,
) -> f64 {
    let ratio = p_target / p_draft.max(1e-9);

    let compensated = if entropy < ctx.low_entropy_threshold {
        ratio * (1.0 + ctx.l1_error_low_entropy)
    } else {
        ratio
    };

    clamp01(compensated)
}
WARDEN_RS

# ---- fix locus 3: post-rejection decision --------------------------------
cat > /app/eng/src/helm.rs <<'HELM_RS'
pub enum Decision {
    Residual,
    Fallback,
}

pub struct StageCConfig {
    pub recent_window: usize,
    pub accept_floor: f64,
    pub low_entropy_threshold: f64,
}

fn evaluate_triggers(
    recent_accept_rate: f64,
    entropy: f64,
    rare_flag: bool,
    ctx: &StageCConfig,
) -> (bool, bool) {
    let rare_struggling =
        rare_flag && recent_accept_rate < (ctx.accept_floor + 0.35);
    let low_ent_struggling = (entropy < ctx.low_entropy_threshold - 0.10)
        && (recent_accept_rate < ctx.accept_floor);
    (rare_struggling, low_ent_struggling)
}

pub fn stage_c_route(
    recent_accept_rate: f64,
    entropy: f64,
    rare_flag: bool,
    ctx: &StageCConfig,
) -> Decision {
    let _ = ctx.recent_window;
    let (rare_trig, low_ent_trig) =
        evaluate_triggers(recent_accept_rate, entropy, rare_flag, ctx);

    if rare_trig || low_ent_trig {
        Decision::Fallback
    } else {
        Decision::Residual
    }
}
HELM_RS

# ---- fix locus 4: proposal token must come from calibrated draft ---------
python3 - <<'PY'
from pathlib import Path
path = Path("/app/eng/src/pipeline.rs")
text = path.read_text()
old = (
    "pub fn select_proposal_token(rec: &PositionRecord, _calibrated: &[f64]) -> usize {\n"
    "    argmax(&softmax(&rec.draft_logits))\n"
    "}"
)
new = (
    "pub fn select_proposal_token(_rec: &PositionRecord, calibrated: &[f64]) -> usize {\n"
    "    argmax(calibrated)\n"
    "}"
)
if old not in text:
    raise SystemExit("proposal-token locus not found in pipeline.rs")
path.write_text(text.replace(old, new, 1))
PY

# ---- fix locus 5: TV distance uses calibrated draft ----------------------
python3 - <<'PY'
from pathlib import Path
path = Path("/app/eng/src/pipeline.rs")
text = path.read_text()
old = (
    "pub fn compute_position_tv(\n"
    "    target: &[f64],\n"
    "    rec: &PositionRecord,\n"
    "    _calibrated: &[f64],\n"
    ") -> f64 {\n"
    "    let raw_draft = softmax(&rec.draft_logits);\n"
    "    0.5 * target\n"
    "        .iter()\n"
    "        .zip(raw_draft.iter())\n"
    "        .map(|(t, d)| (t - d).abs())\n"
    "        .sum::<f64>()\n"
    "}"
)
new = (
    "pub fn compute_position_tv(\n"
    "    target: &[f64],\n"
    "    _rec: &PositionRecord,\n"
    "    calibrated: &[f64],\n"
    ") -> f64 {\n"
    "    0.5 * target\n"
    "        .iter()\n"
    "        .zip(calibrated.iter())\n"
    "        .map(|(t, d)| (t - d).abs())\n"
    "        .sum::<f64>()\n"
    "}"
)
if old not in text:
    raise SystemExit("tv-distance locus not found in pipeline.rs")
path.write_text(text.replace(old, new, 1))
PY

# ---- fix locus 6: acceptance p_t indexes by draft-proposed token ---------
python3 - <<'PY'
from pathlib import Path
path = Path("/app/eng/src/pipeline.rs")
text = path.read_text()
old = (
    "pub fn acceptance_target_probability(target_dist: &[f64], _draft_tok: usize) -> f64 {\n"
    "    target_dist[argmax(target_dist)]\n"
    "}"
)
new = (
    "pub fn acceptance_target_probability(target_dist: &[f64], draft_tok: usize) -> f64 {\n"
    "    target_dist[draft_tok]\n"
    "}"
)
if old not in text:
    raise SystemExit("acceptance p_t locus not found in pipeline.rs")
path.write_text(text.replace(old, new, 1))
PY

# ---- fix locus 7: entropy bucketing threshold in summary -----------------
python3 - <<'PY'
from pathlib import Path
path = Path("/app/eng/src/main.rs")
text = path.read_text()
old = "if ev.entropy < 0.45 {"
new = "if ev.entropy < 0.55 {"
if old not in text:
    raise SystemExit("entropy-threshold locus not found in main.rs")
path.write_text(text.replace(old, new, 1))
PY

# ---- assertions that all loci are correctly patched ----------------------
grep -q "(*raw - bias)" /app/eng/src/axis.rs
! grep -q "(raw + bias)" /app/eng/src/axis.rs

grep -q "entropy < ctx.low_entropy_threshold" /app/eng/src/warden.rs
grep -q "1.0 + ctx.l1_error_low_entropy" /app/eng/src/warden.rs
! grep -q "entropy >= ctx" /app/eng/src/warden.rs
! grep -q "1.0 - ctx" /app/eng/src/warden.rs

grep -q "Decision::Fallback" /app/eng/src/helm.rs
# The if-branch (triggered) should map to Fallback
python3 -c "
t = open('/app/eng/src/helm.rs').read()
idx_if = t.index('if rare_trig || low_ent_trig')
idx_fb = t.index('Decision::Fallback', idx_if)
idx_res = t.index('Decision::Residual', idx_if)
assert idx_fb < idx_res, 'Fallback must come before Residual in the if-branch'
"

grep -q "fn select_proposal_token(_rec:" /app/eng/src/pipeline.rs
grep -q "argmax(calibrated)" /app/eng/src/pipeline.rs
! grep -q "argmax(&softmax(&rec.draft_logits))" /app/eng/src/pipeline.rs

grep -q "fn compute_position_tv" /app/eng/src/pipeline.rs
grep -q ".zip(calibrated.iter())" /app/eng/src/pipeline.rs
! grep -q "raw_draft" /app/eng/src/pipeline.rs

grep -q "fn acceptance_target_probability.*draft_tok:" /app/eng/src/pipeline.rs
grep -q "target_dist\[draft_tok\]" /app/eng/src/pipeline.rs
! grep -q "argmax(target_dist)\]" /app/eng/src/pipeline.rs

grep -q 'ev.entropy < 0.55' /app/eng/src/main.rs
! grep -q 'ev.entropy < 0.45' /app/eng/src/main.rs

# ---- rebuild from patched source -----------------------------------------
cd /app/eng
cargo build --release --offline --locked
test -x /app/eng/target/release/spec-eval

# ---- probe every slice to verify the rebuilt binary ----------------------
for slice in num_completion repetition_prose low_entropy_json code_rare_tokens; do
  /app/eng/target/release/spec-eval probe \
    --slice "${slice}" \
    --data /app/data \
    --seed 3405691582 \
    --out "/tmp/probe_${slice}.jsonl"
  test -s "/tmp/probe_${slice}.jsonl"
done

# ---- generate the official report ---------------------------------------
bash /app/scripts/run_eval.sh

# ---- validate report meets every health band ----------------------------
python3 - <<'PY'
import json
from pathlib import Path

report = json.loads(Path("/output/recalibration-report.json").read_text())
assert report["schema_tag"] == "spec-calib-v1"
assert len(report["slices"]) == 4
for entry in report["slices"]:
    assert entry["ks_statistic"] <= 0.10, entry
    assert entry["accept_rate"] >= 0.75, entry
    assert entry["mean_draft_target_tv"] >= 0.003, entry
    assert entry["mean_draft_target_tv"] <= 0.06, entry
    assert entry["fallback_rate"] <= 0.15, entry
    assert entry["high_entropy_accept_rate"] >= 0.80, entry
summary = report["summary"]
assert summary["overall_speedup"] >= 1.60, summary
assert summary["overall_speedup"] < 2.0, summary
assert summary["overall_divergence"] <= 0.075, summary
assert summary["overall_fallback_rate"] <= 0.20, summary
high = report["positions"]["high_entropy"]["accept_rate"]
low = report["positions"]["low_entropy"]["accept_rate"]
assert high >= 0.85, ("high_entropy", high)
assert low >= 0.85, ("low_entropy", low)
assert report["positions"]["low_entropy"]["count"] > 0
assert report["positions"]["high_entropy"]["count"] > 0
print("oracle recalibration report meets every runtime threshold")
PY

echo "recalibration complete"
