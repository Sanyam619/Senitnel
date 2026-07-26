use std::fs;
use std::path::Path;

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JournalEntry {
    pub gen: u64,
    pub ns: String,
    pub stripes: Vec<u64>,
}

impl JournalEntry {
    pub fn load_chain(root: &Path) -> Result<Vec<Self>> {
        let mut out = Vec::new();
        for name in ["tier_a.jsonl", "tier_b.jsonl", "tier_c.jsonl"] {
            let path = root.join("manifests").join(name);
            let raw = fs::read_to_string(&path).with_context(|| format!("read {name}"))?;
            for line in raw.lines() {
                if line.trim().is_empty() {
                    continue;
                }
                out.push(serde_json::from_str(line)?);
            }
        }
        Ok(out)
    }

    pub fn head_for(root: &Path, ns: &str) -> Result<u64> {
        let entries = Self::load_chain(root)?;
        Ok(entries
            .into_iter()
            .filter(|e| e.ns == ns)
            .map(|e| e.gen)
            .max()
            .unwrap_or(0))
    }

    pub fn stripes_at(root: &Path, ns: &str, gen: u64) -> Result<Vec<u64>> {
        let entries = Self::load_chain(root)?;
        let entry = entries
            .into_iter()
            .filter(|e| e.ns == ns && e.gen <= gen)
            .max_by_key(|e| e.gen)
            .with_context(|| format!("no journal entry for {ns} gen {gen}"))?;
        Ok(entry.stripes)
    }
}
