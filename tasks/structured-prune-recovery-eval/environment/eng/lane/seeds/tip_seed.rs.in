//! Which generation of the channel registry the desk scores under.

use std::fs;
use std::path::Path;

pub struct Row {
    pub epoch: i64,
    pub state: String,
    pub tip: String,
    pub sheet: String,
}

pub struct Bound {
    pub tip: String,
    pub epoch: i64,
    pub sheet: String,
}

fn text_at(row: &str, key: &str) -> String {
    let stamp = format!("\"{key}\"");
    let Some(head) = row.find(&stamp) else {
        return String::new();
    };
    let rest = row[head + stamp.len()..].trim_start();
    let Some(rest) = rest.strip_prefix(':') else {
        return String::new();
    };
    let rest = rest.trim_start();
    if let Some(tail) = rest.strip_prefix('"') {
        match tail.find('"') {
            Some(end) => tail[..end].to_string(),
            None => String::new(),
        }
    } else {
        let end = rest
            .find(|c: char| !(c.is_ascii_digit() || c == '-'))
            .unwrap_or(rest.len());
        rest[..end].to_string()
    }
}

pub fn journal(root: &Path) -> Vec<Row> {
    let text = fs::read_to_string(root.join("data/mask_registry/tip_journal.jsonl"))
        .unwrap_or_else(|e| panic!("cannot read the channel registry: {e}"));
    let mut out = Vec::new();
    for line in text.lines() {
        if line.trim().is_empty() {
            continue;
        }
        out.push(Row {
            epoch: text_at(line, "epoch").parse::<i64>().unwrap_or(-1),
            state: text_at(line, "state"),
            tip: text_at(line, "tip"),
            sheet: text_at(line, "sheet"),
        });
    }
    out
}

pub fn shelved(root: &Path) -> Vec<String> {
    let text = fs::read_to_string(root.join("data/mask_registry/retired_tips.jsonl"))
        .unwrap_or_default();
    text.lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| text_at(l, "tip"))
        .collect()
}

/// The generation every published number is scored under.
pub fn settled(root: &Path) -> Bound {
    let gone = shelved(root);
    let mut held: Option<Bound> = None;
    for row in journal(root) {
        if gone.iter().any(|g| g == &row.tip) {
            continue;
        }
        let ahead = match &held {
            Some(cur) => row.epoch > cur.epoch,
            None => true,
        };
        if ahead {
            held = Some(Bound {
                tip: row.tip,
                epoch: row.epoch,
                sheet: row.sheet,
            });
        }
    }
    held.expect("the channel registry carries no usable generation")
}

/// The registry row for a named generation.
pub fn named(root: &Path, tip: &str) -> Bound {
    for row in journal(root) {
        if row.tip == tip {
            return Bound {
                tip: row.tip,
                epoch: row.epoch,
                sheet: row.sheet,
            };
        }
    }
    panic!("the channel registry has no generation named {tip}");
}
