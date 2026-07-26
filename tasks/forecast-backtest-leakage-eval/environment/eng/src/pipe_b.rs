pub fn row_metrics(
    smape_causal: f64,
    mase_causal: f64,
    smape_leak: f64,
    mase_leak: f64,
    shift: f64,
    epoch: i64,
    horizon: i64,
) -> (f64, f64) {
    let smape = crate::ward_d::mix_w(smape_causal, smape_causal, smape_leak, shift, epoch);
    let mase = crate::helm_e::score_u(mase_causal, mase_causal, mase_leak, shift, horizon);
    (smape, mase)
}
