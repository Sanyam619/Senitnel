use std::fs;
use std::path::{Path, PathBuf};

pub struct TipPick {
    pub tip: String,
    pub epoch: i64,
    pub capacity: f64,
}

pub struct JournalRow {
    pub tip: String,
    pub epoch: i64,
    pub capacity: f64,
    pub sealed: bool,
}

pub struct ScenarioRow {
    pub id: String,
    pub mode: String,
    pub token_scores: Vec<f64>,
    pub base_nll: f64,
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
            capacity: extract_f64(line, "capacity").unwrap_or(1.0),
            sealed: extract_bool(line, "sealed").unwrap_or(false),
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

pub fn read_live_cap(path: &Path) -> f64 {
    let text = fs::read_to_string(path).unwrap_or_default();
    for line in text.lines() {
        let line = line.trim();
        if let Some(rest) = line.strip_prefix("capacity") {
            let v = rest.split('=').nth(1).unwrap_or("").trim();
            return v.parse().unwrap_or(1.0);
        }
    }
    1.0
}

pub fn read_schedule(path: &Path, cap: f64) -> (f64, f64) {
    let text = fs::read_to_string(path).unwrap_or_default();
    let key = format!("{:.2}", cap);
    let pat = format!("\"{}\"", key);
    let Some(idx) = text.find(&pat) else {
        return (1.0, 8.0);
    };
    let after = &text[idx..];
    let shallow = extract_f64(after, "shallow").unwrap_or(1.0);
    let deep = extract_f64(after, "deep").unwrap_or(8.0);
    (shallow, deep)
}

pub fn load_scenarios(dir: &Path) -> Vec<ScenarioRow> {
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
            let mode = extract_str(&text, "mode").unwrap_or_else(|| "cold".to_string());
            let token_scores = extract_f64_array(&text, "token_scores");
            let base_nll = extract_f64(&text, "base_nll").unwrap_or(1.0);
            rows.push(ScenarioRow {
                id,
                mode,
                token_scores,
                base_nll,
            });
        }
    }
    rows.sort_by(|a, b| a.id.cmp(&b.id));
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

fn extract_f64_array(text: &str, key: &str) -> Vec<f64> {
    let pat = format!("\"{}\"", key);
    let Some(idx) = text.find(&pat) else {
        return Vec::new();
    };
    let after = &text[idx + pat.len()..];
    let Some(start) = after.find('[') else {
        return Vec::new();
    };
    let Some(end) = after[start..].find(']') else {
        return Vec::new();
    };
    let body = &after[start + 1..start + end];
    body.split(',')
        .filter_map(|p| p.trim().parse::<f64>().ok())
        .collect()
}

pub struct DataPaths {
    pub journal: PathBuf,
    pub retired: PathBuf,
    pub live: PathBuf,
    pub schedule: PathBuf,
    pub eval: PathBuf,
}

pub fn data_paths(root: &Path) -> DataPaths {
    DataPaths {
        journal: root.join("routers").join("tip_journal.jsonl"),
        retired: root.join("routers").join("retired_tips.jsonl"),
        live: root.join("routers").join("live.toml"),
        schedule: root.join("routers").join("depth_schedule.json"),
        eval: root.join("eval"),
    }
}
