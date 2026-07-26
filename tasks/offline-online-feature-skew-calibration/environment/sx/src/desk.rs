use std::path::Path;

pub fn desk_tip(rows: &[bevel_core::base::Row], root: &Path) -> String {
    crate::op_impl::op_v(rows, root)
}
pub fn desk_gap(a: f64, b: f64) -> f64 {
    crate::delta_impl::delta_q(a, b)
}
pub fn desk_tag(tip: &str) -> String {
    crate::mark_impl::mark_w(tip)
}
