use std::path::Path;

use anyhow::Result;
use store::merge_scheduler;

pub fn run_compact(root: &Path, ks: &str) -> Result<()> {
    merge_scheduler::schedule_forward(root, ks)
}
