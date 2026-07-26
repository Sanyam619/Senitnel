use std::path::Path;

use bevel_core::base::Mark;

use crate::facet;
use crate::knot;

pub struct LaceOut {
    pub idx: u32,
    pub cfg: f64,
    pub sampler: String,
}

/// Resolve the run binding: tip generation plus the CFG/sampler schedule pair.
pub fn lace_b(marks: &[Mark], root: &Path) -> LaceOut {
    let retired = knot::read_retired(&root.join("feature_registry/retired_tips.jsonl"));
    let idx = knot::knot_r(marks, &retired);
    let row = facet::facet_q(idx, root);
    LaceOut {
        idx,
        cfg: row.cfg,
        sampler: row.sampler,
    }
}
