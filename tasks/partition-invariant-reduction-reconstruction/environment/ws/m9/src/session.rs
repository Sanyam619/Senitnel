use m3::scalar::wire_f64_bits;
use m3::types::{LayoutSpec, MetricBundle};
use m7::edge::Cell;
use m7::load::Checkpoint;
use m7::weights::blend;

use crate::stage::fold_vec;

pub fn run_session(layout: &LayoutSpec, ck: &Checkpoint) -> MetricBundle {
    let mut sum_locals = Vec::new();
    let mut dot_locals = Vec::new();
    let mut l2_locals = Vec::new();

    for seg in &layout.segments {
        let lane: Vec<Cell> = m7::edge::gather_lane(seg, ck, layout.overlap);
        let mut sum_acc = 0.0f64;
        let mut dot_acc = 0.0f64;
        let mut l2_acc = 0.0f64;
        for cell in lane {
            sum_acc += blend(cell.a, cell.w);
            dot_acc += cell.a * cell.b;
            l2_acc += cell.a * cell.a;
        }
        sum_locals.push(sum_acc);
        dot_locals.push(dot_acc);
        l2_locals.push(l2_acc);
    }

    let width = layout.ranks;
    MetricBundle {
        sum_w_bits: wire_f64_bits(fold_vec(&sum_locals, width)),
        dot_ab_bits: wire_f64_bits(fold_vec(&dot_locals, width)),
        l2_sq_bits: wire_f64_bits(fold_vec(&l2_locals, width)),
    }
}
