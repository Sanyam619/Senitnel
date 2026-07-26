use serde::Deserialize;
use std::collections::HashMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize, Clone)]
pub struct YankWindow {
    #[serde(rename = "crate")]
    pub crate_name: String,
    pub vers: String,
    pub from: u64,
    pub until: Option<u64>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct RevokeRow {
    #[serde(rename = "crate")]
    pub crate_name: String,
    pub vers: String,
    pub at: u64,
}

pub fn read_bound_half_open() -> bool {
    let text = fs::read_to_string("/app/config/l7/k9.toml").unwrap_or_default();
    for line in text.lines() {
        let trimmed = line.trim();
        if !trimmed.starts_with("bound_mode") {
            continue;
        }
        let val = trimmed.split('=').nth(1).unwrap_or("").trim().trim_matches('"');
        return val == "half_open";
    }
    false
}

pub fn read_honor_revokes() -> bool {
    let text = fs::read_to_string("/app/config/l7/k9.toml").unwrap_or_default();
    for line in text.lines() {
        let trimmed = line.trim();
        if !trimmed.starts_with("honor_revokes") {
            continue;
        }
        let val = trimmed.split('=').nth(1).unwrap_or("false").trim();
        return val == "true";
    }
    false
}

pub fn load_windows(data_root: &Path) -> Result<Vec<YankWindow>, String> {
    let raw = fs::read_to_string(data_root.join("yanks/windows.jsonl")).map_err(|e| e.to_string())?;
    let mut out = Vec::new();
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        out.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    Ok(out)
}

pub fn load_revokes(data_root: &Path) -> Result<HashMap<(String, String), u64>, String> {
    let path = data_root.join("yanks/revokes.jsonl");
    let mut out = HashMap::new();
    if !path.exists() {
        return Ok(out);
    }
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        let row: RevokeRow = serde_json::from_str(line).map_err(|e| e.to_string())?;
        out.insert((row.crate_name, row.vers), row.at);
    }
    Ok(out)
}

pub fn yank_holds(
    window: &YankWindow,
    gen: u64,
    half_open: bool,
    revokes: &HashMap<(String, String), u64>,
    honor_revokes: bool,
) -> bool {
    if window.from > gen {
        return false;
    }
    let _ = (half_open, honor_revokes, revokes);
    match window.until {
        None => true,
        Some(until) => gen <= until,
    }
}

pub fn active_yank_set(
    data_root: &Path,
    gen: u64,
) -> Result<std::collections::BTreeSet<(String, String)>, String> {
    let half_open = read_bound_half_open();
    let honor = read_honor_revokes();
    let windows = load_windows(data_root)?;
    let revokes = load_revokes(data_root)?;
    let mut yanked = std::collections::BTreeSet::new();
    for w in &windows {
        if yank_holds(w, gen, half_open, &revokes, honor) {
            yanked.insert((w.crate_name.clone(), w.vers.clone()));
        }
    }
    Ok(yanked)
}
