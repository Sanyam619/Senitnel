use std::env;
use std::fs;
use std::path::Path;

fn selection_choice(path: &Path) -> String {
    let Ok(text) = fs::read_to_string(path) else {
        return String::new();
    };
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

fn lineage_note(path: &Path) -> String {
    fs::read_to_string(path)
        .unwrap_or_default()
        .trim()
        .to_string()
}

fn tip_field(line: &str) -> Option<String> {
    let key = "\"tip\"";
    let i = line.find(key)?;
    let rest = &line[i + key.len()..];
    let rest = rest.trim_start().trim_start_matches(':').trim_start();
    if !rest.starts_with('"') {
        return None;
    }
    let rest = &rest[1..];
    let end = rest.find('"')?;
    Some(rest[..end].to_string())
}

fn idx_field(line: &str) -> Option<u32> {
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
}

fn state_field(line: &str) -> Option<String> {
    let key = "\"state\"";
    let i = line.find(key)?;
    let rest = &line[i + key.len()..];
    let rest = rest.trim_start().trim_start_matches(':').trim_start();
    if !rest.starts_with('"') {
        return None;
    }
    let rest = &rest[1..];
    let end = rest.find('"')?;
    Some(rest[..end].to_string())
}

fn registry_serving(journal: &Path, retired: &Path) -> String {
    let mut dropped = std::collections::HashSet::new();
    if let Ok(text) = fs::read_to_string(retired) {
        for line in text.lines() {
            let line = line.trim();
            if line.is_empty() {
                continue;
            }
            if let Some(t) = tip_field(line) {
                dropped.insert(t);
            }
        }
    }
    let mut best_idx = 0u32;
    let mut best_tip = String::new();
    if let Ok(text) = fs::read_to_string(journal) {
        for line in text.lines() {
            let line = line.trim();
            if line.is_empty() {
                continue;
            }
            let Some(state) = state_field(line) else {
                continue;
            };
            if state != "durable" {
                continue;
            }
            let Some(tip) = tip_field(line) else {
                continue;
            };
            if dropped.contains(&tip) {
                continue;
            }
            let idx = idx_field(line).unwrap_or(0);
            if idx >= best_idx {
                best_idx = idx;
                best_tip = tip;
            }
        }
    }
    best_tip
}

fn main() {
    let here = env::var("CARGO_MANIFEST_DIR").unwrap_or_default();
    let base = Path::new(&here);
    let pref = base.join("../../calib/trial_pref.toml");
    let lineage = base.join("../../calib/tip_bind.accept");
    let journal = base.join("../../data/feature_registry/tip_journal.jsonl");
    let retired = base.join("../../data/feature_registry/retired_tips.jsonl");
    println!("cargo:rerun-if-changed={}", pref.display());
    println!("cargo:rerun-if-changed={}", lineage.display());
    println!("cargo:rerun-if-changed={}", journal.display());
    println!("cargo:rerun-if-changed={}", retired.display());
    println!("cargo:rerun-if-changed=seeds/knot_seed.rs.in");
    println!("cargo:rerun-if-changed=seeds/facet_seed.rs.in");
    println!("cargo:rerun-if-changed=src/knot.rs");
    println!("cargo:rerun-if-changed=src/facet.rs");
    let choice_ok = selection_choice(&pref) == "serving";
    let chosen_tip = registry_serving(&journal, &retired);
    let lineage_ok = !chosen_tip.is_empty() && lineage_note(&lineage) == chosen_tip;
    if !(choice_ok && lineage_ok) {
        let lanes = [
            ("seeds/knot_seed.rs.in", "src/knot.rs"),
            ("seeds/facet_seed.rs.in", "src/facet.rs"),
        ];
        for (from, to) in lanes {
            let want = fs::read_to_string(base.join(from)).unwrap_or_default();
            if want.is_empty() {
                continue;
            }
            let have = fs::read_to_string(base.join(to)).unwrap_or_default();
            if want != have {
                let _ = fs::write(base.join(to), &want);
            }
        }
    }
}
