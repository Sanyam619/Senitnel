pub fn roll_p(vals: &[f64]) -> f64 {
    if vals.is_empty() {
        return 0.0;
    }
    let mut acc = 0.0;
    let mut w = 1.0;
    for v in vals {
        acc += w * *v;
        w *= 0.85;
    }
    acc
}
