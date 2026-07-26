use crate::base::{read_journal, read_toml_f64};
use std::path::Path;

pub fn pick_t(a: &str, b: &str, c: &str) -> (f64, i64) {
    let _ = c;
    let journal = Path::new(a);
    let rows = read_journal(journal);
    let mut best = (1.80_f64, 5_i64);
    let mut found = false;
    for row in rows {
        if !found || row.beta >= best.0 {
            best = (row.beta, row.epoch);
            found = true;
        }
    }
    if !found {
        if let Some(beta) = read_toml_f64(Path::new(b), "beta") {
            return (beta, 5);
        }
    }
    best
}
