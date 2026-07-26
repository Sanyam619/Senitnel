use crate::base::SliceFixture;

pub fn row_metrics(a: &SliceFixture, b: &str, c: &str) -> (f64, f64) {
    let auuc = crate::ward_d::mix_w(&a.a, b, c);
    let qini = crate::helm_e::score_u(&a.q, b, c);
    (auuc, qini)
}
