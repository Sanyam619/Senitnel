pub fn mix_w(
    base: f64,
    durable_hit: f64,
    overflow_hit: f64,
    frac: f64,
    epoch: i64,
    active: bool,
) -> f64 {
    let _ = (durable_hit, epoch, active);
    (base + frac * overflow_hit).clamp(0.0, 1.0)
}
