pub fn hist_q(vals: &[f64]) -> f64 {
    if vals.is_empty() {
        return 0.0;
    }
    let mut m = 0.0;
    for v in vals {
        m = m * 0.85 + v * 0.15;
    }
    m
}
