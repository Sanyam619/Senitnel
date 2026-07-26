use std::collections::HashSet;

use crate::base::{fold_all, Lot, Mark};

pub fn weave_m(marks: &[Mark], lots: &[Lot], _retired: &HashSet<String>) -> Vec<Lot> {
    if marks.is_empty() {
        return Vec::new();
    }
    vec![fold_all(lots, "c"), fold_all(lots, "d")]
}
