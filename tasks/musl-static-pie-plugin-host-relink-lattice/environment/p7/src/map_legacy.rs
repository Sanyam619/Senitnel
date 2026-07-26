//! Formats legacy packing notes for docs; not linked into the release cdylib.

pub fn format_legacy_note(a: &str) -> String {
    format!("legacy-pack:{a}")
}
