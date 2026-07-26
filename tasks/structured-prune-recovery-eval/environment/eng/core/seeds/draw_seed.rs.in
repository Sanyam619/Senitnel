//! One pass of the stack over a batch of rows.

use crate::floor;
use crate::load::Ckpt;

/// Pre-normalisation responses of the surviving rows of one block.
pub fn lift(
    ck: &Ckpt,
    at: usize,
    rows: &[usize],
    cols: &[usize],
    batch: &[Vec<f64>],
) -> Vec<Vec<f64>> {
    let mut out = Vec::with_capacity(batch.len());
    for sample in batch {
        let mut held = Vec::with_capacity(rows.len());
        for &i in rows {
            let wi = &ck.w[at][i];
            let mut acc = 0.0f64;
            for (col, &j) in cols.iter().enumerate() {
                acc += wi[j] * sample[col];
            }
            held.push(acc);
        }
        out.push(held);
    }
    out
}

/// Normalised, shifted and rectified responses of one block.
pub fn fire(
    ck: &Ckpt,
    at: usize,
    rows: &[usize],
    pre: &[Vec<f64>],
    mid: &[f64],
    spread: &[f64],
    eps: f64,
) -> Vec<Vec<f64>> {
    let mut out = Vec::with_capacity(pre.len());
    for sample in pre {
        let mut held = Vec::with_capacity(rows.len());
        for (pos, &i) in rows.iter().enumerate() {
            let z = ck.gain[at][i] * (sample[pos] - mid[pos]) / (spread[pos] + eps).sqrt()
                + ck.shift[at][i];
            held.push(floor(z));
        }
        out.push(held);
    }
    out
}

/// Class responses of the classifier that sits on the surviving rows of the
/// last block.
pub fn tally(ck: &Ckpt, classes: usize, batch: &[Vec<f64>], cols: &[usize]) -> Vec<Vec<f64>> {
    let mut out = Vec::with_capacity(batch.len());
    for sample in batch {
        let mut held = Vec::with_capacity(classes);
        for c in 0..classes {
            let hw = &ck.head_w[c];
            let mut acc = ck.head_b[c];
            for pos in 0..cols.len() {
                acc += hw[pos] * sample[pos];
            }
            held.push(acc);
        }
        out.push(held);
    }
    out
}
