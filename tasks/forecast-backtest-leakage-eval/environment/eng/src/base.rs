use std::fs;
use std::path::{Path, PathBuf};

pub struct WindowFixture {
    pub id: String,
    pub seq: i64,
    pub smape_causal: f64,
    pub mase_causal: f64,
    pub smape_leak: f64,
    pub mase_leak: f64,
}

pub struct JournalRow {
    pub tip: String,
    pub epoch: i64,
    pub sealed: bool,
    pub horizon: i64,
    pub scaler: String,
    pub shift: f64,
}

pub struct TipPick {
    pub tip: String,
    pub epoch: i64,
    pub horizon: i64,
    pub scaler: String,
    pub shift: f64,
}

pub fn read_journal(path: &Path) -> Vec<JournalRow> {
    let text = fs::read_to_string(path).unwrap_or_default();
    let mut rows = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        rows.push(JournalRow {
            tip: extract_str(line, "tip").unwrap_or_default(),
            epoch: extract_i64(line, "epoch").unwrap_or(0),
            sealed: extract_bool(line, "sealed").unwrap_or(false),
            horizon: extract_i64(line, "horizon").unwrap_or(0),
            scaler: extract_str(line, "scaler").unwrap_or_else(|| "global".to_string()),
            shift: extract_f64(line, "shift").unwrap_or(0.0),
        });
    }
    rows
}

pub fn read_retired(path: &Path) -> Vec<String> {
    let text = fs::read_to_string(path).unwrap_or_default();
    let mut out = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        if let Some(tip) = extract_str(line, "tip") {
            if !tip.is_empty() {
                out.push(tip);
            }
        }
    }
    out
}

pub fn read_windows(dir: &Path) -> Vec<WindowFixture> {
    let mut rows = Vec::new();
    if let Ok(rd) = fs::read_dir(dir) {
        for ent in rd.flatten() {
            let p = ent.path();
            if p.extension().and_then(|s| s.to_str()) != Some("json") {
                continue;
            }
            let text = fs::read_to_string(&p).unwrap_or_default();
            let id = extract_str(&text, "id").unwrap_or_else(|| {
                p.file_stem()
                    .and_then(|s| s.to_str())
                    .unwrap_or("unknown")
                    .to_string()
            });
            rows.push(WindowFixture {
                id,
                seq: extract_i64(&text, "seq").unwrap_or(0),
                smape_causal: extract_f64(&text, "smape_causal").unwrap_or(0.0),
                mase_causal: extract_f64(&text, "mase_causal").unwrap_or(0.0),
                smape_leak: extract_f64(&text, "smape_leak").unwrap_or(0.0),
                mase_leak: extract_f64(&text, "mase_leak").unwrap_or(0.0),
            });
        }
    }
    rows.sort_by_key(|r| r.seq);
    rows
}

fn extract_str(text: &str, key: &str) -> Option<String> {
    let pat = format!("\"{}\"", key);
    let idx = text.find(&pat)?;
    let after = &text[idx + pat.len()..];
    let colon = after.find(':')?;
    let rest = after[colon + 1..].trim();
    if let Some(rest) = rest.strip_prefix('"') {
        let end = rest.find('"')?;
        return Some(rest[..end].to_string());
    }
    None
}

fn extract_scalar<'a>(text: &'a str, key: &str) -> Option<&'a str> {
    let pat = format!("\"{}\"", key);
    let idx = text.find(&pat)?;
    let after = &text[idx + pat.len()..];
    let colon = after.find(':')?;
    let rest = after[colon + 1..].trim_start();
    let end = rest.find([',', '}', '\n']).unwrap_or(rest.len());
    Some(rest[..end].trim())
}

fn extract_f64(text: &str, key: &str) -> Option<f64> {
    extract_scalar(text, key)?.parse().ok()
}

fn extract_i64(text: &str, key: &str) -> Option<i64> {
    extract_scalar(text, key)?.parse().ok()
}

fn extract_bool(text: &str, key: &str) -> Option<bool> {
    match extract_scalar(text, key)? {
        "true" => Some(true),
        "false" => Some(false),
        _ => None,
    }
}

pub struct DataPaths {
    pub journal: PathBuf,
    pub retired: PathBuf,
    pub series: PathBuf,
    pub calib_pref: PathBuf,
}

pub fn data_paths(root: &Path) -> DataPaths {
    DataPaths {
        journal: root.join("feature_registry").join("tip_journal.jsonl"),
        retired: root.join("feature_registry").join("retired_tips.jsonl"),
        series: root.join("series"),
        calib_pref: root
            .parent()
            .map(|p| p.join("calib").join("trial_pref.toml"))
            .unwrap_or_else(|| PathBuf::from("calib/trial_pref.toml")),
    }
}
