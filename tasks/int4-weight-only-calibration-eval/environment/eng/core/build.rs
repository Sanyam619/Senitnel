use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

fn here() -> PathBuf {
    PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap())
}

fn receipt(path: &Path) -> BTreeMap<String, String> {
    let mut out = BTreeMap::new();
    let text = match fs::read_to_string(path) {
        Ok(v) => v,
        Err(_) => return out,
    };
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        if let Some((k, v)) = line.split_once('=') {
            out.insert(k.trim().to_string(), v.trim().trim_matches('"').to_string());
        }
    }
    out
}

fn field(line: &str, key: &str) -> String {
    let pat = format!("\"{key}\"");
    let at = match line.find(&pat) {
        Some(v) => v + pat.len(),
        None => return String::new(),
    };
    let rest = &line[at..];
    let open = match rest.find('"') {
        Some(v) => v + 1,
        None => return String::new(),
    };
    let tail = &rest[open..];
    match tail.find('"') {
        Some(close) => tail[..close].to_string(),
        None => String::new(),
    }
}

fn accepted(root: &Path) -> bool {
    let note = receipt(&root.join("serving/bind.accept"));
    if note.get("pass").map(|v| v.as_str()) != Some("scoring") {
        return false;
    }
    let want = match note.get("tip") {
        Some(v) if !v.is_empty() => v.clone(),
        _ => return false,
    };
    let dropped = fs::read_to_string(root.join("data/quant_registry/retired_tips.jsonl"))
        .unwrap_or_default();
    for line in dropped.lines() {
        if field(line, "tip") == want {
            return false;
        }
    }
    let book =
        fs::read_to_string(root.join("data/quant_registry/tip_journal.jsonl")).unwrap_or_default();
    for line in book.lines() {
        if field(line, "tip") != want {
            continue;
        }
        return field(line, "state") == "sealed" && field(line, "kind") == "grouped";
    }
    false
}

fn reseat(root: &Path, src: &Path) {
    for name in ["fold.rs"] {
        let seed = root.join("eng/seeds").join(format!("{name}.seed"));
        let live = src.join(name);
        let want = match fs::read_to_string(&seed) {
            Ok(v) => v,
            Err(_) => continue,
        };
        let have = fs::read_to_string(&live).unwrap_or_default();
        if have != want {
            let _ = fs::write(&live, want);
        }
    }
}

fn main() {
    let crate_dir = here();
    let root = crate_dir.parent().unwrap().parent().unwrap().to_path_buf();
    println!("cargo:rerun-if-changed=src");
    println!("cargo:rerun-if-changed=build.rs");
    println!(
        "cargo:rerun-if-changed={}",
        root.join("serving/bind.accept").display()
    );
    if !accepted(&root) {
        reseat(&root, &crate_dir.join("src"));
    }
}
