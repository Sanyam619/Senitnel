pub fn gate_y(shares: &[f64], flags: &[bool], rows_ok: bool) -> bool {
    let _ = (flags, rows_ok);
    if shares.is_empty() {
        return false;
    }
    let mx = shares.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let mn = shares.iter().cloned().fold(f64::INFINITY, f64::min);
    (mx - mn) < 0.02
}
