use std::env;
use std::fs;
use std::path::PathBuf;

fn load_blob(p: &PathBuf) -> String {
    match fs::read_to_string(p) {
        Ok(s) => s,
        Err(_) => String::new(),
    }
}

fn scan_selection_token(blob: &str) -> String {
    let bytes = blob.as_bytes();
    let needle = b"selection";
    let mut i = 0usize;
    while i + needle.len() <= bytes.len() {
        if &bytes[i..i + needle.len()] == needle {
            let mut j = i + needle.len();
            while j < bytes.len() && (bytes[j] == b' ' || bytes[j] == b'\t') {
                j += 1;
            }
            if j < bytes.len() && bytes[j] == b'=' {
                j += 1;
                while j < bytes.len() && (bytes[j] == b' ' || bytes[j] == b'\t') {
                    j += 1;
                }
                let start = j;
                while j < bytes.len() && bytes[j] != b'\n' && bytes[j] != b'\r' {
                    j += 1;
                }
                let raw = blob[start..j].trim().trim_matches('"');
                return raw.to_string();
            }
        }
        i += 1;
    }
    String::new()
}

fn pull_quoted(blob: &str, key: &str) -> Option<String> {
    let marker = format!("\"{}\"", key);
    let at = blob.find(&marker)?;
    let mut rest = &blob[at + marker.len()..];
    rest = rest.trim_start();
    if rest.starts_with(':') {
        rest = rest[1..].trim_start();
    }
    if !rest.starts_with('"') {
        return None;
    }
    rest = &rest[1..];
    let stop = rest.find('"')?;
    Some(rest[..stop].to_string())
}

fn pull_uint(blob: &str, key: &str) -> Option<u32> {
    let marker = format!("\"{}\"", key);
    let at = blob.find(&marker)?;
    let mut rest = &blob[at + marker.len()..];
    rest = rest.trim_start();
    if rest.starts_with(':') {
        rest = rest[1..].trim_start();
    }
    let mut digits = String::new();
    for ch in rest.chars() {
        if ch.is_ascii_digit() {
            digits.push(ch);
        } else if !digits.is_empty() {
            break;
        }
    }
    digits.parse().ok()
}

fn registry_tip(journal_blob: &str, retired_blob: &str) -> String {
    let mut retired_list = Vec::new();
    for chunk in retired_blob.split('\n') {
        let chunk = chunk.trim();
        if chunk.is_empty() {
            continue;
        }
        if let Some(t) = pull_quoted(chunk, "tip") {
            retired_list.push(t);
        }
    }
    let mut peak: u32 = 0;
    let mut chosen = String::new();
    for chunk in journal_blob.split('\n') {
        let chunk = chunk.trim();
        if chunk.is_empty() {
            continue;
        }
        let st = match pull_quoted(chunk, "state") {
            Some(s) => s,
            None => continue,
        };
        if st != "durable" {
            continue;
        }
        let name = match pull_quoted(chunk, "tip") {
            Some(t) => t,
            None => continue,
        };
        if retired_list.iter().any(|b| b == &name) {
            continue;
        }
        let n = pull_uint(chunk, "idx").unwrap_or(0);
        if n >= peak {
            peak = n;
            chosen = name;
        }
    }
    chosen
}

fn serving_pinned(choice: &str, lineage: &str, chosen_tip: &str) -> bool {
    choice == "serving" && !chosen_tip.is_empty() && lineage.trim() == chosen_tip
}

fn main() {
    let manifest = env::var("CARGO_MANIFEST_DIR").unwrap_or_default();
    let root = PathBuf::from(&manifest);
    let pref_path = root.join("../../calib/trial_pref.toml");
    let lineage_path = root.join("../../calib/tip_bind.accept");
    let journal_path = root.join("../../data/feature_registry/tip_journal.jsonl");
    let retired_path = root.join("../../data/feature_registry/retired_tips.jsonl");
    let seed_path = root.join("seeds/mesh_seed.rs.in");
    let mesh_path = root.join("src/mesh.rs");

    println!("cargo:rerun-if-changed={}", pref_path.display());
    println!("cargo:rerun-if-changed={}", lineage_path.display());
    println!("cargo:rerun-if-changed={}", journal_path.display());
    println!("cargo:rerun-if-changed={}", retired_path.display());
    println!("cargo:rerun-if-changed={}", seed_path.display());
    println!("cargo:rerun-if-changed={}", mesh_path.display());

    let pref_blob = load_blob(&pref_path);
    let choice = scan_selection_token(&pref_blob);
    let lineage = load_blob(&lineage_path);
    let journal_blob = load_blob(&journal_path);
    let retired_blob = load_blob(&retired_path);
    let chosen_tip = registry_tip(&journal_blob, &retired_blob);

    if !serving_pinned(&choice, &lineage, &chosen_tip) {
        let seed = load_blob(&seed_path);
        if !seed.is_empty() {
            let current = load_blob(&mesh_path);
            if current != seed {
                let _ = fs::write(&mesh_path, seed.as_bytes());
            }
        }
    }
}
