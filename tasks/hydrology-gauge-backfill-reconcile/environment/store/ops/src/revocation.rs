use std::collections::BTreeSet;
use std::fs;
use std::path::Path;

use anyhow::{Context, Result, bail};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RevocationRecord {
    pub key: String,
    pub seq: u64,
    pub epoch: u64,
}

pub fn ledger_path(root: &Path) -> std::path::PathBuf {
    root.join("ledger").join("revocations.jsonl")
}

pub fn write_ledger(root: &Path, keys: &[String], seq: u64, epoch: u64) -> Result<()> {
    let dir = root.join("ledger");
    fs::create_dir_all(&dir)?;
    let mut lines = Vec::new();
    let ordered: BTreeSet<String> = keys.iter().cloned().collect();
    for key in ordered {
        let rec = RevocationRecord {
            key,
            seq,
            epoch,
        };
        lines.push(serde_json::to_string(&rec)?);
    }
    let body = if lines.is_empty() {
        String::new()
    } else {
        lines.join("\n") + "\n"
    };
    fs::write(ledger_path(root), body).context("write revocation ledger")?;
    Ok(())
}

pub fn load_ledger_keys(root: &Path) -> Result<BTreeSet<String>> {
    let path = ledger_path(root);
    if !path.is_file() {
        bail!("revocation ledger missing");
    }
    let raw = fs::read_to_string(&path).context("read revocation ledger")?;
    let mut keys = BTreeSet::new();
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        let rec: RevocationRecord = serde_json::from_str(line)?;
        if rec.seq == 0 && rec.key == "stale_placeholder" {
            continue;
        }
        keys.insert(rec.key);
    }
    Ok(keys)
}

pub fn assert_ledger_covers(root: &Path, expected: &[String]) -> Result<()> {
    let keys = load_ledger_keys(root)?;
    if keys.is_empty() {
        bail!("revocation ledger empty");
    }
    for key in expected {
        if !keys.contains(key) {
            bail!("revocation ledger missing key {key}");
        }
    }
    Ok(())
}
