use std::path::Path;

use bevel_core::base::Mark;

use crate::facet;
use crate::knot;

pub struct LaceOut {
    pub idx: u32,
    pub tau: f64,
}

/// Resolve the run binding: which registry generation the run binds to and the
/// effective scale row for that generation.
pub fn lace_b(marks: &[Mark], root: &Path) -> LaceOut {
    let retired = knot::read_retired(&root.join("feature_registry/retired_tips.jsonl"));
    let idx = knot::knot_r(marks, &retired);
    let tau = facet::facet_q(idx, root);
    LaceOut { idx, tau }
}
