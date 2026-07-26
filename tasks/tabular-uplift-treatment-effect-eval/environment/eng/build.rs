use std::env;
use std::fs;
use std::path::{Path, PathBuf};

const PAIRS: [(&str, &str); 5] = [
    ("seeds/s1.rs.in", "seat/knit_b.rs"),
    ("seeds/s2.rs.in", "flag/xv_c.rs"),
    ("seeds/s3.rs.in", "mix/ward_d.rs"),
    ("seeds/s4.rs.in", "score/helm_e.rs"),
    ("seeds/s5.rs.in", "gate/emit_f.rs"),
];

fn kv_line(text: &str, key: &str) -> Option<String> {
    for line in text.lines() {
        let line = line.trim();
        if let Some(rest) = line.strip_prefix(key) {
            let rest = rest.trim_start();
            if let Some(v) = rest.strip_prefix('=') {
                return Some(v.trim().trim_matches('"').to_string());
            }
        }
    }
    None
}

fn section_kv(text: &str, section: &str, key: &str) -> Option<String> {
    let mut in_section = false;
    for line in text.lines() {
        let line = line.trim();
        if line.starts_with('[') && line.ends_with(']') {
            in_section = line == format!("[{section}]");
            continue;
        }
        if !in_section {
            continue;
        }
        if let Some(rest) = line.strip_prefix(key) {
            let rest = rest.trim_start();
            if let Some(v) = rest.strip_prefix('=') {
                return Some(v.trim().trim_matches('"').to_string());
            }
        }
    }
    None
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

fn retired_set(path: &Path) -> std::collections::HashSet<String> {
    let mut out = std::collections::HashSet::new();
    let Ok(text) = fs::read_to_string(path) else {
        return out;
    };
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        if let Some(tip) = field(line, "tip") {
            out.insert(tip);
        }
    }
    out
}

fn resolve(journal: &Path, retired: &Path) -> Option<(String, i64, String)> {
    let text = fs::read_to_string(journal).ok()?;
    let retired = retired_set(retired);
    let mut best: Option<(String, i64, String)> = None;
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let sealed = field(line, "sealed").map(|v| v == "true").unwrap_or(false);
        if !sealed {
            continue;
        }
        let tip = field(line, "tip")?;
        if retired.contains(&tip) {
            continue;
        }
        let epoch: i64 = field(line, "epoch").and_then(|v| v.parse().ok())?;
        let propensity = field(line, "propensity").unwrap_or_else(|| "surface".to_string());
        if best.as_ref().map(|(_, e, _)| epoch >= *e).unwrap_or(true) {
            best = Some((tip, epoch, propensity));
        }
    }
    best
}

fn seated(root: &Path) -> bool {
    let pref = root.join("calib").join("trial_pref.toml");
    let Ok(pref_text) = fs::read_to_string(&pref) else {
        return false;
    };
    if section_kv(&pref_text, "evaluation", "selection").as_deref() != Some("serving") {
        return false;
    }
    let accept = root.join("calib").join("tip_bind.accept");
    let Ok(text) = fs::read_to_string(&accept) else {
        return false;
    };
    let Some(tip) = kv_line(&text, "tip") else {
        return false;
    };
    let Some(epoch) = kv_line(&text, "epoch").and_then(|v| v.parse::<i64>().ok()) else {
        return false;
    };
    let Some(propensity) = kv_line(&text, "propensity") else {
        return false;
    };
    let journal = root
        .join("data")
        .join("feature_registry")
        .join("tip_journal.jsonl");
    let retired = root
        .join("data")
        .join("feature_registry")
        .join("retired_tips.jsonl");
    let Some((jt, je, jp)) = resolve(&journal, &retired) else {
        return false;
    };
    tip == jt && epoch == je && propensity == jp
}

fn main() {
    let eng = PathBuf::from(env::var("CARGO_MANIFEST_DIR").expect("manifest dir"));
    let root = eng.parent().expect("app root").to_path_buf();

    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=../calib/trial_pref.toml");
    println!("cargo:rerun-if-changed=../calib/tip_bind.accept");
    println!("cargo:rerun-if-changed=../data/feature_registry/tip_journal.jsonl");
    println!("cargo:rerun-if-changed=../data/feature_registry/retired_tips.jsonl");
    for (seed, target) in PAIRS {
        println!("cargo:rerun-if-changed={}", seed);
        println!("cargo:rerun-if-changed=../{}", target);
    }

    if seated(&root) {
        return;
    }

    for (seed, target) in PAIRS {
        let seed_path = eng.join(seed);
        let target_path = root.join(target);
        let Ok(body) = fs::read_to_string(&seed_path) else {
            continue;
        };
        let current = fs::read_to_string(&target_path).unwrap_or_default();
        if current != body {
            let _ = fs::write(&target_path, body);
        }
    }
}
