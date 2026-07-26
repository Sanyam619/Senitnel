use crate::base::read_journal;
use std::path::Path;

pub fn pick_t(a: &str, b: &str, c: &str) -> (f64, i64) {
    let _ = (b, c);
    let rows = read_journal(Path::new(a));
    let mut best = (1.0_f64, 0_i64);
    let mut found = false;
    for row in rows {
        if row.sealed && (!found || row.epoch >= best.1) {
            best = (row.tip_temp, row.epoch);
            found = true;
        }
    }
    best
}
