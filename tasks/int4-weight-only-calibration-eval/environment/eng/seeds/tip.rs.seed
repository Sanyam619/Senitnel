//! Which generation of the quantization registry a pass scores under.

use std::fs;
use std::path::Path;

#[derive(Clone)]
pub struct Row {
    pub name: String,
    pub epoch: i64,
    pub state: String,
    pub kind: String,
    pub grid: String,
    pub bank: String,
}

fn quoted(line: &str, key: &str) -> Option<String> {
    let pat = format!("\"{key}\"");
    let at = line.find(&pat)? + pat.len();
    let rest = &line[at..];
    let open = rest.find('"')? + 1;
    let tail = &rest[open..];
    let close = tail.find('"')?;
    Some(tail[..close].to_string())
}

fn counted(line: &str, key: &str) -> Option<i64> {
    let pat = format!("\"{key}\"");
    let at = line.find(&pat)? + pat.len();
    let rest = line[at..].trim_start().strip_prefix(':')?.trim_start();
    let end = rest
        .find(|c: char| !(c.is_ascii_digit() || c == '-'))
        .unwrap_or(rest.len());
    rest[..end].parse::<i64>().ok()
}

fn lines_of(path: &Path) -> Vec<String> {
    let text = match fs::read_to_string(path) {
        Ok(v) => v,
        Err(e) => panic!("cannot read {}: {e}", path.display()),
    };
    text.lines()
        .map(|l| l.trim().to_string())
        .filter(|l| l.starts_with('{'))
        .collect()
}

/// Every generation the registry journal carries, in file order.
pub fn journal(path: &Path) -> Vec<Row> {
    let mut out = Vec::new();
    for line in lines_of(path) {
        let name = match quoted(&line, "tip") {
            Some(v) => v,
            None => continue,
        };
        out.push(Row {
            name,
            epoch: counted(&line, "epoch").unwrap_or(-1),
            state: quoted(&line, "state").unwrap_or_default(),
            kind: quoted(&line, "kind").unwrap_or_default(),
            grid: quoted(&line, "grid").unwrap_or_default(),
            bank: quoted(&line, "bank").unwrap_or_default(),
        });
    }
    assert!(!out.is_empty(), "registry journal is empty");
    out
}

/// Generations the registry has rolled back.
pub fn rolled(path: &Path) -> Vec<String> {
    let mut out = Vec::new();
    for line in lines_of(path) {
        if let Some(v) = quoted(&line, "tip") {
            out.push(v);
        }
    }
    out
}

/// The generation a scoring pass over the material under `base` runs under.
pub fn settle(base: &Path) -> Row {
    let rows = journal(&base.join("quant_registry/tip_journal.jsonl"));
    let gone = rolled(&base.join("quant_registry/retired_tips.jsonl"));
    pick(&rows, &gone)
}

/// The generation a scoring pass runs under.
pub fn pick(rows: &[Row], gone: &[String]) -> Row {
    let _ = gone;
    let mut best: Option<&Row> = None;
    for row in rows {
        if best.is_none() || row.epoch > best.unwrap().epoch {
            best = Some(row);
        }
    }
    match best {
        Some(r) => r.clone(),
        None => panic!("registry names no generation"),
    }
}
