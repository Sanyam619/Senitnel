use std::path::Path;

use anyhow::Result;

pub fn schedule_forward(_root: &Path, _ks: &str) -> Result<()> {
  anyhow::bail!("forward compaction disabled during recovery window")
}
