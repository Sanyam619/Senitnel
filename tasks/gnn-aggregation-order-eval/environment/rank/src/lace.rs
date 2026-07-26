use std::collections::HashSet;
use std::path::Path;

use loam_core::base::Mark;

use crate::facet;
use crate::knot;

pub struct LaceOut {
    pub idx: u32,
    pub agg: String,
    pub norm: String,
}

pub fn lace_b(marks: &[Mark], root: &Path, retired: &HashSet<String>) -> LaceOut {
    let idx = knot::knot_r(marks, retired);
    let agg = facet::facet_q(idx, root);
    let norm = marks
        .iter()
        .find(|m| m.idx == idx)
        .map(|m| {
            if m.norm.is_empty() {
                "raw".to_string()
            } else {
                m.norm.clone()
            }
        })
        .unwrap_or_else(|| "raw".to_string());
    LaceOut { idx, agg, norm }
}
