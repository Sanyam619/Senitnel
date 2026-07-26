use loam_core::base::read_marks;
use std::path::Path;

pub fn facet_q(_idx: u32, root: &Path) -> String {
    let marks = read_marks(&root.join("feature_registry/tip_journal.jsonl"));
    marks
        .iter()
        .max_by_key(|m| m.idx)
        .map(|m| m.agg.clone())
        .unwrap_or_default()
}
