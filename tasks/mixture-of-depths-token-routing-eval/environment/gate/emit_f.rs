pub fn gate_y(depths: &[f64], ppls: &[f64], caps: &[f64], rows_ok: bool) -> bool {
    let _ = rows_ok;
    if depths.is_empty() || ppls.is_empty() || caps.is_empty() {
        return false;
    }
    depths.iter().all(|v| v.is_finite()) && ppls.iter().all(|v| v.is_finite())
}
