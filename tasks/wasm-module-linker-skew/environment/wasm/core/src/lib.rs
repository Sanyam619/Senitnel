use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize)]
pub struct RuntimeState {
    pub active_epoch: u64,
    pub last_link_epoch: u64,
    pub manifest_head: u64,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct ModuleSpec {
    pub id: String,
    pub version: u64,
    pub exports: Vec<String>,
    #[serde(default)]
    pub imports: Vec<ImportRow>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct ImportRow {
    pub module: String,
    pub field: String,
    pub bind: String,
}

#[derive(Debug, Serialize)]
pub struct ModuleView {
    pub version: u64,
    pub digest: String,
}

#[derive(Debug, Serialize)]
pub struct ImportBind {
    pub import: String,
    pub slot: u64,
    pub bound: String,
}

#[derive(Debug, Serialize)]
pub struct LinkDoc {
    pub epoch: u64,
    pub graph_digest: String,
    pub modules: BTreeMap<String, ModuleView>,
    pub imports: Vec<ImportBind>,
}

pub fn epoch_cut(state: &RuntimeState, cap: u64) -> u64 {
    let mut e = state.last_link_epoch;
    if cap > 0 && cap < e {
        e = cap;
    }
    if e > state.active_epoch {
        e = state.active_epoch;
    }
    e
}

pub fn load_slot(modules_dir: &Path, module_id: &str, slot: u64) -> Result<ModuleSpec, String> {
    let path = modules_dir.join(format!("{module_id}.slot{slot}.json"));
    let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

fn module_digest(path: &Path) -> Result<String, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let val: serde_json::Value = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let canon = canonical_json(&val);
    Ok(hex::encode(Sha256::digest(canon.as_bytes())))
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

fn visible_ids(epoch: u64) -> Vec<&'static str> {
    let mut out = Vec::new();
    if epoch >= 1 {
        out.push("codec");
        out.push("host");
    }
    if epoch >= 3 {
        out.push("filter");
    }
    out.sort();
    out
}

pub fn resolve_graph(data_root: &Path, epoch: u64) -> Result<LinkDoc, String> {
    let modules_dir = data_root.join("modules");
    let mut modules = BTreeMap::new();
    let mut dep_versions = BTreeMap::new();
    for mid in visible_ids(epoch) {
        let path = modules_dir.join(format!("{mid}.slot{epoch}.json"));
        let spec = load_slot(&modules_dir, mid, epoch)?;
        let digest = module_digest(&path)?;
        dep_versions.insert(mid.to_string(), epoch);
        modules.insert(
            mid.to_string(),
            ModuleView {
                version: epoch,
                digest,
            },
        );
    }
    let mut imports = Vec::new();
    if let Ok(host) = load_slot(&modules_dir, "host", epoch) {
        for row in host.imports {
            let dep = row.module.clone();
            let slot = dep_versions.get(&dep).copied().unwrap_or(0);
            if slot == 0 {
                continue;
            }
            imports.push(ImportBind {
                import: format!("{}.{}" , dep, row.field),
                slot,
                bound: row.bind,
            });
        }
    }
    imports.sort_by(|a, b| a.import.cmp(&b.import));
    let canon_val = serde_json::json!({
        "epoch": epoch,
        "modules": &modules,
        "imports": &imports,
    });
    let digest = hex::encode(Sha256::digest(canonical_json(&canon_val).as_bytes()));
    Ok(LinkDoc {
        epoch,
        graph_digest: digest,
        modules,
        imports,
    })
}

pub fn write_report(out_path: &Path, data_root: &Path) -> Result<(), String> {
    let state_path = data_root.join("state/runtime.json");
    let raw = fs::read_to_string(&state_path).map_err(|e| e.to_string())?;
    let state: RuntimeState = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let cap = read_cap(data_root)?;
    let epoch = epoch_cut(&state, cap);
    let doc = resolve_graph(data_root, epoch)?;
    let payload = serde_json::to_string_pretty(&doc).map_err(|e| e.to_string())?;
    if let Some(parent) = out_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(out_path, format!("{payload}\n")).map_err(|e| e.to_string())
}

fn read_cap(data_root: &Path) -> Result<u64, String> {
    let cfg_dir = Path::new("/app/config/l7");
    for entry in fs::read_dir(cfg_dir).map_err(|e| e.to_string())? {
        let entry = entry.map_err(|e| e.to_string())?;
        if entry.file_name() != "k9.toml" {
            continue;
        }
        let text = fs::read_to_string(entry.path()).map_err(|e| e.to_string())?;
        for line in text.lines() {
            let trimmed = line.trim();
            if !trimmed.starts_with("link_epoch_cap") {
                continue;
            }
            let val = trimmed.split('=').nth(1).unwrap_or("0").trim();
            return val.parse().map_err(|e| format!("cap: {e}"));
        }
    }
    Ok(0)
}
