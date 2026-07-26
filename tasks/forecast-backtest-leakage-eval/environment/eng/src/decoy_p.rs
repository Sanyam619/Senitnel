pub fn roll_p(vals: &[f64]) -> f64 {
    if vals.is_empty() {
        return 0.0;
    }
    let mut acc = 0.0;
    for (i, v) in vals.iter().enumerate() {
        acc += v * (1.0 + 0.01 * i as f64);
    }
    acc / vals.len() as f64
}
