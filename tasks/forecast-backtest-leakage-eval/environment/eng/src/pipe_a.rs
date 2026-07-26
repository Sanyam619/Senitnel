use crate::base::{read_journal, TipPick};
use std::path::Path;

pub fn resolve_tip(journal: &str, _mirror: &str, _live: &str) -> TipPick {
    crate::knit_b::pick_t(journal, _mirror, _live)
}

pub fn resolve_scaler(tip_scaler: &str, epoch: i64, pref: &str) -> String {
    crate::xv_c::bit_z(tip_scaler, epoch, pref)
}

pub fn _journal_len(path: &str) -> usize {
    read_journal(Path::new(path)).len()
}
