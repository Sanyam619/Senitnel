use std::fs;
use std::path::{Path, PathBuf};

pub struct ChanSet {
    pub cols: Vec<(String, f64)>,
    pub obs: f64,
}

impl ChanSet {
    pub fn at(&self, key: &str) -> Option<f64> {
        self.cols.iter().find(|(k, _)| k == key).map(|(_, v)| *v)
    }
}

pub struct SliceFixture {
    pub id: String,
    pub seq: i64,
    pub a: ChanSet,
    pub q: ChanSet,
}

pub struct JournalRow {
    pub tip: String,
    pub epoch: i64,
    pub sealed: bool,
    pub propensity: String,
}

pub struct TipPick {
    pub tip: String,
    pub epoch: i64,
    pub propensity: String,
}

pub struct DataPaths {
    pub outcomes: PathBuf,
    pub journal: PathBuf,
    pub retired: PathBuf,
    pub calib_pref: PathBuf,
}

pub fn data_paths(root: &Path) -> DataPaths {
    DataPaths {
        outcomes: root.join("outcomes"),
        journal: root.join("feature_registry").join("tip_journal.jsonl"),
        retired: root.join("feature_registry").join("retired_tips.jsonl"),
        calib_pref: root
            .parent()
            .map(|p| p.join("calib").join("trial_pref.toml"))
            .unwrap_or_else(|| PathBuf::from("calib/trial_pref.toml")),
    }
}

pub fn read_map(path: &Path) -> Vec<(String, String)> {
    let text = fs::read_to_string(path).unwrap_or_default();
    let mut out = Vec::new();
    for chunk in text.split('{') {
        let name = extract_str(chunk, "name");
        let column = extract_str(chunk, "column");
        if let (Some(n), Some(c)) = (name, column) {
            out.push((n, c));
        }
    }
    out
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
            propensity: extract_str(line, "propensity")
                .unwrap_or_else(|| "surface".to_string()),
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
                a: ChanSet {
                    cols: keyed_cols(&text, "auuc_"),
                    obs: extract_f64(&text, "auuc_obs").unwrap_or(0.0),
                },
                q: ChanSet {
                    cols: keyed_cols(&text, "qini_"),
                    obs: extract_f64(&text, "qini_obs").unwrap_or(0.0),
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
        if !key.starts_with("col_") {
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
