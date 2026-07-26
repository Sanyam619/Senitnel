use std::fs;
use std::path::{Path, PathBuf};

use anyhow::{Context, Result, bail};
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct TrustPolicy {
    pub forbid_merged_stripe: u64,
    pub require_revocation_ledger: bool,
    pub primary_channel: String,
}

impl TrustPolicy {
    pub fn load() -> Result<Self> {
        let path = PathBuf::from("/app/ops/trust_policy.toml");
        let raw = fs::read_to_string(&path).context("read trust policy")?;
        Ok(toml::from_str(&raw)?)
    }
}

pub fn assert_lineage_clean(root: &Path, channel: &str, gen: u64, forbid: u64) -> Result<()> {
    let stripes = manifest::journal::JournalEntry::stripes_at(root, channel, gen)?;
    if stripes.iter().any(|s| *s == forbid) {
        bail!("lineage rejected: gen {gen} includes forbidden stripe {forbid}");
    }
    Ok(())
}
