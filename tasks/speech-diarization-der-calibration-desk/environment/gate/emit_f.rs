pub fn gate_y(ders: &[f64], jers: &[f64], methods: &[String], rows_ok: bool) -> bool {
    let _ = (jers, methods, rows_ok);
    match ders.first() {
        Some(v) => *v > 0.01 && *v < 0.55,
        None => false,
    }
}
