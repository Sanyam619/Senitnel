use std::fs;
use std::path::{Path, PathBuf};

pub struct TaskFixture {
    pub id: String,
    pub seq: i64,
    pub stratum: String,
    pub base: f64,
    pub peak: f64,
    pub durable_hit: f64,
    pub overflow_hit: f64,
}

pub struct JournalRow {
    pub tip: String,
    pub epoch: i64,
    pub replay_frac: f64,
    pub sealed: bool,
}

pub struct HoldRow {
    pub id: String,
    pub op: String,
    pub epoch: i64,
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
        let replay_frac = extract_f64(line, "replay_frac").unwrap_or(0.0);
        let sealed = extract_bool(line, "sealed").unwrap_or(false);
        rows.push(JournalRow {
            tip,
            epoch,
            replay_frac,
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

pub fn read_ledger(path: &Path) -> Vec<HoldRow> {
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
        if !id.is_empty() {
            rows.push(HoldRow { id, op, epoch });
        }
    }
    rows
}

pub fn read_roster(path: &Path) -> Vec<String> {
    let text = fs::read_to_string(path).unwrap_or_default();
    let mut out = Vec::new();
    // Prefer JSON array under "held"
    if let Some(start) = text.find('[') {
        if let Some(end) = text[start..].find(']') {
            let body = &text[start + 1..start + end];
            for part in body.split(',') {
                let p = part.trim().trim_matches('"');
                if !p.is_empty() {
                    out.push(p.to_string());
                }
            }
        }
    }
    out
}

pub fn read_tasks(dir: &Path) -> Vec<TaskFixture> {
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
            let seq = extract_i64(&text, "seq").unwrap_or(0);
            let stratum = extract_str(&text, "stratum").unwrap_or_else(|| "s0".to_string());
            let base = extract_f64(&text, "base").unwrap_or(0.0);
            let peak = extract_f64(&text, "peak").unwrap_or(0.0);
            let durable_hit = extract_f64(&text, "durable_hit").unwrap_or(0.0);
            let overflow_hit = extract_f64(&text, "overflow_hit").unwrap_or(0.0);
            rows.push(TaskFixture {
                id,
                seq,
                stratum,
                base,
                peak,
                durable_hit,
                overflow_hit,
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
    pub mirror: PathBuf,
    pub live: PathBuf,
    pub ledger: PathBuf,
    pub roster: PathBuf,
    pub tasks: PathBuf,
}

pub fn data_paths(root: &Path) -> DataPaths {
    DataPaths {
        journal: root.join("replay").join("tip_journal.jsonl"),
        retired: root.join("replay").join("retired_tips.jsonl"),
        mirror: root.join("replay").join("durable.toml"),
        live: root.join("replay").join("live.toml"),
        ledger: root.join("replay").join("hold_ledger.jsonl"),
        roster: root.join("replay").join("roster.json"),
        tasks: root.join("tasks"),
    }
}

pub fn list_strata(tasks: &[TaskFixture]) -> Vec<String> {
    let mut out = Vec::new();
    for t in tasks {
        if !out.iter().any(|s| s == &t.stratum) {
            out.push(t.stratum.clone());
        }
    }
    out.sort();
    out
}
