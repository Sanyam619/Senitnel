use std::path::Path;

use anyhow::Result;

pub fn patch_from_head(_root: &Path, _ks: &str) -> Result<String> {
    anyhow::bail!("fast patch requires barrier first")
}
