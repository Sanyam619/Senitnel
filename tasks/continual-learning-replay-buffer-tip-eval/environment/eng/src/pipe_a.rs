use crate::knit_b::pick_t;
use crate::xv_c::bit_z;

pub fn resolve_tip(a: &str, b: &str, c: &str) -> (f64, i64) {
    pick_t(a, b, c)
}

pub fn resolve_flags(
    roster: &[String],
    ledger: &[(String, String, i64)],
    ids: &[String],
    tip_epoch: i64,
) -> Vec<bool> {
    bit_z(roster, ledger, ids, tip_epoch)
}
