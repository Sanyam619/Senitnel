use bevel_core::base::read_marks;
use std::path::Path;

pub fn facet_q(idx: u32, root: &Path) -> f64 {
    let marks = read_marks(&root.join("feature_registry/tip_journal.jsonl"));
    let fam = marks
        .iter()
        .max_by_key(|m| m.idx)
        .map(|m| m.sheet.clone())
        .unwrap_or_default();
    let table = root.join("sched").join(format!("table_{fam}.toml"));
    row_of(&table, idx)
}

fn row_of(path: &Path, idx: u32) -> f64 {
    let text = std::fs::read_to_string(path).unwrap_or_default();
    let key = format!("\"{idx}\"");
    for line in text.lines() {
        let line = line.trim();
        if let Some(rest) = line.strip_prefix(&key) {
            let rest = rest.trim_start();
            if let Some(rest) = rest.strip_prefix('=') {
                if let Ok(v) = rest.trim().parse::<f64>() {
                    return v;
                }
            }
        }
    }
    0.0
}
