//! Dry-run metadata printer for local docs. Not consumed by abi_probe.

pub fn preview_line(name: &str, value: &str) -> String {
    format!("{name}={value}")
}

pub fn recount(pairs: &[(&str, &str)]) -> usize {
    pairs.len()
}
