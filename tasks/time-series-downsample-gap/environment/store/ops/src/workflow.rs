use std::path::Path;

use anyhow::Result;

use crate::phase::{read_phase_table, validate_order};
use crate::steps_barrier;
use crate::steps_rebuild;
use crate::steps_roll;

pub fn run_roll(root: &Path, cfg: &Path, ks: &str) -> Result<()> {
    steps_roll::run(root, cfg, ks)
}

pub fn run_barrier(root: &Path, cfg: &Path) -> Result<()> {
    steps_barrier::run(root, cfg)
}

pub fn run_rebuild(root: &Path, ks: &str) -> Result<()> {
    steps_rebuild::run(root, ks)
}

pub fn run_workflow(root: &Path, cfg: &Path, ks: &str) -> Result<()> {
    let phases = read_phase_table(cfg)?;
    validate_order(&phases)?;
    for phase in phases {
        match phase.as_str() {
            "roll" => steps_roll::run(root, cfg, ks)?,
            "barrier" => steps_barrier::run(root, cfg)?,
            "rebuild" => steps_rebuild::run(root, ks)?,
            other => anyhow::bail!("unknown phase {other}"),
        }
    }
    Ok(())
}
