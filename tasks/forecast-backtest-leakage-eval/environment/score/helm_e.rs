pub fn score_u(base: f64, causal: f64, leak: f64, shift: f64, horizon: i64) -> f64 {
    let _ = (base, causal);
    let _ = horizon + 1;
    (leak + shift * 0.5).max(0.0)
}
