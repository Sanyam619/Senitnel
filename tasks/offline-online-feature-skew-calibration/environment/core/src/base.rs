use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

#[derive(Clone, Debug)]
pub struct Row {
    pub idx: u32,
    pub state: String,
    pub tip: String,
}

pub type FeatMap = BTreeMap<String, f64>;

pub fn read_journal(path: &Path) -> Vec<Row> {
    let text = fs::read_to_string(path).unwrap_or_default();
    let mut out = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let idx = extract_u32(line, "idx").unwrap_or(0);
        let state = extract_str(line, "state").unwrap_or_default();
        let tip = extract_str(line, "tip").unwrap_or_default();
        out.push(Row { idx, state, tip });
    }
    out
}

pub fn offline_means(path: &Path) -> FeatMap {
    let text = fs::read_to_string(path).unwrap_or_default();
    let mut sums: BTreeMap<String, f64> = BTreeMap::new();
    let mut n = 0u64;
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        n += 1;
        for key in ["f_amt", "f_age", "f_zip", "f_chn", "f_risk"] {
            if let Some(v) = extract_f64(line, key) {
                *sums.entry(key.to_string()).or_insert(0.0) += v;
            }
        }
    }
    let mut out = FeatMap::new();
    if n == 0 {
        return out;
    }
    for (k, s) in sums {
        out.insert(k, s / n as f64);
    }
    out
}

pub fn read_tip_means(path: &Path) -> FeatMap {
    let text = fs::read_to_string(path).unwrap_or_default();
    let mut out = FeatMap::new();
    for key in ["f_amt", "f_age", "f_zip", "f_chn", "f_risk"] {
        // means object is nested; match "key": number anywhere after "means".
        if let Some(v) = extract_f64(&text, key) {
            out.insert(key.to_string(), v);
        }
    }
    out
}

pub fn read_selection(path: &Path) -> String {
    let text = fs::read_to_string(path).unwrap_or_default();
    for line in text.lines() {
        let line = line.trim();
        if let Some(rest) = line.strip_prefix("selection") {
            let rest = rest.trim_start();
            if let Some(rest) = rest.strip_prefix('=') {
                return rest.trim().trim_matches('"').to_string();
            }
        }
    }
    String::new()
}

pub fn extract_u32(line: &str, key: &str) -> Option<u32> {
    let pat = format!("\"{key}\"");
    let i = line.find(&pat)?;
    let rest = &line[i + pat.len()..];
    let rest = rest.trim_start().trim_start_matches(':').trim_start();
    let mut num = String::new();
    for c in rest.chars() {
        if c.is_ascii_digit() {
            num.push(c);
        } else if !num.is_empty() {
            break;
        }
    }
    num.parse().ok()
}

pub fn extract_str(line: &str, key: &str) -> Option<String> {
    let pat = format!("\"{key}\"");
    let i = line.find(&pat)?;
    let rest = &line[i + pat.len()..];
    let rest = rest.trim_start().trim_start_matches(':').trim_start();
    if !rest.starts_with('"') {
        return None;
    }
    let rest = &rest[1..];
    let end = rest.find('"')?;
    Some(rest[..end].to_string())
}

pub fn extract_f64(line: &str, key: &str) -> Option<f64> {
    let pat = format!("\"{key}\"");
    let i = line.find(&pat)?;
    let rest = &line[i + pat.len()..];
    let rest = rest.trim_start().trim_start_matches(':').trim_start();
    let mut num = String::new();
    for c in rest.chars() {
        if c.is_ascii_digit() || c == '-' || c == '+' || c == '.' || c == 'e' || c == 'E' {
            num.push(c);
        } else if !num.is_empty() {
            break;
        }
    }
    num.parse().ok()
}

pub fn sigmoid(x: f64) -> f64 {
    if x >= 0.0 {
        let z = (-x).exp();
        1.0 / (1.0 + z)
    } else {
        let z = x.exp();
        z / (1.0 + z)
    }
}

pub fn cal_term(means: &FeatMap, offline: &FeatMap) -> f64 {
    let weights = [
        ("f_amt", 1.0),
        ("f_age", -0.8),
        ("f_zip", 12.0),
        ("f_chn", 0.7),
        ("f_risk", -0.9),
    ];
    let mut t = 0.0;
    for (k, w) in weights {
        let m = means.get(k).copied().unwrap_or(0.0);
        let o = offline.get(k).copied().unwrap_or(0.0);
        t += w * (m - o);
    }
    t
}

pub fn auc(pairs: &[(f64, i32)]) -> f64 {
    let pos: Vec<f64> = pairs.iter().filter(|(_, y)| *y == 1).map(|(p, _)| *p).collect();
    let neg: Vec<f64> = pairs.iter().filter(|(_, y)| *y == 0).map(|(p, _)| *p).collect();
    if pos.is_empty() || neg.is_empty() {
        return 0.5;
    }
    let mut wins = 0.0;
    for p in &pos {
        for n in &neg {
            if p > n {
                wins += 1.0;
            } else if (p - n).abs() < 1e-15 {
                wins += 0.5;
            }
        }
    }
    wins / (pos.len() as f64 * neg.len() as f64)
}

pub fn brier(pairs: &[(f64, i32)]) -> f64 {
    if pairs.is_empty() {
        return 0.0;
    }
    let s: f64 = pairs.iter().map(|(p, y)| (p - f64::from(*y)).powi(2)).sum();
    s / pairs.len() as f64
}
