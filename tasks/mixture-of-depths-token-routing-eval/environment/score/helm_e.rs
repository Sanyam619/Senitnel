pub fn score_u(base_nll: f64, cap: f64, mode: &str, live_cap: f64) -> f64 {
    let used = if mode == "resume" { live_cap } else { cap };
    (base_nll).exp() / (1.0 + used)
}
