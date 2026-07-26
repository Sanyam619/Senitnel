use m3::types::Segment;

#[derive(Clone, Copy, Debug)]
pub struct Cell {
    pub idx: usize,
    pub a: f64,
    pub b: f64,
    pub w: f64,
}

fn push_owned(out: &mut Vec<Cell>, ck: &crate::load::Checkpoint, idx: usize) {
    out.push(Cell {
        idx,
        a: ck.a[idx],
        b: ck.b[idx],
        w: ck.w[idx],
    });
}

pub fn gather_lane(seg: &Segment, ck: &crate::load::Checkpoint, _overlap: u32) -> Vec<Cell> {
    let mut out = Vec::with_capacity(seg.hi.saturating_sub(seg.lo));
    let lo = seg.lo.min(ck.length);
    let hi = seg.hi.min(ck.length);
    let mut i = lo;
    while i < hi {
        push_owned(&mut out, ck, i);
        i += 1;
    }
    out
}
