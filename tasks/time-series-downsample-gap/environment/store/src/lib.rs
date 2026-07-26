pub mod column_reader;
pub mod merge_scheduler;
pub mod rollup;

use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};

pub const DATA_ROOT: &str = "/app/data";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RuntimeState {
    pub active_gen: u64,
    #[serde(default)]
    pub ceiling_gen: u64,
    pub wal_seq: u64,
    pub sidecar_gen: HashMap<String, u64>,
    pub tombstone_keys: Vec<String>,
    pub tombstone_seq: u64,
}

impl RuntimeState {
    pub fn load(root: &Path) -> Result<Self> {
        let raw = fs::read_to_string(root.join("state/runtime.json"))
            .context("read runtime state")?;
        Ok(serde_json::from_str(&raw)?)
    }

    pub fn save(&self, root: &Path) -> Result<()> {
        let path = root.join("state/runtime.json");
        fs::write(path, serde_json::to_string_pretty(self)?)?;
        Ok(())
    }
}

pub fn data_root() -> PathBuf {
    PathBuf::from(DATA_ROOT)
}

pub fn recovery_dir() -> PathBuf {
    PathBuf::from("/app/config/l7")
}

pub fn stripe_path(root: &Path, ns: &str, stripe_id: u64) -> PathBuf {
    if stripe_id == 99 {
        root.join("columns").join(format!("{ns}_merged.col"))
    } else {
        root.join("columns").join(format!("{ns}_{stripe_id:03}.col"))
    }
}

pub fn sidecar_path(root: &Path, ns: &str) -> PathBuf {
    root.join("sidecars").join(format!("{ns}.idx"))
}
