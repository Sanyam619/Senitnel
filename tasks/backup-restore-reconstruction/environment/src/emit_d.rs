use serde::Deserialize;
use std::fs;
use std::path::Path;

use crate::slot_e::Arms;

#[derive(Debug, Deserialize)]
struct BagC {
    parts: Vec<Tile>,
}

#[derive(Debug, Deserialize, Clone)]
struct Tile {
    #[allow(dead_code)]
    id: String,
    offset: u64,
    seal_ord: u64,
    bytes_hex: String,
}

pub fn fold_z(dir: &Path, pol: &Arms) -> Result<Vec<u8>, String> {
    let raw = fs::read_to_string(dir.join("fragments.json")).map_err(|e| e.to_string())?;
    let ff: BagC = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let mut parts = ff.parts;
    if pol.fragment_order == "seal_ordinal" {
        parts.sort_by_key(|p| p.seal_ord);
    } else {
        parts.sort_by_key(|p| p.offset);
    }
    let mut out = Vec::new();
    for p in &parts {
        let chunk = hex::decode(&p.bytes_hex).map_err(|e| e.to_string())?;
        out.extend_from_slice(&chunk);
    }
    Ok(out)
}
