use std::fs;
use std::path::Path;

/// Trace stream shaping for the emitter's optional per-utterance trace.
pub struct Trace {
    pub stream: String,
    pub width: usize,
}

impl Default for Trace {
    fn default() -> Trace {
        Trace {
            stream: "off".to_string(),
            width: 4,
        }
    }
}

pub fn trace(root: &Path) -> Trace {
    let text = match fs::read_to_string(root.join("calib/trace_pref.toml")) {
        Ok(v) => v,
        Err(_) => return Trace::default(),
    };
    let mut held = Trace::default();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') || line.starts_with('[') {
            continue;
        }
        let Some((key, val)) = line.split_once('=') else {
            continue;
        };
        let val = val.trim().trim_matches('"');
        match key.trim() {
            "stream" => held.stream = val.to_string(),
            "width" => {
                if let Ok(v) = val.parse::<usize>() {
                    held.width = v;
                }
            }
            _ => {}
        }
    }
    held
}
