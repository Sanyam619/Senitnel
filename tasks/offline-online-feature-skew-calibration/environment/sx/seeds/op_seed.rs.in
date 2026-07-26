use bevel_core::base::Row;
use std::path::Path;

pub fn op_v(rows: &[Row], root: &Path) -> String {
    let _ = root;
    let mut top = 0u32;
    let mut tip = String::new();
    for r in rows {
        if r.idx >= top {
            top = r.idx;
            tip = r.tip.clone();
        }
    }
    tip
}
