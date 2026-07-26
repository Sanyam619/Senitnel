use std::fs;
use std::path::{Path, PathBuf};

fn value(root: &Path, file: &str, key: &str) -> String {
    let text = match fs::read_to_string(root.join(file)) {
        Ok(v) => v,
        Err(_) => return String::new(),
    };
    for line in text.lines() {
        let line = line.trim();
        if line.starts_with('#') || line.starts_with('[') {
            continue;
        }
        if let Some((lhs, rhs)) = line.split_once('=') {
            if lhs.trim() == key {
                return rhs.trim().trim_matches('"').to_string();
            }
        }
    }
    String::new()
}

fn jot(row: &str, key: &str) -> String {
    let stamp = format!("\"{key}\"");
    match row.split_once(&stamp) {
        Some((_, tail)) => match tail.split_once(':') {
            Some((_, val)) => {
                let val = val.trim_start();
                if let Some(rest) = val.strip_prefix('"') {
                    rest.split('"').next().unwrap_or("").to_string()
                } else {
                    rest_digits(val)
                }
            }
            None => String::new(),
        },
        None => String::new(),
    }
}

fn rest_digits(val: &str) -> String {
    let end = val
        .find(|c: char| !c.is_ascii_digit())
        .unwrap_or(val.len());
    val[..end].to_string()
}

fn sheet_meta(root: &Path, sheet: &str) -> (String, usize) {
    let text = match fs::read_to_string(root.join("data/masks").join(sheet)) {
        Ok(v) => v,
        Err(_) => return (String::new(), usize::MAX),
    };
    let mut kind = String::new();
    let mut kept = 0usize;
    for line in text.lines() {
        let row: Vec<&str> = line.split_whitespace().collect();
        if row.len() >= 2 && row[0] == "kind" {
            kind = row[1].to_string();
        }
        if row.len() > 2 && row[0] == "keep" {
            kept += row.len() - 2;
        }
    }
    (kind, kept)
}

fn receipt_ready(root: &Path) -> bool {
    if value(root, "serving/bind.accept", "desk_pass") != "scoring" {
        return false;
    }
    let tip = value(root, "serving/bind.accept", "bound_tip");
    let epoch = value(root, "serving/bind.accept", "bound_epoch");
    let kept = value(root, "serving/bind.accept", "kept_channels");
    if tip.is_empty() || epoch.is_empty() || kept.is_empty() {
        return false;
    }
    let gone: Vec<String> =
        match fs::read_to_string(root.join("data/mask_registry/retired_tips.jsonl")) {
            Ok(text) => text
                .lines()
                .filter(|l| !l.trim().is_empty())
                .map(|l| jot(l, "tip"))
                .collect(),
            Err(_) => Vec::new(),
        };
    if gone.iter().any(|g| g == &tip) {
        return false;
    }
    let mut state = String::new();
    let mut sheet = String::new();
    let mut at = String::new();
    if let Ok(text) = fs::read_to_string(root.join("data/mask_registry/tip_journal.jsonl")) {
        for line in text.lines() {
            if line.trim().is_empty() {
                continue;
            }
            if jot(line, "tip") == tip {
                state = jot(line, "state");
                sheet = jot(line, "sheet");
                at = jot(line, "epoch");
                break;
            }
        }
    }
    if state != "durable" || at != epoch {
        return false;
    }
    let (kind, width) = sheet_meta(root, &sheet);
    kind == "structured" && width.to_string() == kept
}

fn restore(here: &Path, seed: &str, live: &str) {
    let want = match fs::read_to_string(here.join(seed)) {
        Ok(v) => v,
        Err(_) => return,
    };
    let have = fs::read_to_string(here.join(live)).unwrap_or_default();
    if have != want {
        fs::write(here.join(live), want).expect("seed restore");
    }
}

fn main() {
    let here = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
    let root = here.parent().unwrap().parent().unwrap().to_path_buf();

    println!("cargo:rerun-if-changed=src");
    println!("cargo:rerun-if-changed=seeds");
    println!("cargo:rerun-if-changed={}/calib", root.display());
    println!("cargo:rerun-if-changed={}/serving", root.display());
    println!("cargo:rerun-if-changed={}/data/mask_registry", root.display());
    println!("cargo:rerun-if-changed={}/data/masks", root.display());

    if !receipt_ready(&root) {
        restore(&here, "seeds/tip_seed.rs.in", "src/tip.rs");
        restore(&here, "seeds/seat_seed.rs.in", "src/seat.rs");
    }
}
