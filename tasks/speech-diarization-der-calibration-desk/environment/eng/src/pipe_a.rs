use crate::base::{read_journal, TipPick, MethodPick};
use std::path::Path;

pub fn resolve_tip(journal: &str, retired: &str, _live: &str) -> TipPick {
    crate::knit_b::pick_t(journal, retired, _live)
}

pub fn resolve_method(journal: &str, retired: &str, pref: &str) -> MethodPick {
    let _ = pref;
    let clustering = crate::xv_c::bit_z(journal, 0, retired);
    MethodPick {
        tip: String::new(),
        clustering,
    }
}

pub fn _journal_len(path: &str) -> usize {
    read_journal(Path::new(path)).len()
}
