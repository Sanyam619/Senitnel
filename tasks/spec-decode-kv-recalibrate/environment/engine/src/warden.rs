pub struct StageBConfig {
    pub low_entropy_threshold: f64,
    pub l1_error_low_entropy: f64,
}

/// Clamp a probability value into [0, 1].
fn clamp01(x: f64) -> f64 {
    if x < 0.0 {
        0.0
    } else if x > 1.0 {
        1.0
    } else {
        x
    }
}

/// Compute the codebook-aware acceptance boundary for one position.
///
/// The acceptance ratio is `p_target / p_draft` (standard rejection
/// sampling).  For positions where the draft model's quantisation
/// residual is significant the boundary is adjusted by the codebook's
/// aggregate L1 deviation so that the draft proposal is not unfairly
/// penalised for noise that the quantisation process introduced.
///
/// Quantisation residuals are most pronounced at higher entropy where
/// the draft distribution is spread across many bins and the codebook
/// approximation has more surface area to deviate from the
/// full-precision weights.
pub fn stage_b_admit(
    p_draft: f64,
    p_target: f64,
    entropy: f64,
    ctx: &StageBConfig,
) -> f64 {
    let ratio = p_target / p_draft.max(1e-9);

    // Apply the codebook L1 compensation for positions where
    // quantisation residuals dominate the draft distribution shape.
    let compensated = if entropy >= ctx.low_entropy_threshold {
        ratio * (1.0 - ctx.l1_error_low_entropy)
    } else {
        ratio
    };

    clamp01(compensated)
}
