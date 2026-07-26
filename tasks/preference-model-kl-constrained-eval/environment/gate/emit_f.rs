pub fn gate_y(wins: &[f64], kls: &[f64], betas: &[f64], epochs: &[i64], rows_ok: bool) -> bool {
    let _ = (kls, betas, epochs, rows_ok);
    !wins.is_empty() && wins.iter().all(|w| *w >= 0.60)
}
