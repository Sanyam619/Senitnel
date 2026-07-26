use std::fs;
use std::path::{Path, PathBuf};

pub struct ChanSet {
    pub cols: Vec<(String, f64)>,
    pub obs: f64,
    pub oracle: f64,
}

impl ChanSet {
    pub fn at(&self, key: &str) -> Option<f64> {
        self.cols.iter().find(|(k, _)| k == key).map(|(_, v)| *v)
    }
}

pub struct SliceFixture {
    pub id: String,
    pub seq: i64,
    pub der: ChanSet,
    pub jer: ChanSet,
}

pub struct JournalRow {
    pub tip: String,
    pub epoch: i64,
    pub sealed: bool,
    pub clustering: String,
}

pub struct TipPick {
    pub tip: String,
    pub epoch: i64,
}

pub struct MethodPick {
    pub tip: String,
    pub clustering: String,
}

pub struct DataPaths {
    pub audio: PathBuf,
    pub embed_journal: PathBuf,
    pub embed_retired: PathBuf,
    pub cluster_journal: PathBuf,
    pub cluster_retired: PathBuf,
}

pub fn data_paths(root: &Path) -> DataPaths {
    DataPaths {
        audio: root.join("audio"),
        embed_journal: root.join("embed_registry").join("tip_journal.jsonl"),
        embed_retired: root.join("embed_registry").join("retired_tips.jsonl"),
        cluster_journal: root.join("cluster_registry").join("tip_journal.jsonl"),
        cluster_retired: root.join("cluster_registry").join("retired_tips.jsonl"),
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
        rows.push(JournalRow {
            tip: extract_str(line, "tip").unwrap_or_default(),
            epoch: extract_i64(line, "epoch").unwrap_or(0),
            sealed: extract_bool(line, "sealed").unwrap_or(false),
            clustering: extract_str(line, "clustering")
                .unwrap_or_else(|| "spectral".to_string()),
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

pub fn read_slices(dir: &Path) -> Vec<SliceFixture> {
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
            rows.push(SliceFixture {
                id,
                seq: extract_i64(&text, "seq").unwrap_or(0),
                der: ChanSet {
                    cols: keyed_cols(&text, "der_"),
                    obs: extract_f64(&text, "der_obs").unwrap_or(0.0),
                    oracle: extract_f64(&text, "der_oracle").unwrap_or(0.0),
                },
                jer: ChanSet {
                    cols: keyed_cols(&text, "jer_"),
                    obs: extract_f64(&text, "jer_obs").unwrap_or(0.0),
                    oracle: extract_f64(&text, "jer_oracle").unwrap_or(0.0),
                },
            });
        }
    }
    rows.sort_by_key(|r| r.seq);
    rows
}

fn keyed_cols(text: &str, prefix: &str) -> Vec<(String, f64)> {
    let pat = format!("\"{}", prefix);
    let mut out = Vec::new();
    let mut from = 0usize;
    while let Some(rel) = text[from..].find(&pat) {
        let start = from + rel + pat.len();
        let Some(endq) = text[start..].find('"') else {
            break;
        };
        let key = text[start..start + endq].to_string();
        from = start + endq;
        if key == "obs" || key == "oracle" {
            continue;
        }
        let after = &text[from + 1..];
        let Some(colon) = after.find(':') else {
            continue;
        };
        let rest = after[colon + 1..].trim_start();
        let end = rest.find([',', '}', '\n']).unwrap_or(rest.len());
        if let Ok(v) = rest[..end].trim().parse::<f64>() {
            out.push((key, v));
        }
    }
    out.sort_by(|x, y| x.0.cmp(&y.0));
    out
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
