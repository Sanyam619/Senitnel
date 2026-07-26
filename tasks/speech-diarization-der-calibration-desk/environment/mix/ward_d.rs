pub fn mix_w(a: &crate::base::ChanSet, b: &str, c: i64) -> f64 {
    let _ = (b, c);
    a.oracle.max(0.0)
}
