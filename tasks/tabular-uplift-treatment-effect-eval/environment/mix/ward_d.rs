pub fn mix_w(a: &crate::base::ChanSet, b: &str, c: &str) -> f64 {
    let _ = (b, c);
    a.obs.max(0.0)
}
