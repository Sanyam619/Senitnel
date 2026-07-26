use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize)]
pub struct LeafRow {
    pub id: String,
    pub payload: String,
    pub since: u64,
}

#[derive(Debug, Deserialize)]
pub struct RuntimeState {
    pub active_gen: u64,
    pub last_sync_gen: u64,
    pub journal_head: u64,
}

#[derive(Debug, Serialize)]
pub struct SyncReport {
    pub branch_gen: u64,
    pub root_digest: String,
    pub leaves: BTreeMap<String, String>,
}

pub fn canonical_leaf(id: &str, payload: &str) -> String {
    format!(r#"{{"id":"{id}","payload":"{payload}"}}"#)
}

pub fn leaf_hash(id: &str, payload: &str) -> String {
    let body = canonical_leaf(id, payload);
    let mut h = Sha256::new();
    h.update(body.as_bytes());
    hex::encode(h.finalize())
}

pub fn load_leaves(dir: &Path) -> std::io::Result<Vec<LeafRow>> {
    let mut rows = Vec::new();
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        if !entry.path().extension().map(|e| e == "json").unwrap_or(false) {
            continue;
        }
        let raw = fs::read_to_string(entry.path())?;
        let row: LeafRow = serde_json::from_str(&raw)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
        rows.push(row);
    }
    rows.sort_by(|a, b| a.id.cmp(&b.id));
    Ok(rows)
}

pub fn visible_at(rows: &[LeafRow], branch: u64) -> BTreeMap<String, String> {
    let mut out = BTreeMap::new();
    for row in rows {
        if row.since <= branch {
            out.insert(row.id.clone(), leaf_hash(&row.id, &row.payload));
        }
    }
    out
}

pub fn merkle_root(leaves: &BTreeMap<String, String>) -> String {
    let mut layer: Vec<String> = leaves.values().cloned().collect();
    if layer.is_empty() {
        let mut h = Sha256::new();
        return hex::encode(h.finalize());
    }
    while layer.len() > 1 {
        let mut next = Vec::new();
        let mut idx = 0;
        while idx < layer.len() {
            let left = &layer[idx];
            let right = if idx + 1 < layer.len() {
                &layer[idx + 1]
            } else {
                &layer[idx]
            };
            let left_bytes = hex::decode(left).unwrap_or_default();
            let right_bytes = hex::decode(right).unwrap_or_default();
            let mut h = Sha256::new();
            h.update(&left_bytes);
            h.update(&right_bytes);
            next.push(hex::encode(h.finalize()));
            idx += 2;
        }
        layer = next;
    }
    layer[0].clone()
}

pub fn read_runtime(path: &Path) -> std::io::Result<RuntimeState> {
    let raw = fs::read_to_string(path)?;
    Ok(serde_json::from_str(&raw)?)
}

pub fn read_branch_cap(config_dir: &Path) -> std::io::Result<u64> {
    let path = config_dir.join("k9.toml");
    let raw = fs::read_to_string(path)?;
    for line in raw.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("branch_cap") {
            let rhs = trimmed.split('=').nth(1).unwrap_or("0").trim();
            return Ok(rhs.parse().unwrap_or(0));
        }
    }
    Ok(0)
}

pub fn branch_cut(state: &RuntimeState, cap: u64) -> u64 {
    let mut g = state.last_sync_gen;
    if cap > 0 && cap < g {
        g = cap;
    }
    if g > state.active_gen {
        g = state.active_gen;
    }
    g
}

pub fn build_report(data_root: &Path, config_dir: &Path) -> std::io::Result<SyncReport> {
    let leaves_dir = data_root.join("leaves");
    let runtime = read_runtime(&data_root.join("state/runtime.json"))?;
    let cap = read_branch_cap(config_dir)?;
    let branch = branch_cut(&runtime, cap);
    let rows = load_leaves(&leaves_dir)?;
    let leaf_map = visible_at(&rows, branch);
    let root = merkle_root(&leaf_map);
    Ok(SyncReport {
        branch_gen: branch,
        root_digest: root,
        leaves: leaf_map,
    })
}
