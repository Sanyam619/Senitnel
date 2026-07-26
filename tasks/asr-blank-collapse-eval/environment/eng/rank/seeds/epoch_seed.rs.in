use std::collections::HashSet;
use std::fs;
use std::path::Path;

pub struct Row {
    pub at: u32,
    pub state: String,
    pub name: String,
    pub sheet: String,
    pub route: String,
}

fn text_of(row: &str, key: &str) -> String {
    let needle = format!("\"{key}\"");
    let Some(head) = row.find(&needle) else {
        return String::new();
    };
    let rest = row[head + needle.len()..].trim_start();
    let Some(rest) = rest.strip_prefix(':') else {
        return String::new();
    };
    let rest = rest.trim_start();
    match rest.strip_prefix('"') {
        Some(tail) => tail
            .find('"')
            .map(|end| tail[..end].to_string())
            .unwrap_or_default(),
        None => {
            let end = rest
                .find(|c: char| !c.is_ascii_digit())
                .unwrap_or(rest.len());
            rest[..end].to_string()
        }
    }
}

pub fn rows(root: &Path) -> Vec<Row> {
    let text = fs::read_to_string(root.join("data/decoder_registry/tip_journal.jsonl"))
        .expect("registry journal");
    text.lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| Row {
            at: text_of(l, "idx").parse().unwrap_or(0),
            state: text_of(l, "state"),
            name: text_of(l, "tip"),
            sheet: text_of(l, "sheet"),
            route: text_of(l, "mode"),
        })
        .collect()
}

pub fn out_set(root: &Path) -> HashSet<String> {
    fs::read_to_string(root.join("data/decoder_registry/retired_tips.jsonl"))
        .unwrap_or_default()
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| text_of(l, "tip"))
        .collect()
}

/// Returns the generation index the desk binds for this run.
pub fn pick_e(rows: &[Row], out: &HashSet<String>) -> u32 {
    let _ = out;
    let mut held = 0u32;
    for row in rows.iter() {
        if row.at > held {
            held = row.at;
        }
    }
    held
}
