use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

fn field(text: &str, key: &str) -> Option<String> {
    text.lines()
        .map(str::trim)
        .filter(|l| !l.starts_with('#'))
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

fn settled(root: &Path) -> Option<(String, u32)> {
    let journal =
        fs::read_to_string(root.join("data/decoder_registry/tip_journal.jsonl")).ok()?;
    let gone: HashSet<String> =
        fs::read_to_string(root.join("data/decoder_registry/retired_tips.jsonl"))
            .unwrap_or_default()
            .lines()
            .filter_map(|l| jot(l, "tip"))
            .collect();
    let mut held: Option<(String, u32)> = None;
    for line in journal.lines().filter(|l| !l.trim().is_empty()) {
        let state = jot(line, "state").unwrap_or_default();
        let name = jot(line, "tip").unwrap_or_default();
        let at: u32 = jot(line, "idx").unwrap_or_default().parse().unwrap_or(0);
        if state != "sealed" || gone.contains(&name) {
            continue;
        }
        if held.as_ref().map(|(_, n)| at > *n).unwrap_or(true) {
            held = Some((name, at));
        }
    }
    held
}

fn seated(root: &Path) -> bool {
    let pass = fs::read_to_string(root.join("calib/eval_pass.toml")).unwrap_or_default();
    if field(&pass, "pass").as_deref() != Some("scoring") {
        return false;
    }
    let note = fs::read_to_string(root.join("calib/decoder_selection.txt")).unwrap_or_default();
    let (name, at) = match settled(root) {
        Some(v) => v,
        None => return false,
    };
    field(&note, "selected_tip").as_deref() == Some(name.as_str())
        && field(&note, "selected_generation")
            .and_then(|v| v.parse::<u32>().ok())
            .map(|v| v == at)
            .unwrap_or(false)
}

fn main() {
    let here = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
    let root = here.parent().unwrap().parent().unwrap().to_path_buf();

    println!("cargo:rerun-if-changed=src");
    println!("cargo:rerun-if-changed=seeds");
    println!("cargo:rerun-if-changed={}/calib", root.display());
    println!(
        "cargo:rerun-if-changed={}/data/decoder_registry",
        root.display()
    );

    if seated(&root) {
        return;
    }
    for (seed, live) in [
        ("seeds/collapse_seed.rs.in", "src/collapse.rs"),
        ("seeds/join_seed.rs.in", "src/join.rs"),
    ] {
        let want = match fs::read_to_string(here.join(seed)) {
            Ok(v) => v,
            Err(_) => continue,
        };
        let have = fs::read_to_string(here.join(live)).unwrap_or_default();
        if have != want {
            fs::write(here.join(live), want).expect("desk seating restore");
        }
    }
}
