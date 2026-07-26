pub fn hist_q(vals: &[f64]) -> usize {
    vals.iter().filter(|v| **v > 0.5).count()
}
