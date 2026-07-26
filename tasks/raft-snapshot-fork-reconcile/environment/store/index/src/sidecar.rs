use std::collections::HashMap;
use std::fs;
use std::path::Path;

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SidecarFile {
    pub bound_gen: u64,
    pub map: HashMap<String, u64>,
    pub digest: String,
}

pub fn load(root: &Path, ks: &str) -> Result<SidecarFile> {
    let path = root.join("sidecars").join(format!("{ks}.idx"));
    let raw = fs::read_to_string(path).context("read sidecar")?;
    Ok(serde_json::from_str(&raw)?)
}

pub fn save(root: &Path, ks: &str, sidecar: &SidecarFile) -> Result<()> {
    let path = root.join("sidecars").join(format!("{ks}.idx"));
    fs::write(path, serde_json::to_string_pretty(sidecar)?)?;
    Ok(())
}
