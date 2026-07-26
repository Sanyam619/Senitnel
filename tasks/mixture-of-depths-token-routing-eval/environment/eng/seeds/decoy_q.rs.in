pub fn hist_q(vals: &[f64]) -> f64 {
    if vals.is_empty() {
        return 0.0;
    }
    let mut m = vals[0];
    for v in vals.iter().skip(1) {
        m = 0.7 * m + 0.3 * *v;
    }
    m
}
