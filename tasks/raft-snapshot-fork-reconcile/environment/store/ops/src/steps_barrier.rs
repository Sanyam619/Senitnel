use std::path::Path;

use anyhow::Result;

use crate::barrier::{apply_k2, read_seq_cutoff};

pub fn run(root: &Path, cfg: &Path) -> Result<()> {
    let cutoff = read_seq_cutoff(cfg)?;
    let state = apply_k2(&root.join("wal"), cutoff)?;
    let mut runtime = store::RuntimeState::load(root)?;
    runtime.wal_seq = state.applied_seq;
    runtime.tombstone_keys = state.tombstones.into_iter().collect();
    runtime.tombstone_seq = cutoff;
    runtime.save(root)?;
    println!("barrier applied at {}", cutoff);
    Ok(())
}
