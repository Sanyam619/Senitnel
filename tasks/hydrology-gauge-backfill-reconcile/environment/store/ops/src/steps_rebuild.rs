use std::path::Path;

use anyhow::Result;
use index::run_p4;

pub fn run(root: &Path, ks: &str) -> Result<()> {
    let runtime = store::RuntimeState::load(root)?;
    let digest = run_p4(
        root,
        ks,
        runtime.active_gen,
        &runtime.tombstone_keys,
        runtime.wal_seq,
        runtime.tombstone_seq,
    )?;
    let mut rt = runtime;
    rt.sidecar_gen.insert(ks.to_string(), rt.active_gen);
    rt.save(root)?;
    println!(
        "rebuilt {} digest {} segments {}",
        ks, digest.hex, digest.segment_count
    );
    Ok(())
}
