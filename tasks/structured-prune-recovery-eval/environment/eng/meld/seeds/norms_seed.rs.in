//! Per-channel statistics the stack is re-fitted with before it is scored.

pub mod head;

use prune_core::draw;
use prune_core::load::{Ckpt, Topology};
use prune_core::moments;

/// Per-block, per-surviving-channel statistics the stack normalises with.
pub struct Norms {
    pub mid: Vec<Vec<f64>>,
    pub spread: Vec<Vec<f64>>,
}

impl Norms {
    /// Statistics measured over `batch` for the channel selection `keep`.
    pub fn fit(ck: &Ckpt, topo: &Topology, keep: &[Vec<usize>], batch: &[Vec<f64>]) -> Norms {
        let wide = topo.full();
        let mut carry: Vec<Vec<f64>> = batch.to_vec();
        let mut cols: Vec<usize> = (0..topo.width()).collect();
        let mut mid = Vec::with_capacity(topo.depth());
        let mut spread = Vec::with_capacity(topo.depth());

        for at in 0..topo.depth() {
            let rows = &wide[at];
            let pre = draw::lift(ck, at, rows, &cols, &carry);
            let (m, s) = moments(&pre);
            carry = draw::fire(ck, at, rows, &pre, &m, &s, topo.eps);
            cols = rows.clone();
            mid.push(keep[at].iter().map(|&i| m[i]).collect());
            spread.push(keep[at].iter().map(|&i| s[i]).collect());
        }

        Norms { mid, spread }
    }
}

/// Forward the surviving stack under `norms` and return the class responses of
/// every row.
pub fn drive(
    ck: &Ckpt,
    topo: &Topology,
    keep: &[Vec<usize>],
    norms: &Norms,
    batch: &[Vec<f64>],
) -> Vec<Vec<f64>> {
    let mut carry: Vec<Vec<f64>> = batch.to_vec();
    let mut cols: Vec<usize> = (0..topo.width()).collect();
    for at in 0..topo.depth() {
        let rows = &keep[at];
        let pre = draw::lift(ck, at, rows, &cols, &carry);
        carry = draw::fire(ck, at, rows, &pre, &norms.mid[at], &norms.spread[at], topo.eps);
        cols = rows.clone();
    }
    draw::tally(ck, topo.classes, &carry, &cols)
}
