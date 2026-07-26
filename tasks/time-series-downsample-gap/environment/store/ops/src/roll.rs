use std::path::Path;

use anyhow::{Context, Result};
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct AnchorConfig {
    tier_c: u64,
}

pub struct RollReport {
    pub anchor: u64,
    pub ks: String,
    pub prior_gen: u64,
}

pub const TIER_C: &str = "tier_c";

pub fn read_anchor(config_dir: &Path) -> Result<u64> {
    let raw = std::fs::read_to_string(config_dir.join("k9.toml")).context("read k9 table")?;
    let cfg: AnchorConfig = toml::from_str(&raw)?;
    Ok(cfg.tier_c)
}

pub fn exec_m9(data_root: &Path, anchor: u64, ks: &str) -> Result<RollReport> {
    let mut state = store::RuntimeState::load(data_root)?;
    let prior = state.active_gen;
    state.active_gen = anchor;
    state.save(data_root)?;

    let _stripes = manifest::journal::JournalEntry::stripes_at(data_root, ks, anchor)
        .with_context(|| format!("resolve stripes for {ks} at {anchor}"))?;

    Ok(RollReport {
        anchor,
        ks: ks.to_string(),
        prior_gen: prior,
    })
}
