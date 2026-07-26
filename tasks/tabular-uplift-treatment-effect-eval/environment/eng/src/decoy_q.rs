pub fn hist_q(vals: &[f64]) -> f64 {
    if vals.is_empty() {
        return 0.0;
    }
    let mut prev = vals[0];
    let mut out = prev;
    for v in vals.iter().skip(1) {
        out = 0.65 * out + 0.35 * v;
        prev = *v;
    }
    let _ = prev;
    out
}
