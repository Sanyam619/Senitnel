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

fn retired_tips(path: &Path) -> std::collections::HashSet<String> {
    let mut out = std::collections::HashSet::new();
    let Ok(text) = fs::read_to_string(path) else {
        return out;
    };
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        if let Some(t) = tip_field(line) {
            out.insert(t);
        }
    }
    out
}

/// Publishable lineage: receipt is a durable, non-retired tip id in the journal.
/// Tip selection among durable candidates stays in runtime seating.
fn lineage_publishable(lineage: &Path, journal: &Path, retired: &Path) -> bool {
    let want = lineage_note(lineage);
    if want.is_empty() {
        return false;
    }
    if retired_tips(retired).contains(&want) {
        return false;
    }
    let Ok(text) = fs::read_to_string(journal) else {
        return false;
    };
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        if tip_field(line).as_deref() != Some(want.as_str()) {
            continue;
        }
        if state_field(line).as_deref() == Some("durable") {
            return true;
        }
    }
    false
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
    let lineage_ok = lineage_publishable(&lineage, &journal, &retired);
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
