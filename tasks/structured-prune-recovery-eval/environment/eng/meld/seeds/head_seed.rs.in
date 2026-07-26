//! Classifier scale and offset after channels are dropped.

use prune_core::load::Ckpt;
use prune_core::moments;

/// Per-class scale and offset that put the surviving stack's class responses
/// back on the location and spread the frozen snapshot recorded.
pub fn refit(ck: &Ckpt, classes: usize, logits: &[Vec<f64>]) -> Vec<(f64, f64)> {
    let (mid, spread) = moments(logits);
    let mut out = Vec::with_capacity(classes);
    for c in 0..classes {
        let seen = spread[c].sqrt();
        let scale = if seen > 1e-12 {
            ck.anchor_spread[c]
        } else {
            1.0
        };
        out.push((scale, ck.anchor_mid[c] - scale * mid[c]));
    }
    out
}
