//! Publishes the INT4 weight-only evaluation report.

use std::fs;
use std::path::{Path, PathBuf};

use q4_core::root;
use q4_pane::run;

struct Band {
    id: String,
    ppl_lo: f64,
    ppl_hi: f64,
    top_lo: f64,
    top_hi: f64,
}

fn bands(path: &Path) -> Vec<Band> {
    let text = match fs::read_to_string(path) {
        Ok(v) => v,
        Err(e) => panic!("cannot read {}: {e}", path.display()),
    };
    let mut out = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if !line.starts_with('|') {
            continue;
        }
        let cols: Vec<&str> = line
            .trim_matches('|')
            .split('|')
            .map(|c| c.trim())
            .collect();
        if cols.len() != 5 {
            continue;
        }
        let nums: Vec<f64> = cols[1..]
            .iter()
            .filter_map(|c| c.parse::<f64>().ok())
            .collect();
        if nums.len() != 4 {
            continue;
        }
        out.push(Band {
            id: cols[0].to_string(),
            ppl_lo: nums[0],
            ppl_hi: nums[1],
            top_lo: nums[2],
            top_hi: nums[3],
        });
    }
    assert!(!out.is_empty(), "no published bands");
    out
}

fn out_path() -> PathBuf {
    match std::env::var("Q4_OUT") {
        Ok(v) => PathBuf::from(v),
        Err(_) => PathBuf::from("/output/int4-eval.json"),
    }
}

fn main() {
    let root = root();
    let desk = run::open(&root);
    let cards = run::score(&desk);
    let table = bands(&root.join("docs/int4_bands.md"));

    let mut ok = true;
    let mut body = String::new();
    body.push_str("{\n  \"schema_tag\": \"int4-eval-v1\",\n  \"scenarios\": [\n");
    for (at, card) in cards.iter().enumerate() {
        let hit = table.iter().find(|b| b.id == card.id);
        match hit {
            Some(b) => {
                if card.perplexity < b.ppl_lo
                    || card.perplexity > b.ppl_hi
                    || card.top1 < b.top_lo
                    || card.top1 > b.top_hi
                {
                    ok = false;
                }
            }
            None => ok = false,
        }
        body.push_str(&format!(
            "    {{\"id\": \"{}\", \"perplexity\": {:.9}, \"top1\": {:.9}, \"group_size\": {}, \"tip_epoch\": {}}}{}\n",
            card.id,
            card.perplexity,
            card.top1,
            card.group_size,
            card.tip_epoch,
            if at + 1 == cards.len() { "" } else { "," }
        ));
    }
    body.push_str(&format!("  ],\n  \"bands_ok\": {ok}\n}}\n"));

    let dest = out_path();
    if let Some(parent) = dest.parent() {
        let _ = fs::create_dir_all(parent);
    }
    if let Err(e) = fs::write(&dest, body) {
        panic!("cannot publish {}: {e}", dest.display());
    }
    println!(
        "published {} scenarios under generation {} (epoch {}, width {}) over {} calibration rows",
        cards.len(),
        desk.row.name,
        desk.row.epoch,
        desk.grid.group,
        desk.rows.len()
    );
    println!("shards {}", desk.shards.join(","));
}
