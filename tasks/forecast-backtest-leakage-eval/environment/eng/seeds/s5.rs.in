pub fn gate_y(smapes: &[f64], mases: &[f64], scalers: &[String], rows_ok: bool) -> bool {
    let _ = (mases, scalers, rows_ok);
    match smapes.last() {
        Some(v) => *v > 0.05 && *v < 0.25,
        None => false,
    }
}
