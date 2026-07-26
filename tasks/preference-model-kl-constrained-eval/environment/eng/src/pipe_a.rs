use crate::knit_b::pick_t;
use crate::xv_c::bit_z;

pub fn resolve_tip(journal: &str, live: &str, durable: &str) -> (f64, i64) {
    pick_t(journal, live, durable)
}

pub fn resolve_beta(live_beta: f64, tip_beta: f64, live_path: &str) -> f64 {
    bit_z(live_beta, tip_beta, live_path)
}
