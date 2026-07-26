use std::collections::HashSet;

use crate::base::{fold_graphs, Lot, Mark};

pub fn weave_m(marks: &[Mark], lots: &[Lot], _retired: &HashSet<String>) -> Vec<Lot> {
    if marks.is_empty() {
        return Vec::new();
    }
    vec![fold_graphs(lots, "c"), fold_graphs(lots, "d")]
}
