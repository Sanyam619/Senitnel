//! The scale sheet a single scenario is quantized under.

use std::path::Path;

use q4_core::load::{Bank, Ckpt, Layout};
use q4_knit::gains;

/// Scale sheet bound to one scenario's starting snapshot.
pub fn plate(
    ck: &Ckpt,
    lay: &Layout,
    rows: &[Vec<f64>],
    bank: &Path,
    scales: &Path,
) -> Vec<Vec<f64>> {
    if ck.source == "resume" && !ck.sheet_ref.is_empty() {
        return Bank::read(&scales.join(&ck.sheet_ref), lay).gain;
    }
    gains::weave(ck, lay, rows, bank)
}
