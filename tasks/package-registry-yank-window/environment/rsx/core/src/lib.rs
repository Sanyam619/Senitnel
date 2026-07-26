mod k_net;
mod q_slot;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize)]
pub struct RuntimeState {
    pub active_gen: u64,
    pub snapshot_head: u64,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct DepRow {
    #[serde(rename = "crate")]
    pub crate_name: String,
    pub version: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub kind: Option<String>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct VersionRow {
    pub name: String,
    pub vers: String,
    pub gen: u64,
    pub deps: Vec<DepRow>,
    pub cksum: String,
}

#[derive(Debug, Serialize)]
pub struct InstallableRow {
    #[serde(rename = "crate")]
    pub crate_name: String,
    pub version: String,
}

#[derive(Debug, Serialize)]
pub struct YankedRow {
    #[serde(rename = "crate")]
    pub crate_name: String,
    pub version: String,
}

#[derive(Debug, Serialize)]
pub struct ReconcileDoc {
    pub snapshot_gen: u64,
    pub index_digest: String,
    pub installable: Vec<InstallableRow>,
    pub yanked: Vec<YankedRow>,
    pub advisory_digest: String,
}

fn canonical_json(value: &serde_json::Value) -> String {
    match value {
        serde_json::Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            let body: Vec<String> = keys
                .iter()
                .map(|k| format!("\"{k}\":{}", canonical_json(&map[*k])))
                .collect();
            format!("{{{}}}", body.join(","))
        }
        serde_json::Value::Array(items) => {
            let body: Vec<String> = items.iter().map(canonical_json).collect();
            format!("[{}]", body.join(","))
        }
        serde_json::Value::String(s) => format!("\"{}\"", s.replace('\\', "\\\\").replace('"', "\\\"")),
        serde_json::Value::Number(n) => n.to_string(),
        serde_json::Value::Bool(b) => b.to_string(),
        serde_json::Value::Null => "null".to_string(),
    }
}

fn read_adv_live_only() -> bool {
    let text = fs::read_to_string("/app/config/l7/k9.toml").unwrap_or_default();
    for line in text.lines() {
        let trimmed = line.trim();
        if !trimmed.starts_with("adv_live_only") {
            continue;
        }
        return trimmed.split('=').nth(1).unwrap_or("false").trim() == "true";
    }
    false
}

fn read_adv_floor() -> String {
    let text = fs::read_to_string("/app/config/l7/k9.toml").unwrap_or_default();
    for line in text.lines() {
        let trimmed = line.trim();
        if !trimmed.starts_with("adv_floor") {
            continue;
        }
        return trimmed
            .split('=')
            .nth(1)
            .unwrap_or("\"low\"")
            .trim()
            .trim_matches('"')
            .to_string();
    }
    "low".to_string()
}

fn sev_rank(s: &str) -> u8 {
    match s {
        "critical" => 4,
        "high" => 3,
        "medium" => 2,
        "low" => 1,
        _ => 0,
    }
}

fn load_versions(data_root: &Path, gen: u64) -> Result<Vec<VersionRow>, String> {
    let mut rows = Vec::new();
    let crates_dir = data_root.join("crates");
    for entry in fs::read_dir(&crates_dir).map_err(|e| e.to_string())? {
        let entry = entry.map_err(|e| e.to_string())?;
        if !entry.path().is_dir() {
            continue;
        }
        for file in fs::read_dir(entry.path()).map_err(|e| e.to_string())? {
            let file = file.map_err(|e| e.to_string())?;
            let path = file.path();
            if path.extension().and_then(|s| s.to_str()) != Some("json") {
                continue;
            }
            let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
            let row: VersionRow = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
            if row.gen <= gen {
                rows.push(row);
            }
        }
    }
    rows.sort_by(|a, b| (a.name.as_str(), a.vers.as_str()).cmp(&(b.name.as_str(), b.vers.as_str())));
    Ok(rows)
}

fn load_advisories(data_root: &Path) -> Result<Vec<serde_json::Value>, String> {
    let raw = fs::read_to_string(data_root.join("advisories/feed.jsonl")).map_err(|e| e.to_string())?;
    let mut out = Vec::new();
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        out.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    Ok(out)
}

pub fn resolve_index(data_root: &Path, gen: u64) -> Result<ReconcileDoc, String> {
    let live_only = read_adv_live_only();
    let floor = read_adv_floor();
    let entries = load_versions(data_root, gen)?;
    let yanked_set = q_slot::active_yank_set(data_root, gen)?;

    let installable_keys = k_net::installable_rows(&entries, &yanked_set);
    let installable: Vec<InstallableRow> = installable_keys
        .into_iter()
        .map(|(c, v)| InstallableRow {
            crate_name: c,
            version: v,
        })
        .collect();

    let yanked: Vec<YankedRow> = yanked_set
        .iter()
        .map(|(c, v)| YankedRow {
            crate_name: c.clone(),
            version: v.clone(),
        })
        .collect();

    let floor_rank = sev_rank(&floor);
    let _ = floor_rank;
    let mut advisories = Vec::new();
    for adv in load_advisories(data_root)? {
        let crate_name = adv.get("crate").and_then(|v| v.as_str()).unwrap_or("").to_string();
        let vers = adv.get("vers").and_then(|v| v.as_str()).unwrap_or("").to_string();
        let from = adv.get("from").and_then(|v| v.as_u64()).unwrap_or(0);
        let sev = adv.get("severity").and_then(|v| v.as_str()).unwrap_or("low");
        if from > gen {
            continue;
        }
        if live_only && !yanked_set.contains(&(crate_name.clone(), vers.clone())) {
            continue;
        }
        let _ = sev;
        advisories.push(adv);
    }
    advisories.sort_by(|a, b| {
        let ac = a.get("crate").and_then(|v| v.as_str()).unwrap_or("");
        let bc = b.get("crate").and_then(|v| v.as_str()).unwrap_or("");
        let av = a.get("vers").and_then(|v| v.as_str()).unwrap_or("");
        let bv = b.get("vers").and_then(|v| v.as_str()).unwrap_or("");
        (ac, av).cmp(&(bc, bv))
    });

    let entries_json: Vec<serde_json::Value> = entries
        .iter()
        .map(|r| {
            serde_json::json!({
                "name": r.name,
                "vers": r.vers,
                "gen": r.gen,
                "deps": r.deps,
                "cksum": r.cksum,
            })
        })
        .collect();
    let yanked_json: Vec<serde_json::Value> = yanked
        .iter()
        .map(|r| serde_json::json!({"crate": r.crate_name, "version": r.version}))
        .collect();

    let canon = serde_json::json!({
        "gen": gen,
        "entries": entries_json,
        "yanked": yanked_json,
        "advisories": advisories,
    });
    let index_digest = hex::encode(Sha256::digest(canonical_json(&canon).as_bytes()));
    let adv_canon = serde_json::json!({"advisories": advisories});
    let advisory_digest = hex::encode(Sha256::digest(canonical_json(&adv_canon).as_bytes()));

    Ok(ReconcileDoc {
        snapshot_gen: gen,
        index_digest,
        installable,
        yanked,
        advisory_digest,
    })
}

pub fn write_report(out_path: &Path, data_root: &Path) -> Result<(), String> {
    let raw = fs::read_to_string(data_root.join("state/runtime.json")).map_err(|e| e.to_string())?;
    let state: RuntimeState = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let gen = state.active_gen;
    let doc = resolve_index(data_root, gen)?;
    let payload = serde_json::to_string_pretty(&doc).map_err(|e| e.to_string())?;
    if let Some(parent) = out_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(out_path, format!("{payload}\n")).map_err(|e| e.to_string())
}
