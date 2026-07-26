use serde::Deserialize;
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Deserialize)]
pub struct HopRow {
    pub r#ref: String,
    pub dest: String,
    pub store_key: String,
    pub stage: String,
    pub epoch: i64,
}

pub fn load_jsonl(path: &Path) -> Vec<HopRow> {
    let text = fs::read_to_string(path).unwrap_or_default();
    text.lines()
        .filter(|l| !l.trim().is_empty())
        .filter_map(|l| serde_json::from_str(l).ok())
        .collect()
}
