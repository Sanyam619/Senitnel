pub fn mix_w(raw: &[f64], caps: &[f64], flags: &[bool], scale: f64) -> Vec<f64> {
    let _ = caps;
    let n = raw.len().min(flags.len());
    if n == 0 {
        return Vec::new();
    }
    let s = if scale.abs() < 1e-12 { 1.0 } else { scale };
    let mx = raw
        .iter()
        .take(n)
        .map(|v| v / s)
        .fold(f64::NEG_INFINITY, f64::max);
    let ex: Vec<f64> = (0..n).map(|i| (raw[i] / s - mx).exp()).collect();
    let total: f64 = ex.iter().sum::<f64>().max(f64::MIN_POSITIVE);
    let masked: Vec<f64> = (0..n)
        .map(|i| if flags[i] { ex[i] / total } else { 0.0 })
        .collect();
    let mass: f64 = masked.iter().sum();
    if mass <= 1e-15 {
        let active = flags.iter().filter(|f| **f).count().max(1) as f64;
        return flags
            .iter()
            .map(|f| if *f { 1.0 / active } else { 0.0 })
            .collect();
    }
    masked.iter().map(|v| v / mass).collect()
}
