use std::{fs, path::Path};

pub fn u64v(dir: &Path, file: &str, key: &str) -> Result<u64, String> {
    let raw = fs::read_to_string(dir.join(file)).map_err(|e| format!("read {file}: {e}"))?;
    for line in raw.lines() {
        if let Some(rest) = line.trim().strip_prefix(&format!("{key} = ")) {
            return rest
                .trim_matches('"')
                .parse()
                .map_err(|_| format!("bad {key}"));
        }
    }
    Err(format!("missing {key}"))
}

pub fn boolv(dir: &Path, file: &str, key: &str) -> Result<bool, String> {
    let raw = fs::read_to_string(dir.join(file)).map_err(|e| format!("read {file}: {e}"))?;
    for line in raw.lines() {
        if let Some(rest) = line.trim().strip_prefix(&format!("{key} = ")) {
            return match rest.trim() {
                "true" => Ok(true),
                "false" => Ok(false),
                _ => Err(format!("bad {key}")),
            };
        }
    }
    Err(format!("missing {key}"))
}

pub fn strv(dir: &Path, file: &str, key: &str) -> Result<String, String> {
    let raw = fs::read_to_string(dir.join(file)).map_err(|e| format!("read {file}: {e}"))?;
    for line in raw.lines() {
        if let Some(rest) = line.trim().strip_prefix(&format!("{key} = ")) {
            return Ok(rest.trim().trim_matches('"').to_string());
        }
    }
    Err(format!("missing {key}"))
}
