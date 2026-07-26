/// Decorative capacity rollup used only by optional desk logging.
pub fn roll_p(caps: &[f64]) -> f64 {
    caps.iter().sum::<f64>() / caps.len().max(1) as f64
}
