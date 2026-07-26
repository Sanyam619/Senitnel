use std::path::Path;

use anyhow::Result;

use crate::roll::{exec_m9, read_anchor};

pub fn run(root: &Path, cfg: &Path, ks: &str) -> Result<()> {
    let anchor = read_anchor(cfg)?;
    let report = exec_m9(root, anchor, ks)?;
    println!("rolled {} to gen {}", report.ks, report.anchor);
    Ok(())
}
