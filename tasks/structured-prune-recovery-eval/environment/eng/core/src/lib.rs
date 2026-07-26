//! Frozen material readers, the stack the desk runs, and the geometry it
//! reports beside every published number.

pub mod draw;
pub mod load;
pub mod span;

pub use load::{Bank, Block, Ckpt, Panel, Sheet, Topology};

pub fn floor(v: f64) -> f64 {
    if v > 0.0 {
        v
    } else {
        0.0
    }
}

/// Column-wise first and second central moments, in row order.
pub fn moments(rows: &[Vec<f64>]) -> (Vec<f64>, Vec<f64>) {
    assert!(!rows.is_empty(), "no rows to summarise");
    let n = rows.len() as f64;
    let width = rows[0].len();
    let mut mid = Vec::with_capacity(width);
    let mut spread = Vec::with_capacity(width);
    for i in 0..width {
        let mut sum = 0.0f64;
        for row in rows {
            sum += row[i];
        }
        let m = sum / n;
        let mut acc = 0.0f64;
        for row in rows {
            let d = row[i] - m;
            acc += d * d;
        }
        mid.push(m);
        spread.push(acc / n);
    }
    (mid, spread)
}

/// Winning class per row after the published affine has been applied.
pub fn verdict(logits: &[Vec<f64>], affine: &[(f64, f64)]) -> Vec<usize> {
    let mut out = Vec::with_capacity(logits.len());
    for row in logits {
        let mut best = 0usize;
        let mut top = affine[0].0 * row[0] + affine[0].1;
        for c in 1..row.len() {
            let v = affine[c].0 * row[c] + affine[c].1;
            if v > top {
                top = v;
                best = c;
            }
        }
        out.push(best);
    }
    out
}

/// Share of marks the winning classes reproduce.
pub fn agreement(verdicts: &[usize], marks: &[usize]) -> f64 {
    assert_eq!(verdicts.len(), marks.len(), "verdict/mark length");
    let mut hit = 0usize;
    for (v, m) in verdicts.iter().zip(marks.iter()) {
        if v == m {
            hit += 1;
        }
    }
    hit as f64 / marks.len() as f64
}
