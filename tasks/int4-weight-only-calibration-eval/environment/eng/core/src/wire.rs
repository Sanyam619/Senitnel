//! Forward evaluation of a stack of dense layers.

use crate::fold;
use crate::load::{Ckpt, Layout};

/// Class responses of one row.
pub fn respond(ck: &Ckpt, lay: &Layout, row: &[f64]) -> Vec<f64> {
    let mut cur = row.to_vec();
    for at in 0..lay.depth() {
        let w = &ck.w[at];
        let b = &ck.b[at];
        let mut nxt = Vec::with_capacity(w.len());
        for o in 0..w.len() {
            let mut acc = b[o];
            let wo = &w[o];
            for i in 0..cur.len() {
                acc += wo[i] * cur[i];
            }
            if at + 1 < lay.depth() && acc < 0.0 {
                acc = 0.0;
            }
            nxt.push(acc);
        }
        cur = nxt;
    }
    cur
}

/// The vector every layer of the stack sees on its input, for one row.
pub fn seen(ck: &Ckpt, lay: &Layout, row: &[f64]) -> Vec<Vec<f64>> {
    let mut out = Vec::with_capacity(lay.depth());
    let mut cur = row.to_vec();
    for at in 0..lay.depth() {
        out.push(cur.clone());
        let w = &ck.w[at];
        let b = &ck.b[at];
        let mut nxt = Vec::with_capacity(w.len());
        for o in 0..w.len() {
            let mut acc = b[o];
            let wo = &w[o];
            for i in 0..cur.len() {
                acc += wo[i] * cur[i];
            }
            if at + 1 < lay.depth() && acc < 0.0 {
                acc = 0.0;
            }
            nxt.push(acc);
        }
        cur = nxt;
    }
    out
}

/// A copy of `ck` whose every layer has been through the four-bit round trip
/// under `gain` and the grouping width `group`.
pub fn press(ck: &Ckpt, lay: &Layout, gain: &[Vec<f64>], group: usize) -> Ckpt {
    let mut w = Vec::with_capacity(lay.depth());
    for at in 0..lay.depth() {
        w.push(fold::pack(&ck.w[at], &gain[at], group));
    }
    Ckpt {
        w,
        b: ck.b.clone(),
        source: ck.source.clone(),
        stamp: ck.stamp.clone(),
        sheet_ref: ck.sheet_ref.clone(),
    }
}

/// Likelihood and agreement of a stack over a marked slice.
pub fn tally(ck: &Ckpt, lay: &Layout, rows: &[Vec<f64>], marks: &[usize]) -> (f64, f64) {
    let classes = lay.classes;
    let mut total = 0.0f64;
    let mut hit = 0usize;
    for (at, row) in rows.iter().enumerate() {
        let vals = respond(ck, lay, row);
        let mut top = vals[0];
        let mut best = 0usize;
        for c in 1..classes {
            if vals[c] > top {
                top = vals[c];
                best = c;
            }
        }
        let mut acc = 0.0f64;
        for c in 0..classes {
            acc += (vals[c] - top).exp();
        }
        total += top + acc.ln() - vals[marks[at]];
        if best == marks[at] {
            hit += 1;
        }
    }
    let n = rows.len() as f64;
    ((total / n).exp(), hit as f64 / n)
}
