use std::fs;
use std::path::{Path, PathBuf};

pub struct TipSheet {
    pub tip_temp: f64,
    pub label: String,
    pub epoch: i64,
}

pub struct SliceRow {
    pub id: String,
    pub logits: Vec<f64>,
}

pub struct JournalRow {
    pub tip: String,
    pub epoch: i64,
    pub tip_temp: f64,
    pub sealed: bool,
}

pub fn read_tip(path: &Path) -> TipSheet {
    let text = fs::read_to_string(path).unwrap_or_default();
    let mut tip_temp = 1.0;
    let mut label = String::new();
    let mut epoch = 0i64;
    for line in text.lines() {
        let line = line.trim();
        if let Some(rest) = line.strip_prefix("tip_temp") {
            let v = rest.split('=').nth(1).unwrap_or("").trim();
            tip_temp = v.parse().unwrap_or(1.0);
        } else if let Some(rest) = line.strip_prefix("label") {
            let v = rest.split('=').nth(1).unwrap_or("").trim().trim_matches('"');
            label = v.to_string();
        } else if let Some(rest) = line.strip_prefix("epoch") {
            let v = rest.split('=').nth(1).unwrap_or("").trim();
            epoch = v.parse().unwrap_or(0);
        }
    }
    TipSheet {
        tip_temp,
        label,
        epoch,
    }
}

pub fn read_journal(path: &Path) -> Vec<JournalRow> {
    let text = fs::read_to_string(path).unwrap_or_default();
    let mut rows = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let tip = extract_str(line, "tip").unwrap_or_default();
        let epoch = extract_i64(line, "epoch").unwrap_or(0);
        let tip_temp = extract_f64(line, "tip_temp").unwrap_or(1.0);
        let sealed = extract_bool(line, "sealed").unwrap_or(false);
        rows.push(JournalRow {
            tip,
            epoch,
            tip_temp,
            sealed,
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

pub fn read_ledger(path: &Path) -> Vec<(String, String, i64)> {
    let text = fs::read_to_string(path).unwrap_or_default();
    let mut rows = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let id = extract_str(line, "id").unwrap_or_default();
        let op = extract_str(line, "op").unwrap_or_default();
        let epoch = extract_i64(line, "epoch").unwrap_or(0);
        if !id.is_empty() && !op.is_empty() {
            rows.push((id, op, epoch));
        }
    }
    rows
}

pub fn read_hold(path: &Path) -> Vec<String> {
    let text = fs::read_to_string(path).unwrap_or_else(|_| "{\"held\":[]}".into());
    let mut out = Vec::new();
    if let Some(start) = text.find('[') {
        if let Some(end) = text[start..].find(']') {
            let body = &text[start + 1..start + end];
            for part in body.split(',') {
                let t = part.trim().trim_matches('"').trim();
                if !t.is_empty() {
                    out.push(t.to_string());
                }
            }
        }
    }
    out
}

pub fn list_expert_ids(dir: &Path) -> Vec<String> {
    let mut ids = Vec::new();
    if let Ok(rd) = fs::read_dir(dir) {
        for ent in rd.flatten() {
            let p = ent.path();
            if p.extension().and_then(|s| s.to_str()) == Some("json") {
                if let Some(stem) = p.file_stem().and_then(|s| s.to_str()) {
                    ids.push(stem.to_string());
                }
            }
        }
    }
    ids.sort();
    ids
}

pub fn read_caps(dir: &Path, ids: &[String]) -> Vec<f64> {
    ids.iter()
        .map(|id| {
            let p = dir.join(format!("{}.json", id));
            let text = fs::read_to_string(&p).unwrap_or_default();
            extract_f64(&text, "capacity").unwrap_or(1.0)
        })
        .collect()
}

pub fn load_slices(dir: &Path) -> Vec<SliceRow> {
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
            let logits = extract_f64_array(&text, "logits");
            rows.push(SliceRow { id, logits });
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
    let end = rest
        .find([',', '}', '\n'])
        .unwrap_or(rest.len());
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
    pub mirror: PathBuf,
    pub live: PathBuf,
    pub roster: PathBuf,
    pub ledger: PathBuf,
    pub experts: PathBuf,
    pub eval: PathBuf,
}

pub fn data_paths(root: &Path) -> DataPaths {
    DataPaths {
        journal: root.join("routers").join("tip_journal.jsonl"),
        mirror: root.join("routers").join("durable.toml"),
        live: root.join("routers").join("live.toml"),
        roster: root.join("routers").join("hold.json"),
        ledger: root.join("routers").join("hold_ledger.jsonl"),
        experts: root.join("experts"),
        eval: root.join("eval"),
    }
}
