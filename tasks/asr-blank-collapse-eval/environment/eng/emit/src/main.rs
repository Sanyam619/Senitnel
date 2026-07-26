use std::fs;
use std::path::{Path, PathBuf};

use asr_core::collapse::fold_c;
use asr_core::frame::{sheet, stack};
use asr_core::glyph::{lines, Lex};
use asr_core::join::step_j;
use asr_core::span::batches;
use asr_core::tally::Meter;
use asr_rank::bind::seat;
use asr_rank::dial::trace;

const TAG: &str = "asr-eval-v3";

struct Target {
    id: String,
    lo_unit: f64,
    hi_unit: f64,
    lo_char: f64,
    hi_char: f64,
}

fn targets(root: &Path) -> Vec<Target> {
    let path = root.join("docs/asr_bands.md");
    let text = fs::read_to_string(&path).unwrap_or_else(|e| panic!("{}: {e}", path.display()));
    let mut out = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if !line.starts_with('|') {
            continue;
        }
        let cells: Vec<&str> = line
            .trim_matches('|')
            .split('|')
            .map(str::trim)
            .collect();
        if cells.len() != 5 {
            continue;
        }
        let nums: Vec<f64> = cells[1..]
            .iter()
            .filter_map(|c| c.parse::<f64>().ok())
            .collect();
        if nums.len() != 4 {
            continue;
        }
        out.push(Target {
            id: cells[0].to_string(),
            lo_unit: nums[0],
            hi_unit: nums[1],
            lo_char: nums[2],
            hi_char: nums[3],
        });
    }
    assert!(!out.is_empty(), "no published rows in {}", path.display());
    out
}

fn main() {
    let root = PathBuf::from(std::env::var("ASR_ROOT").unwrap_or_else(|_| "/app".to_string()));
    let held = seat(&root);
    let shape = trace(&root);
    let lex = Lex::load(&root.join("data/lexicon/tokens.txt"));
    let prior = sheet(&root.join("data/lm/bigram.bin"), b"LMB1");
    let state = sheet(&root.join("data/predict/bias.bin"), b"PRD1");
    assert_eq!(prior.len(), lex.width(), "conditioning table width");
    assert_eq!(state.len(), lex.width(), "prediction table width");

    let mut body = String::new();
    let mut clean = true;
    let mut notes = String::new();
    let plan = targets(&root);
    for (at, target) in plan.iter().enumerate() {
        let refs = lines(&root.join(format!("data/align/{}.txt", target.id)), &lex);
        let mut meter = Meter::new();
        for (from, upto) in batches(refs.len(), shape.width.max(1)) {
            for line in refs[from..upto].iter() {
                let grid = stack(
                    &root.join(format!("data/audio/{}/{}.bin", target.id, line.stem)),
                );
                let hyp = match held.route.as_str() {
                    "ctc_collapse" => fold_c(&grid, &prior, held.weight),
                    "rnnt_join" => step_j(&grid, &prior, &state, held.weight),
                    other => panic!("unknown decode route {other}"),
                };
                if shape.stream == "on" {
                    notes.push_str(&format!(
                        "{} {} {}\n",
                        target.id,
                        line.stem,
                        lex.text(&hyp).join(" ")
                    ));
                }
                meter.add(&lex.text(&hyp), &lex.text(&line.units));
            }
        }
        let unit = meter.unit_rate();
        let ch = meter.char_rate();
        if unit < target.lo_unit || unit > target.hi_unit {
            clean = false;
        }
        if ch < target.lo_char || ch > target.hi_char {
            clean = false;
        }
        body.push_str("    {\n");
        body.push_str(&format!("      \"id\": \"{}\",\n", target.id));
        body.push_str(&format!("      \"wer\": {unit:.12},\n"));
        body.push_str(&format!("      \"cer\": {ch:.12},\n"));
        body.push_str(&format!("      \"blank_mode\": \"{}\",\n", held.route));
        body.push_str(&format!("      \"lm_weight\": {:.6},\n", held.weight));
        body.push_str(&format!("      \"tip_epoch\": {}\n", held.at));
        body.push_str("    }");
        if at + 1 < plan.len() {
            body.push(',');
        }
        body.push('\n');
    }

    let report = format!(
        "{{\n  \"schema_tag\": \"{TAG}\",\n  \"slices\": [\n{body}  ],\n  \"eval_ok\": {clean}\n}}\n"
    );
    fs::create_dir_all("/output").expect("output directory");
    fs::write("/output/asr-eval.json", report).expect("publish report");
    if shape.stream == "on" {
        fs::write("/output/asr-eval-trace.txt", notes).expect("publish trace");
    }
}
