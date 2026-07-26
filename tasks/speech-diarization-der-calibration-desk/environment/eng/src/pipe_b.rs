use crate::base::SliceFixture;

pub fn row_metrics(a: &SliceFixture, b: &str, c: i64) -> (f64, f64) {
    let der = crate::ward_d::mix_w(&a.der, b, c);
    let jer = crate::helm_e::score_u(&a.jer, b, c);
    (der, jer)
}
