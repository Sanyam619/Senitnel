pub fn gate_y(
    accs: &[f64],
    forgettings: &[f64],
    fracs: &[f64],
    actives: &[bool],
    rows_ok: bool,
) -> bool {
    let _ = (forgettings, fracs, actives, rows_ok);
    match accs.last() {
        Some(v) => *v > 0.70 && *v < 0.85,
        None => false,
    }
}
