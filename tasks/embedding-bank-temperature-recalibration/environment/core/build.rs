use std::env;
use std::fs;
use std::path::Path;

fn eval_selection(path: &Path) -> String {
    let Ok(text) = fs::read_to_string(path) else {
        return String::new();
    };
    for raw in text.lines() {
        let line = raw.trim();
        if line.starts_with('#') || line.is_empty() {
            continue;
        }
        if let Some(pos) = line.find("selection") {
            let after = line[pos + "selection".len()..].trim_start();
            if let Some(rest) = after.strip_prefix('=') {
                return rest.trim().trim_matches('"').to_string();
            }
        }
    }
    String::new()
}

fn bind_receipt(path: &Path) -> String {
    fs::read_to_string(path)
        .unwrap_or_default()
        .lines()
        .next()
        .unwrap_or("")
        .trim()
        .to_string()
}

fn extract_quoted(line: &str, key: &str) -> Option<String> {
    let needle = format!("\"{key}\"");
    let i = line.find(&needle)?;
    let mut rest = line[i + needle.len()..].trim_start();
    if !rest.starts_with(':') {
        return None;
    }
    rest = rest[1..].trim_start();
    let rest = rest.strip_prefix('"')?;
    let end = rest.find('"')?;
    Some(rest[..end].to_string())
}

fn extract_idx(line: &str) -> u32 {
    extract_quoted(line, "idx")
        .and_then(|s| s.parse().ok())
        .or_else(|| {
            let key = "\"idx\"";
            let i = line.find(key)?;
            let rest = &line[i + key.len()..];
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
        })
        .unwrap_or(0)
}

fn resolved_tip(journal: &Path, retired: &Path) -> String {
    let mut banned = std::collections::HashSet::new();
    if let Ok(body) = fs::read_to_string(retired) {
        for line in body.lines() {
            if let Some(t) = extract_quoted(line, "tip") {
                banned.insert(t);
            }
        }
    }
    let mut best = (0u32, String::new());
    if let Ok(body) = fs::read_to_string(journal) {
        for line in body.lines() {
            let line = line.trim();
            if line.is_empty() {
                continue;
            }
            if extract_quoted(line, "state").as_deref() != Some("durable") {
                continue;
            }
            let Some(tip) = extract_quoted(line, "tip") else {
                continue;
            };
            if banned.contains(&tip) {
                continue;
            }
            let idx = extract_idx(line);
            if idx >= best.0 {
                best = (idx, tip);
            }
        }
    }
    best.1
}

fn main() {
    let here = env::var("CARGO_MANIFEST_DIR").unwrap_or_default();
    let base = Path::new(&here);
    let pref = base.join("../../calib/trial_pref.toml");
    let accept = base.join("../../calib/tip_bind.accept");
    let journal = base.join("../../data/feature_registry/tip_journal.jsonl");
    let retired = base.join("../../data/feature_registry/retired_tips.jsonl");
    println!("cargo:rerun-if-changed={}", pref.display());
    println!("cargo:rerun-if-changed={}", accept.display());
    println!("cargo:rerun-if-changed={}", journal.display());
    println!("cargo:rerun-if-changed={}", retired.display());
    println!("cargo:rerun-if-changed=seeds/lens_seed.rs.in");
    println!("cargo:rerun-if-changed=seeds/weave_seed.rs.in");
    println!("cargo:rerun-if-changed=src/lens.rs");
    println!("cargo:rerun-if-changed=src/weave.rs");

    let serving = eval_selection(&pref) == "serving";
    let tip = resolved_tip(&journal, &retired);
    let bound = !tip.is_empty() && bind_receipt(&accept) == tip;
    if !(serving && bound) {
        for (seed, dest) in [
            ("seeds/lens_seed.rs.in", "src/lens.rs"),
            ("seeds/weave_seed.rs.in", "src/weave.rs"),
        ] {
            let body = fs::read_to_string(base.join(seed)).unwrap_or_default();
            if body.is_empty() {
                continue;
            }
            let cur = fs::read_to_string(base.join(dest)).unwrap_or_default();
            if cur != body {
                let _ = fs::write(base.join(dest), &body);
            }
        }
    }
}
