use std::collections::HashMap;
use std::fs;
use std::path::Path;

pub fn alias_map() -> HashMap<String, String> {
    let path = Path::new("/app/config/aliases.toml");
    let mut out = HashMap::new();
    if !path.exists() {
        return out;
    }
    let body = fs::read_to_string(path).unwrap_or_default();
    let mut in_map = false;
    for line in body.lines() {
        let line = line.trim();
        if line == "[map]" {
            in_map = true;
            continue;
        }
        if line.starts_with('[') {
            in_map = false;
        }
        if !in_map || !line.contains('=') {
            continue;
        }
        let (k, v) = line.split_once('=').unwrap();
        let key = k.trim().trim_matches('"').to_string();
        let val = v.trim().trim_matches('"').to_string();
        if !key.is_empty() && !val.is_empty() {
            out.insert(key, val);
        }
    }
    out
}

pub fn resolve_name(raw: &str) -> String {
    let table = alias_map();
    table.get(raw).cloned().unwrap_or_else(|| raw.to_string())
}

pub fn resolve_list(values: &[String]) -> Vec<String> {
    values.iter().map(|v| resolve_name(v)).collect()
}
