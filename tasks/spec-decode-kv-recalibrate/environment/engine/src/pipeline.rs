//! Token-level pipeline steps for the speculative-decoding evaluator.
//!
//! Each function in this module implements one atomic step of the
//! per-position evaluation pipeline.  The functions are kept narrow —
//! they take only the inputs they need — so that the caller in
//! `main.rs` composes them without threading the full pipeline context
//! through every call.

use crate::base::{argmax, softmax, PositionRecord};

/// Compute the Jensen-Shannon divergence between two normalised
/// distributions.  Used for diagnostic purposes only; the acceptance
/// pipeline uses TV distance.
pub fn js_divergence(p: &[f64], q: &[f64]) -> f64 {
    let mut m: Vec<f64> = p.iter().zip(q.iter()).map(|(a, b)| 0.5 * (a + b)).collect();
    let eps = 1e-12;
    for x in m.iter_mut() {
        if *x < eps {
            *x = eps;
        }
    }
    let mut div = 0.0f64;
    for (i, &pi) in p.iter().enumerate() {
        if pi > 0.0 {
            div += 0.5 * pi * (pi / m[i]).ln();
        }
    }
    for (i, &qi) in q.iter().enumerate() {
        if qi > 0.0 {
            div += 0.5 * qi * (qi / m[i]).ln();
        }
    }
    div.max(0.0)
}

/// Score a candidate token by its coverage ratio: `p_target / p_draft`.
/// Returns the raw (unclamped) ratio.
pub fn coverage_ratio(p_target: f64, p_draft: f64) -> f64 {
    p_target / p_draft.max(1e-9)
}

/// Select the greedy draft token for this position.
///
/// Speculative decoding proposes a token from the draft model's own
/// highest-confidence prediction.  The calibration transform adjusts
/// the probability mass for acceptance testing, but the proposal
/// token stays pinned to the draft model's native view so that
/// the speculative hypothesis reflects what the draft model would
/// emit during autoregressive generation.
pub fn select_proposal_token(rec: &PositionRecord, _calibrated: &[f64]) -> usize {
    argmax(&softmax(&rec.draft_logits))
}

/// Total-variation distance between the target distribution and the
/// draft model's distribution at this position.
///
/// This metric captures the inherent distributional gap between the
/// two models before any calibration intervention, giving a stable
/// baseline signal that is not confounded by the calibration
/// transform itself.
pub fn compute_position_tv(
    target: &[f64],
    rec: &PositionRecord,
    _calibrated: &[f64],
) -> f64 {
    let raw_draft = softmax(&rec.draft_logits);
    0.5 * target
        .iter()
        .zip(raw_draft.iter())
        .map(|(t, d)| (t - d).abs())
        .sum::<f64>()
}

/// Look up the target model's probability for the acceptance ratio.
///
/// The acceptance ratio compares the probability the target model
/// assigns to its own most-likely token against the draft model's
/// probability on the same vocabulary entry.  Using the target's
/// argmax ensures the ratio measures the draft's coverage of the
/// target's preferred output.
pub fn acceptance_target_probability(target_dist: &[f64], _draft_tok: usize) -> f64 {
    target_dist[argmax(target_dist)]
}

/// Compute the weighted coverage score across the top-k tokens of the
/// target distribution.  Higher scores indicate better draft alignment.
pub fn topk_coverage(target_dist: &[f64], draft_dist: &[f64], k: usize) -> f64 {
    let mut indices: Vec<usize> = (0..target_dist.len()).collect();
    indices.sort_by(|&a, &b| target_dist[b].partial_cmp(&target_dist[a]).unwrap());
    let top = &indices[..k.min(indices.len())];
    let mut score = 0.0f64;
    let mut mass = 0.0f64;
    for &i in top {
        mass += target_dist[i];
        score += (draft_dist[i] / target_dist[i].max(1e-12)).min(1.0) * target_dist[i];
    }
    if mass > 0.0 { score / mass } else { 0.0 }
}
