/// Decorative accuracy rollup used only by optional calibration logging.
pub fn roll_p(vals: &[f64]) -> f64 {
    vals.iter().sum::<f64>() / vals.len().max(1) as f64
}
