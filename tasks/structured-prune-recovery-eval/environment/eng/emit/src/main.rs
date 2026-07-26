//! Publishes the evaluation report for the desk's roster.

use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

use prune_lane::{Cell, Desk};

const TAG: &str = "prune-eval-v2";
const OUT: &str = "/output/prune-eval.json";
const PLACES: usize = 12;

struct Limits {
    per_id: HashMap<String, (f64, f64)>,
    dropped: (f64, f64),
    kept: (f64, f64),
}

fn cut(line: &str) -> Vec<String> {
    line.trim()
        .trim_matches('|')
        .split('|')
        .map(|c| c.trim().to_string())
        .collect()
}

fn limits(path: &Path) -> Limits {
    let text = fs::read_to_string(path)
        .unwrap_or_else(|e| panic!("cannot read the published bands: {e}"));
    let mut out = Limits {
        per_id: HashMap::new(),
        dropped: (f64::NAN, f64::NAN),
        kept: (f64::NAN, f64::NAN),
    };
    for line in text.lines() {
        if !line.trim_start().starts_with('|') {
            continue;
        }
        let cells = cut(line);
        if cells.len() != 3 {
            continue;
        }
        let lo = cells[1].parse::<f64>();
        let hi = cells[2].parse::<f64>();
        if let (Ok(lo), Ok(hi)) = (lo, hi) {
            match cells[0].as_str() {
                "sparsity" => out.dropped = (lo, hi),
                "flops_frac" => out.kept = (lo, hi),
                key => {
                    out.per_id.insert(key.to_string(), (lo, hi));
                }
            }
        }
    }
    out
}

fn inside(v: f64, band: (f64, f64)) -> bool {
    band.0 <= v && v <= band.1
}

fn settled(cells: &[Cell], bands: &Limits) -> bool {
    for cell in cells {
        let Some(&band) = bands.per_id.get(&cell.id) else {
            return false;
        };
        if !inside(cell.accuracy, band)
            || !inside(cell.dropped, bands.dropped)
            || !inside(cell.kept, bands.kept)
        {
            return false;
        }
    }
    true
}

fn main() {
    let root = PathBuf::from(std::env::var("PRUNE_ROOT").unwrap_or_else(|_| "/app".to_string()));
    let desk = Desk::open(&root);
    let cells = desk.cells();
    let bands = limits(&root.join("docs/prune_bands.md"));

    let mut text = String::new();
    text.push_str("{\n");
    text.push_str(&format!("  \"schema_tag\": \"{TAG}\",\n"));
    text.push_str("  \"scenarios\": [\n");
    for (at, cell) in cells.iter().enumerate() {
        text.push_str("    {\n");
        text.push_str(&format!("      \"id\": \"{}\",\n", cell.id));
        text.push_str(&format!(
            "      \"accuracy\": {:.*},\n",
            PLACES, cell.accuracy
        ));
        text.push_str(&format!(
            "      \"sparsity\": {:.*},\n",
            PLACES, cell.dropped
        ));
        text.push_str(&format!(
            "      \"flops_frac\": {:.*},\n",
            PLACES, cell.kept
        ));
        text.push_str(&format!("      \"mask_tip\": {}\n", cell.epoch));
        text.push_str(if at + 1 == cells.len() {
            "    }\n"
        } else {
            "    },\n"
        });
    }
    text.push_str("  ],\n");
    text.push_str(&format!(
        "  \"bands_ok\": {}\n",
        settled(&cells, &bands)
    ));
    text.push_str("}\n");

    let out = Path::new(OUT);
    if let Some(dir) = out.parent() {
        fs::create_dir_all(dir).unwrap_or_else(|e| panic!("cannot open {}: {e}", dir.display()));
    }
    fs::write(out, text.as_bytes()).unwrap_or_else(|e| panic!("cannot publish {OUT}: {e}"));
    println!("published {OUT} for {} scenarios", cells.len());
}
