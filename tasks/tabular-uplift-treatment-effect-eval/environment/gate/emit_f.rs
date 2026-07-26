pub fn gate_y(auucs: &[f64], qinis: &[f64], props: &[String], rows_ok: bool) -> bool {
    let _ = (qinis, props, rows_ok);
    match auucs.last() {
        Some(v) => *v > 0.05 && *v < 0.55,
        None => false,
    }
}
