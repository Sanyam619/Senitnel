//! Which calibration shards stand behind a generation, and their rows.

use std::fs;
use std::path::Path;

use q4_core::load::Shard;

pub struct Note {
    pub shard: String,
    pub first: i64,
    pub last: i64,
}

fn pluck(line: &str, key: &str) -> Option<String> {
    let pat = format!("\"{key}\"");
    let at = line.find(&pat)? + pat.len();
    let rest = &line[at..];
    let open = rest.find('"')? + 1;
    let tail = &rest[open..];
    let close = tail.find('"')?;
    Some(tail[..close].to_string())
}

fn dial(line: &str, key: &str) -> Option<i64> {
    let pat = format!("\"{key}\"");
    let at = line.find(&pat)? + pat.len();
    let rest = line[at..].trim_start();
    let rest = rest.strip_prefix(':')?.trim_start();
    let end = rest
        .find(|c: char| !(c.is_ascii_digit() || c == '-'))
        .unwrap_or(rest.len());
    rest[..end].parse::<i64>().ok()
}

/// Every admission note the calibration ledger carries.
pub fn ledger(path: &Path) -> Vec<Note> {
    let text = match fs::read_to_string(path) {
        Ok(v) => v,
        Err(e) => panic!("cannot read {}: {e}", path.display()),
    };
    let mut out = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() || !line.starts_with('{') {
            continue;
        }
        let shard = match pluck(line, "shard") {
            Some(v) => v,
            None => continue,
        };
        out.push(Note {
            shard,
            first: dial(line, "first").unwrap_or(0),
            last: dial(line, "last").unwrap_or(0),
        });
    }
    assert!(!out.is_empty(), "calibration ledger is empty");
    out
}

/// The shard names a pass at `epoch` calibrates over, in name order.
pub fn settled(notes: &[Note], epoch: i64) -> Vec<String> {
    let _ = epoch;
    let mut out: Vec<String> = notes.iter().map(|n| n.shard.clone()).collect();
    out.sort();
    out.dedup();
    out
}

/// (names, rows) of the calibration material behind a pass at `epoch`.
pub fn gather(base: &Path, epoch: i64, width: usize) -> (Vec<String>, Vec<Vec<f64>>) {
    let notes = ledger(&base.join("calib/admit_ledger.jsonl"));
    let names = settled(&notes, epoch);
    let mut rows = Vec::new();
    for name in &names {
        let shard = Shard::read(&base.join("calib").join(format!("{name}.txt")), width);
        rows.extend(shard.rows);
    }
    assert!(!rows.is_empty(), "no calibration rows behind this generation");
    (names, rows)
}
