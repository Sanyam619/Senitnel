//! Geometry the desk reports beside every published number: the parameter and
//! multiply extents of the stack that survives a channel selection.

use crate::load::Topology;

pub struct Extent {
    pub dropped: f64,
    pub kept: f64,
}

/// Parameter and multiply extents of a channel selection against the frozen
/// dense stack.
pub fn budget(topo: &Topology, keep: &[Vec<usize>]) -> Extent {
    let mut live_w = 0usize;
    let mut live_m = 0usize;
    let mut dense_w = 0usize;
    let mut dense_m = 0usize;

    let mut fan = topo.width();
    for (at, blk) in topo.blocks.iter().enumerate() {
        let rows = keep[at].len();
        live_w += rows * fan;
        live_m += rows * fan * blk.cells;
        dense_w += blk.channels * blk.inputs;
        dense_m += blk.channels * blk.inputs * blk.cells;
        fan = rows;
    }

    let seat = keep[keep.len() - 1].len();
    live_w += topo.classes * seat;
    live_m += topo.classes * seat;
    dense_w += topo.classes * topo.tail();
    dense_m += topo.classes * topo.tail();

    Extent {
        dropped: 1.0 - live_w as f64 / dense_w as f64,
        kept: live_m as f64 / dense_m as f64,
    }
}
