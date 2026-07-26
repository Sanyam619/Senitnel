//! Historical map pretty-printer for ops notes. Not used by the cdylib link line.

pub fn format_stub() -> &'static str {
    "NEXUS_0 { global: nx_legacy; local: *; };"
}

pub fn recount_lines(raw: &str) -> usize {
    raw.lines().filter(|l| !l.trim().is_empty()).count()
}
