use bevel_core::base::read_marks;
use std::path::Path;

pub struct SheetRow {
    pub cfg: f64,
    pub sampler: String,
}

pub fn facet_q(idx: u32, root: &Path) -> SheetRow {
    let marks = read_marks(&root.join("feature_registry/tip_journal.jsonl"));
    let fam = marks
        .iter()
        .max_by_key(|m| m.idx)
        .map(|m| m.sheet.clone())
        .unwrap_or_default();
    let table = root.join("sched").join(format!("table_{fam}.toml"));
    row_of(&table, idx)
}

fn row_of(path: &Path, idx: u32) -> SheetRow {
    let text = std::fs::read_to_string(path).unwrap_or_default();
    let key = format!("\"{idx}\"");
    let mut cfg = 0.0f64;
    let mut sampler = String::new();
    let mut section = "";
    for line in text.lines() {
        let line = line.trim();
        if line == "[cfg]" {
            section = "cfg";
            continue;
        }
        if line == "[sampler]" {
            section = "sampler";
            continue;
        }
        if let Some(rest) = line.strip_prefix(&key) {
            let rest = rest.trim_start();
            if let Some(rest) = rest.strip_prefix('=') {
                let rest = rest.trim();
                if section == "cfg" {
                    if let Ok(v) = rest.parse::<f64>() {
                        cfg = v;
                    }
                } else if section == "sampler" {
                    sampler = rest.trim_matches('"').to_string();
                }
            }
        }
    }
    SheetRow { cfg, sampler }
}
