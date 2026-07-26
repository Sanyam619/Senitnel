//! Optional dry-run preview of expand input shapes for runbook smoke.

pub fn preview_line(name: &str, value: &str) -> String {
    format!("{name}={value}")
}

pub fn recount(pairs: &[(&str, &str)]) -> usize {
    pairs.len()
}
