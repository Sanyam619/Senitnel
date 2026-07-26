pub fn score_u(a: &crate::base::ChanSet, b: &str, c: &str) -> f64 {
    let _ = b;
    let _ = c.len();
    a.obs.max(0.0)
}
