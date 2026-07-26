use std::fs;
use std::path::Path;

/// Trace stride reader for calib/trace_pref.toml — unused by graded emit.
pub fn dial_p(root: &Path) -> u32 {
    let text = fs::read_to_string(root.join("calib/trace_pref.toml")).unwrap_or_default();
    for line in text.lines() {
        let line = line.trim();
        if let Some(rest) = line.strip_prefix("stride") {
            let rest = rest.trim_start().trim_start_matches('=').trim();
            if let Ok(v) = rest.parse::<u32>() {
                return v;
            }
        }
    }
    1
}
