use std::fs;
use std::path::Path;

pub fn dial_stride(root: &Path) -> u32 {
    let path = root.join("calib/trace_pref.toml");
    let text = fs::read_to_string(path).unwrap_or_default();
    for line in text.lines() {
        let line = line.trim();
        if let Some(rest) = line.strip_prefix("stride") {
            let rest = rest.trim_start().trim_start_matches('=').trim();
            if let Ok(v) = rest.parse::<u32>() {
                return v;
            }
        }
    }
    0
}
