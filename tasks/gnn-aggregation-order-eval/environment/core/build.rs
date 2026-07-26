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

fn load_set(path: &Path, key: &str) -> std::collections::HashSet<String> {
    let mut out = std::collections::HashSet::new();
    let Ok(body) = fs::read_to_string(path) else {
        return out;
    };
    for line in body.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        if let Some(v) = extract_quoted(line, key) {
            out.insert(v);
        }
    }
    out
}

/// Publishable bind: receipt names a durable journal tip that is not retired.
/// Tip selection among durable candidates stays in runtime seating.
fn publishable_bind(accept: &Path, journal: &Path, retired: &Path) -> bool {
    let tip = bind_receipt(accept);
    if tip.is_empty() {
        return false;
    }
    if load_set(retired, "tip").contains(&tip) {
        return false;
    }
    let Ok(body) = fs::read_to_string(journal) else {
        return false;
    };
    for line in body.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        if extract_quoted(line, "tip").as_deref() != Some(tip.as_str()) {
            continue;
        }
        if extract_quoted(line, "state").as_deref() == Some("durable") {
            return true;
        }
    }
    false
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
    println!("cargo:rerun-if-changed=seeds/braid_seed.rs.in");
    println!("cargo:rerun-if-changed=src/lens.rs");
    println!("cargo:rerun-if-changed=src/weave.rs");
    println!("cargo:rerun-if-changed=src/braid.rs");

    let serving = eval_selection(&pref) == "serving";
    let bound = publishable_bind(&accept, &journal, &retired);
    if !(serving && bound) {
        for (seed, dest) in [
            ("seeds/lens_seed.rs.in", "src/lens.rs"),
            ("seeds/weave_seed.rs.in", "src/weave.rs"),
            ("seeds/braid_seed.rs.in", "src/braid.rs"),
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
