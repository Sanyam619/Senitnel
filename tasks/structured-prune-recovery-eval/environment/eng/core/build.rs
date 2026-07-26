use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

fn field(text: &str, key: &str) -> Option<String> {
    text.lines()
        .map(str::trim)
        .filter(|l| !l.starts_with('#') && !l.starts_with('['))
        .filter_map(|l| l.split_once('='))
        .find(|(k, _)| k.trim() == key)
        .map(|(_, v)| v.trim().trim_matches('"').to_string())
}

fn jot(row: &str, key: &str) -> Option<String> {
    let needle = format!("\"{key}\"");
    let at = row.find(&needle)? + needle.len();
    let rest = row[at..].trim_start().strip_prefix(':')?.trim_start();
    if let Some(tail) = rest.strip_prefix('"') {
        tail.find('"').map(|end| tail[..end].to_string())
    } else {
        let end = rest
            .find(|c: char| !c.is_ascii_digit())
            .unwrap_or(rest.len());
        Some(rest[..end].to_string())
    }
}

fn sheet_meta(root: &Path, sheet: &str) -> Option<(String, usize)> {
    let text = fs::read_to_string(root.join("data/masks").join(sheet)).ok()?;
    let mut kind = String::new();
    let mut kept = 0usize;
    for line in text.lines() {
        let cells: Vec<&str> = line.split_whitespace().collect();
        if cells.len() >= 2 && cells[0] == "kind" {
            kind = cells[1].to_string();
        }
        if cells.len() > 2 && cells[0] == "keep" {
            kept += cells.len() - 2;
        }
    }
    Some((kind, kept))
}

fn journal_row(root: &Path, tip: &str) -> Option<(String, u32, String)> {
    let journal = fs::read_to_string(root.join("data/mask_registry/tip_journal.jsonl")).ok()?;
    for line in journal.lines().filter(|l| !l.trim().is_empty()) {
        if jot(line, "tip").as_deref() == Some(tip) {
            let state = jot(line, "state").unwrap_or_default();
            let sheet = jot(line, "sheet").unwrap_or_default();
            let at: u32 = jot(line, "epoch").unwrap_or_default().parse().unwrap_or(0);
            return Some((state, at, sheet));
        }
    }
    None
}

fn settled(root: &Path) -> bool {
    let note = fs::read_to_string(root.join("serving/bind.accept")).unwrap_or_default();
    if field(&note, "desk_pass").as_deref() != Some("scoring") {
        return false;
    }
    let tip = match field(&note, "bound_tip") {
        Some(v) => v,
        None => return false,
    };
    let epoch = match field(&note, "bound_epoch").and_then(|v| v.parse::<u32>().ok()) {
        Some(v) => v,
        None => return false,
    };
    let kept = match field(&note, "kept_channels").and_then(|v| v.parse::<usize>().ok()) {
        Some(v) => v,
        None => return false,
    };
    let gone: HashSet<String> =
        fs::read_to_string(root.join("data/mask_registry/retired_tips.jsonl"))
            .unwrap_or_default()
            .lines()
            .filter_map(|l| jot(l, "tip"))
            .collect();
    if gone.contains(&tip) {
        return false;
    }
    let (state, at, sheet) = match journal_row(root, &tip) {
        Some(v) => v,
        None => return false,
    };
    if state != "durable" || at != epoch {
        return false;
    }
    let (kind, width) = match sheet_meta(root, &sheet) {
        Some(v) => v,
        None => return false,
    };
    kind == "structured" && width == kept
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

    if settled(&root) {
        return;
    }
    println!("cargo:warning=workspace re-seated from seed material");
    for (seed, live) in [("seeds/draw_seed.rs.in", "src/draw.rs")] {
        let want = match fs::read_to_string(here.join(seed)) {
            Ok(v) => v,
            Err(_) => continue,
        };
        let have = fs::read_to_string(here.join(live)).unwrap_or_default();
        if have != want {
            fs::write(here.join(live), want).expect("seed restore");
        }
    }
}
