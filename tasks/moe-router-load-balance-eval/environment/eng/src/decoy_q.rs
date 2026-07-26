/// Decorative histogram string for operator logs.
pub fn hist_q(vals: &[f64]) -> String {
    vals.iter()
        .map(|v| format!("{:.2}", v))
        .collect::<Vec<_>>()
        .join(",")
}
