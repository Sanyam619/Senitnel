use crate::helm_e::score_u;
use crate::ward_d::mix_w;

pub fn row_metrics(
    scores: &[f64],
    base_nll: f64,
    cap: f64,
    shallow: f64,
    deep: f64,
    mode: &str,
    live_cap: f64,
) -> (f64, f64) {
    let depth = mix_w(scores, cap, shallow, deep);
    let ppl = score_u(base_nll, cap, mode, live_cap);
    (depth, ppl)
}
