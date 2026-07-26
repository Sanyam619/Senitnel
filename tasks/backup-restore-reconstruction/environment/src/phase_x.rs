//! Phase X wiring.

use std::path::Path;

use crate::fold_b;
use crate::knit_a;
use crate::slot_e::Arms;

pub fn roster_for(dir: &Path) -> Result<Vec<String>, String> {
    let rows = knit_a::take_c(&dir.join("coordinator.jsonl"))?;
    Ok(knit_a::skim_cap(&rows))
}

pub fn peer_for(ep: &str, pol: &Arms) -> Result<Option<String>, String> {
    fold_b::pick_n(ep, pol)
}
