use std::env;
use std::fs;
use std::process;

use policy::gate_r::gate_r;
use policy::skim_pol::skim_pol;
use policy::{RowR, SlotR};

const MARK_PATH: &str = "/app/data/revoke/current.rl";
const BOUND_PATH: &str = "/app/data/revoke/window.toml";

fn read_marks(path: &str) -> Vec<String> {
    match fs::read_to_string(path) {
        Ok(text) => text
            .lines()
            .map(|l| l.trim().to_string())
            .filter(|l| !l.is_empty())
            .collect(),
        Err(_) => Vec::new(),
    }
}

fn read_bounds(path: &str) -> (i64, i64) {
    let mut lo = 0i64;
    let mut hi = 0i64;
    if let Ok(text) = fs::read_to_string(path) {
        for line in text.lines() {
            let line = line.trim();
            if let Some(rest) = line.strip_prefix("lo=") {
                lo = rest.trim().parse().unwrap_or(0);
            } else if let Some(rest) = line.strip_prefix("hi=") {
                hi = rest.trim().parse().unwrap_or(0);
            }
        }
    }
    (lo, hi)
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 3 {
        eprintln!("usage: polgate <id> <claim>");
        process::exit(2);
    }

    let id = args[1].clone();
    let claim: i64 = args[2].parse().unwrap_or(0);

    if args.len() >= 4 && args[3] == "--surface" {
        let row = RowR {
            id: id.clone(),
            claim,
            marks: Vec::new(),
            lo: 0,
            hi: 0,
        };
        println!("{{\"surface\":{}}}", skim_pol(&row));
        return;
    }

    let marks = read_marks(MARK_PATH);
    let (lo, hi) = read_bounds(BOUND_PATH);

    let row = RowR {
        id,
        claim,
        marks,
        lo,
        hi,
    };
    let mut slot = SlotR::new();
    gate_r(&row, &mut slot);

    println!("{{\"code\":{}}}", slot.code);
}
