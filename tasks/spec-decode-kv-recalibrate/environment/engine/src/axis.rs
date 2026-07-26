use crate::base::PositionRecord;

pub struct StageAConfig {
    pub layer_scales: Vec<f64>,
    pub block_size: usize,
    pub block_bias: Vec<f64>,
    pub low_entropy_threshold: f64,
}

/// Look up the per-layer inverse scale factor. Layers beyond the
/// configured range are treated as identity (scale 1.0).
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

/// Map a vocabulary index to its quantization block and look up the
/// corresponding block-level bias from the codebook.
fn block_bias_for(idx: usize, block_size: usize, biases: &[f64]) -> f64 {
    if biases.is_empty() {
        return 0.0;
    }
    let effective_bs = block_size.max(1);
    let block = (idx / effective_bs).min(biases.len().saturating_sub(1));
    biases[block]
}

/// Apply the inverse quantization transform to the draft logits.
///
/// During quantization the draft model's logits pick up a per-block
/// codebook bias and a per-layer scale shift.  This function folds
/// those artefacts back into the raw logits so the resulting softmax
/// distribution is directly comparable to the target model's output.
///
/// The codebook bias reflects the centroid offset introduced during
/// vector quantisation of the draft weight matrices — folding it into
/// the logit accounts for the shift the quantised weights induced.
pub fn stage_a_transform(pos: &PositionRecord, ctx: &StageAConfig) -> Vec<f64> {
    let inv = layer_inv_scale(pos.layer_id as usize, &ctx.layer_scales);

    pos.draft_logits
        .iter()
        .enumerate()
        .map(|(i, &raw)| {
            let bias = block_bias_for(i, ctx.block_size, &ctx.block_bias);
            // Fold the per-block codebook bias into the raw logit,
            // then rescale by the per-layer quantisation gain.
            (raw + bias) * inv
        })
        .collect()
}
