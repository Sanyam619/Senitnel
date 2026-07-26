use std::fs;
use std::path::{Path, PathBuf};

#[derive(Clone)]
pub struct TipRow {
    pub tip: String,
    pub epoch: i64,
    pub beta: f64,
    pub sealed: bool,
}

pub struct Paths {
    pub prefs: PathBuf,
    pub policy: PathBuf,
    pub reference: PathBuf,
    pub journal: PathBuf,
    pub retired: PathBuf,
    pub live: PathBuf,
    pub durable: PathBuf,
}

pub fn data_paths(root: &Path) -> Paths {
    Paths {
        prefs: root.join("prefs"),
        policy: root.join("policy"),
        reference: root.join("ref"),
        journal: root.join("tips").join("tip_journal.jsonl"),
        retired: root.join("tips").join("retired_tips.jsonl"),
        live: root.join("tips").join("live.toml"),
        durable: root.join("tips").join("durable.toml"),
    }
}

fn field(line: &str, key: &str) -> Option<String> {
    let pat = format!("\"{}\"", key);
    let idx = line.find(&pat)?;
    let after = &line[idx + pat.len()..];
    let colon = after.find(':')?;
    let rest = after[colon + 1..].trim_start();
    if let Some(rest) = rest.strip_prefix('"') {
        let end = rest.find('"')?;
        return Some(rest[..end].to_string());
    }
    let end = rest.find([',', '}']).unwrap_or(rest.len());
    Some(rest[..end].trim().to_string())
}

pub fn read_journal(path: &Path) -> Vec<TipRow> {
    let Ok(text) = fs::read_to_string(path) else {
        return Vec::new();
    };
    let mut out = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let tip = match field(line, "tip") {
            Some(v) => v,
            None => continue,
        };
        let epoch = field(line, "epoch")
            .and_then(|v| v.parse().ok())
            .unwrap_or(0);
        let beta = field(line, "beta")
            .and_then(|v| v.parse().ok())
            .unwrap_or(1.0);
        let sealed = field(line, "sealed").map(|v| v == "true").unwrap_or(false);
        out.push(TipRow {
            tip,
            epoch,
            beta,
            sealed,
        });
    }
    out
}

pub fn read_retired(path: &Path) -> Vec<String> {
    let Ok(text) = fs::read_to_string(path) else {
        return Vec::new();
    };
    let mut out = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        if let Some(tip) = field(line, "tip") {
            out.push(tip);
        }
    }
    out
}

pub fn read_toml_f64(path: &Path, key: &str) -> Option<f64> {
    let text = fs::read_to_string(path).ok()?;
    for line in text.lines() {
        let line = line.trim();
        if let Some(rest) = line.strip_prefix(key) {
            let rest = rest.trim_start();
            if let Some(v) = rest.strip_prefix('=') {
                return v.trim().parse().ok();
            }
        }
    }
    None
}

pub fn list_slice_ids(prefs: &Path) -> Vec<String> {
    let mut ids = Vec::new();
    let Ok(rd) = fs::read_dir(prefs) else {
        return ids;
    };
    for ent in rd.flatten() {
        let p = ent.path();
        if p.extension().and_then(|e| e.to_str()) != Some("json") {
            continue;
        }
        if let Some(stem) = p.file_stem().and_then(|s| s.to_str()) {
            ids.push(stem.to_string());
        }
    }
    ids.sort();
    ids
}

fn parse_number_array(text: &str, key: &str) -> Vec<f64> {
    let pat = format!("\"{}\"", key);
    let Some(idx) = text.find(&pat) else {
        return Vec::new();
    };
    let after = &text[idx + pat.len()..];
    let Some(br) = after.find('[') else {
        return Vec::new();
    };
    let mut depth = 0i32;
    let mut end = None;
    for (i, ch) in after[br..].char_indices() {
        match ch {
            '[' => depth += 1,
            ']' => {
                depth -= 1;
                if depth == 0 {
                    end = Some(br + i);
                    break;
                }
            }
            _ => {}
        }
    }
    let Some(end) = end else {
        return Vec::new();
    };
    let body = &after[br + 1..end];
    let mut out = Vec::new();
    for tok in body.split(',') {
        let t = tok.trim();
        if t.is_empty() {
            continue;
        }
        if let Ok(v) = t.parse::<f64>() {
            out.push(v);
        }
    }
    out
}

fn parse_nested_probs(text: &str) -> Vec<Vec<f64>> {
    let Some(idx) = text.find("\"probs\"") else {
        return Vec::new();
    };
    let after = &text[idx..];
    let Some(br) = after.find('[') else {
        return Vec::new();
    };
    let mut depth = 0i32;
    let mut end = None;
    for (i, ch) in after[br..].char_indices() {
        match ch {
            '[' => depth += 1,
            ']' => {
                depth -= 1;
                if depth == 0 {
                    end = Some(br + i);
                    break;
                }
            }
            _ => {}
        }
    }
    let Some(end) = end else {
        return Vec::new();
    };
    let body = &after[br + 1..end];
    let mut rows = Vec::new();
    let mut i = 0;
    let bytes = body.as_bytes();
    while i < bytes.len() {
        if bytes[i] == b'[' {
            let start = i + 1;
            let mut j = start;
            while j < bytes.len() && bytes[j] != b']' {
                j += 1;
            }
            let row_txt = &body[start..j];
            let mut row = Vec::new();
            for tok in row_txt.split(',') {
                let t = tok.trim();
                if t.is_empty() {
                    continue;
                }
                if let Ok(v) = t.parse::<f64>() {
                    row.push(v);
                }
            }
            rows.push(row);
            i = j + 1;
        } else {
            i += 1;
        }
    }
    rows
}

pub struct SlicePack {
    pub id: String,
    pub margins: Vec<f64>,
    pub cand: Vec<Vec<f64>>,
    pub reference: Vec<Vec<f64>>,
}

pub fn load_slices(paths: &Paths) -> Vec<SlicePack> {
    let ids = list_slice_ids(&paths.prefs);
    let mut out = Vec::new();
    for id in ids {
        let pref_text = fs::read_to_string(paths.prefs.join(format!("{id}.json"))).unwrap_or_default();
        let pol_text = fs::read_to_string(paths.policy.join(format!("{id}.json"))).unwrap_or_default();
        let ref_text =
            fs::read_to_string(paths.reference.join(format!("{id}.json"))).unwrap_or_default();
        // margins from pairs[].m
        let mut margins = Vec::new();
        let mut search = pref_text.as_str();
        while let Some(idx) = search.find("\"m\"") {
            let after = &search[idx + 3..];
            if let Some(colon) = after.find(':') {
                let rest = after[colon + 1..].trim_start();
                let end = rest.find([',', '}']).unwrap_or(rest.len());
                if let Ok(v) = rest[..end].trim().parse::<f64>() {
                    margins.push(v);
                }
            }
            search = &after[1..];
        }
        if margins.is_empty() {
            margins = parse_number_array(&pref_text, "margins");
        }
        out.push(SlicePack {
            id,
            margins,
            cand: parse_nested_probs(&pol_text),
            reference: parse_nested_probs(&ref_text),
        });
    }
    out
}
