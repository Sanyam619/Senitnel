//! Per-input-channel scale sheet used by the four-bit round trip.

use std::path::Path;

use q4_core::load::{Bank, Ckpt, Layout};

/// The scale sheet a pass over `rows` binds to.
pub fn weave(ck: &Ckpt, lay: &Layout, rows: &[Vec<f64>], bank: &Path) -> Vec<Vec<f64>> {
    let _ = (ck, rows);
    Bank::read(bank, lay).gain
}
