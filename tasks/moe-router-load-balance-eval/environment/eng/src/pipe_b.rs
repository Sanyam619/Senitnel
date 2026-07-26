use crate::helm_e::score_u;
use crate::ward_d::mix_w;

pub fn row_metrics(raw: &[f64], caps: &[f64], flags: &[bool], scale: f64) -> (Vec<f64>, f64, f64) {
    let weights = mix_w(raw, caps, flags, scale);
    let (ppl, ent) = score_u(&weights, scale);
    (weights, ppl, ent)
}
