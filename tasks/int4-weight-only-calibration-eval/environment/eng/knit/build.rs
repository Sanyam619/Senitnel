use std::fs;
use std::path::{Path, PathBuf};

const SURFACES: [&str; 2] = ["admit.rs", "gains.rs"];

fn pairs(text: &str) -> Vec<(String, String)> {
    text.lines()
        .map(str::trim)
        .filter(|l| !l.is_empty() && !l.starts_with('#') && l.contains('='))
        .map(|l| {
            let mut it = l.splitn(2, '=');
            let k = it.next().unwrap_or("").trim().to_string();
            let v = it.next().unwrap_or("").trim().trim_matches('"').to_string();
            (k, v)
        })
        .collect()
}

fn look(book: &[(String, String)], key: &str) -> String {
    book.iter()
        .rev()
        .find(|(k, _)| k == key)
        .map(|(_, v)| v.clone())
        .unwrap_or_default()
}

fn tagged(line: &str, key: &str) -> String {
    let mut chunks = line.split('"');
    while let Some(chunk) = chunks.next() {
        if chunk == key {
            let sep = chunks.next().unwrap_or("");
            if sep.contains(':') {
                return chunks.next().unwrap_or("").to_string();
            }
        }
    }
    String::new()
}

fn widths(path: &Path) -> Vec<usize> {
    let mut slots: Vec<(usize, usize)> = Vec::new();
    for line in fs::read_to_string(path).unwrap_or_default().lines() {
        let cols: Vec<&str> = line.split_whitespace().collect();
        if cols.len() == 4 && cols[0] == "layer" {
            let at = cols[1].parse::<usize>().unwrap_or(0);
            let inn = cols[3].parse::<usize>().unwrap_or(0);
            slots.push((at, inn));
        }
    }
    slots.sort_by_key(|s| s.0);
    slots.into_iter().map(|s| s.1).collect()
}

fn extent(group: usize, len: usize) -> usize {
    if group == 0 || group > len || len % group != 0 {
        len
    } else {
        group
    }
}

fn cleared(root: &Path) -> bool {
    let note = pairs(&fs::read_to_string(root.join("serving/bind.accept")).unwrap_or_default());
    let want = look(&note, "tip");
    let group = look(&note, "group").parse::<usize>().unwrap_or(0);
    let count = look(&note, "groups").parse::<usize>().unwrap_or(0);
    if want.is_empty() || group == 0 || count == 0 {
        return false;
    }
    let book =
        fs::read_to_string(root.join("data/quant_registry/tip_journal.jsonl")).unwrap_or_default();
    let sheet = book
        .lines()
        .find(|l| tagged(l, "tip") == want)
        .map(|l| tagged(l, "grid"))
        .unwrap_or_default();
    if sheet.is_empty() {
        return false;
    }
    let mut declared = 0usize;
    let mut kind = String::new();
    for line in fs::read_to_string(root.join("data/quant_grids").join(&sheet))
        .unwrap_or_default()
        .lines()
    {
        let cols: Vec<&str> = line.split_whitespace().collect();
        if cols.len() == 2 && cols[0] == "group" {
            declared = cols[1].parse::<usize>().unwrap_or(0);
        }
        if cols.len() == 2 && cols[0] == "kind" {
            kind = cols[1].to_string();
        }
    }
    if kind != "grouped" || declared != group {
        return false;
    }
    let laid: usize = widths(&root.join("data/arch/topology.txt"))
        .into_iter()
        .map(|d| d / extent(group, d))
        .sum();
    laid == count
}

fn main() {
    let crate_dir = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
    let root = crate_dir.parent().unwrap().parent().unwrap().to_path_buf();
    println!("cargo:rerun-if-changed=src");
    println!("cargo:rerun-if-changed=build.rs");
    println!(
        "cargo:rerun-if-changed={}",
        root.join("serving/bind.accept").display()
    );
    if cleared(&root) {
        return;
    }
    for name in SURFACES {
        let seed = root.join("eng/seeds").join(format!("{name}.seed"));
        let live = crate_dir.join("src").join(name);
        if let Ok(body) = fs::read_to_string(&seed) {
            if fs::read_to_string(&live).unwrap_or_default() != body {
                let _ = fs::write(&live, body);
            }
        }
    }
}
