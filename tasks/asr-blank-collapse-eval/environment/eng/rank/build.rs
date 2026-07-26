use std::fs;
use std::path::{Path, PathBuf};

struct Entry {
    at: u32,
    state: String,
    name: String,
}

struct Ledger {
    entries: Vec<Entry>,
    dropped: Vec<String>,
}

fn quoted(chunk: &str) -> String {
    let mut it = chunk.chars();
    let mut held = String::new();
    let mut open = false;
    for ch in it.by_ref() {
        if ch == '"' {
            if open {
                return held;
            }
            open = true;
            continue;
        }
        if open {
            held.push(ch);
        } else if ch.is_ascii_digit() {
            held.push(ch);
        } else if !held.is_empty() {
            return held;
        }
    }
    held
}

fn slot(line: &str, key: &str) -> String {
    let stamp = format!("\"{key}\"");
    match line.split_once(&stamp) {
        Some((_, tail)) => match tail.split_once(':') {
            Some((_, val)) => quoted(val),
            None => String::new(),
        },
        None => String::new(),
    }
}

impl Ledger {
    fn open(root: &Path) -> Ledger {
        let mut entries = Vec::new();
        if let Ok(text) = fs::read_to_string(root.join("data/decoder_registry/tip_journal.jsonl")) {
            for line in text.lines() {
                if line.trim().is_empty() {
                    continue;
                }
                entries.push(Entry {
                    at: slot(line, "idx").parse().unwrap_or(0),
                    state: slot(line, "state"),
                    name: slot(line, "tip"),
                });
            }
        }
        let mut dropped = Vec::new();
        if let Ok(text) =
            fs::read_to_string(root.join("data/decoder_registry/retired_tips.jsonl"))
        {
            for line in text.lines() {
                if line.trim().is_empty() {
                    continue;
                }
                dropped.push(slot(line, "tip"));
            }
        }
        Ledger { entries, dropped }
    }

    fn held(&self) -> Option<&Entry> {
        let mut best: Option<&Entry> = None;
        for entry in self.entries.iter() {
            if entry.state != "sealed" {
                continue;
            }
            if self.dropped.iter().any(|d| d == &entry.name) {
                continue;
            }
            best = match best {
                Some(prev) if prev.at >= entry.at => Some(prev),
                _ => Some(entry),
            };
        }
        best
    }
}

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

    let ledger = Ledger::open(&root);
    let mut ready = value(&root, "calib/eval_pass.toml", "pass") == "scoring";
    match ledger.held() {
        Some(entry) => {
            if value(&root, "calib/decoder_selection.txt", "selected_tip") != entry.name {
                ready = false;
            }
            if value(&root, "calib/decoder_selection.txt", "selected_generation")
                != entry.at.to_string()
            {
                ready = false;
            }
        }
        None => ready = false,
    }

    if !ready {
        restore(&here, "seeds/epoch_seed.rs.in", "src/epoch.rs");
        restore(&here, "seeds/fuse_seed.rs.in", "src/fuse.rs");
    }
}

fn restore(here: &Path, seed: &str, live: &str) {
    let want = match fs::read_to_string(here.join(seed)) {
        Ok(v) => v,
        Err(_) => return,
    };
    let have = fs::read_to_string(here.join(live)).unwrap_or_default();
    if have != want {
        fs::write(here.join(live), want).expect("desk seating restore");
    }
}
