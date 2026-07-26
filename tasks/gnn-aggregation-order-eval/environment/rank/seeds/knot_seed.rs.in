use std::collections::HashSet;
use std::path::Path;

use loam_core::base::Mark;

pub fn knot_r(marks: &[Mark], _retired: &HashSet<String>) -> u32 {
    let mut top = 0u32;
    for m in marks {
        if m.idx > top {
            top = m.idx;
        }
    }
    top
}

pub fn read_retired(path: &Path) -> HashSet<String> {
    let text = std::fs::read_to_string(path).unwrap_or_default();
    let mut out = HashSet::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        if let Some(i) = line.find("\"tip\"") {
            let rest = &line[i + 5..];
            let rest = rest.trim_start().trim_start_matches(':').trim_start();
            if let Some(rest) = rest.strip_prefix('"') {
                if let Some(end) = rest.find('"') {
                    out.insert(rest[..end].to_string());
                }
            }
        }
    }
    out
}
