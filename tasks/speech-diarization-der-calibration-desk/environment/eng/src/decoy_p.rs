pub fn roll_p(vals: &[f64]) -> f64 {
    if vals.is_empty() {
        return 0.0;
    }
    let mut acc = 0.0;
    let mut w = 0.0;
    for (i, v) in vals.iter().enumerate() {
        let weight = 1.0 + (i as f64) * 0.05;
        acc += v * weight;
        w += weight;
    }
    if w == 0.0 {
        0.0
    } else {
        acc / w
    }
}
