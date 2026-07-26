use crate::helm_e::score_u;
use crate::ward_d::mix_w;

pub fn row_metrics(
    margins: &[f64],
    cand: &[Vec<f64>],
    reference: &[Vec<f64>],
    beta: f64,
) -> (f64, f64) {
    let win = mix_w(margins, beta);
    let kl = score_u(cand, reference);
    (win, kl)
}
