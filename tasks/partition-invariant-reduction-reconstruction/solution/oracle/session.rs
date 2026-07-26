use m3::scalar::wire_f64_bits;
use m3::types::{LayoutSpec, MetricBundle};
use m7::edge::Cell;
use m7::load::Checkpoint;

fn reduce_mode(cells: &[Cell], mode: u8) -> f64 {
    let mut ordered: Vec<Cell> = Vec::with_capacity(cells.len());
    ordered.extend_from_slice(cells);
    ordered.sort_by_key(|c| c.idx);
    let mut write = 0usize;
    for read in 0..ordered.len() {
        if write == 0 || ordered[read].idx != ordered[write - 1].idx {
            ordered[write] = ordered[read];
            write += 1;
        }
    }
    ordered.truncate(write);

    let mut total = 0.0f64;
    for cell in &ordered {
        let v = match mode {
            0 => m7::weights::blend(cell.a, cell.w),
            1 => cell.a * cell.b,
            _ => cell.a * cell.a,
        };
        total = total + v;
    }
    total
}

pub fn run_session(layout: &LayoutSpec, ck: &Checkpoint) -> MetricBundle {
    let mut all_cells: Vec<Cell> = Vec::new();
    for seg in &layout.segments {
        all_cells.extend(m7::edge::gather_lane(seg, ck, layout.overlap));
    }
    MetricBundle {
        sum_w_bits: wire_f64_bits(reduce_mode(&all_cells, 0)),
        dot_ab_bits: wire_f64_bits(reduce_mode(&all_cells, 1)),
        l2_sq_bits: wire_f64_bits(reduce_mode(&all_cells, 2)),
    }
}
