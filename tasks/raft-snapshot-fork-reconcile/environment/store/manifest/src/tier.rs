use std::path::Path;

use anyhow::Result;

pub fn promote_forward(_root: &Path, _ns: &str) -> Result<u64> {
    anyhow::bail!("tier promotion is forward-only")
}
