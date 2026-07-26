use serde::Deserialize;
use std::collections::HashMap;
use std::fs;

#[derive(Debug, Clone, Deserialize)]
pub struct BatchEvent {
    pub seq: i32,
    pub ts: i64,
    pub syscall: String,
    pub container_id: String,
    pub pid: i32,
    #[serde(default)]
    pub labels: HashMap<String, String>,
}

#[derive(Debug, Clone)]
pub struct RuleDoc {
    pub name: String,
    pub priority: i32,
    pub syscall: String,
    pub rate_limit: i32,
    pub suppression_sec: i64,
    pub scope_prefix: String,
}

pub fn read_batch(path: &str) -> Result<Vec<BatchEvent>, Box<dyn std::error::Error>> {
    let raw = fs::read_to_string(path)?;
    let mut out = Vec::new();
    for line in raw.lines() {
        if line.trim().is_empty() { continue; }
        out.push(serde_json::from_str(line)?);
    }
    Ok(out)
}
