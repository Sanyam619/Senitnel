use std::fs;
use std::path::Path;

use anyhow::{Context, Result};
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct PhaseTable {
    phases: Vec<String>,
}

pub fn read_phase_table(config_dir: &Path) -> Result<Vec<String>> {
    let raw = fs::read_to_string(config_dir.join("p7.toml")).context("read p7 table")?;
    let table: PhaseTable = toml::from_str(&raw)?;
    Ok(table.phases)
}

pub fn validate_order(phases: &[String]) -> Result<()> {
    let pos = |name: &str| phases.iter().position(|p| p == name);
    if let (Some(roll), Some(barrier)) = (pos("roll"), pos("barrier")) {
        if roll >= barrier {
            anyhow::bail!("roll must precede barrier");
        }
    }
    if let (Some(barrier), Some(rebuild)) = (pos("barrier"), pos("rebuild")) {
        if barrier >= rebuild {
            anyhow::bail!("barrier must precede rebuild");
        }
    }
    if let (Some(roll), Some(rebuild)) = (pos("roll"), pos("rebuild")) {
        if roll >= rebuild {
            anyhow::bail!("roll must precede rebuild");
        }
    }
    Ok(())
}
