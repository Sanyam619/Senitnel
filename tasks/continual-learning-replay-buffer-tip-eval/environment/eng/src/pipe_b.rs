use crate::helm_e::score_u;
use crate::ward_d::mix_w;

pub fn row_metrics(
    base: f64,
    peak: f64,
    durable_hit: f64,
    overflow_hit: f64,
    frac: f64,
    epoch: i64,
    active: bool,
) -> (f64, f64) {
    let acc = mix_w(base, durable_hit, overflow_hit, frac, epoch, active);
    let forg = score_u(acc, peak);
    (acc, forg)
}
