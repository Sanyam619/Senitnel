//! Mono tag strings retained for documentation examples.

pub fn mono_label() -> &'static str {
    "FLUX_MONO_1"
}

pub fn alias(stem: &str) -> String {
    format!("MONO_{stem}")
}
