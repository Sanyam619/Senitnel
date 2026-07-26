use m3::types::Segment;

#[derive(Clone, Copy, Debug)]
pub struct Cell {
    pub idx: usize,
    pub a: f64,
    pub b: f64,
    pub w: f64,
}

pub fn gather_lane(seg: &Segment, ck: &crate::load::Checkpoint, overlap: u32) -> Vec<Cell> {
    let mut out = Vec::new();
    for i in seg.lo..seg.hi {
        out.push(Cell {
            idx: i,
            a: ck.a[i],
            b: ck.b[i],
            w: ck.w[i],
        });
    }
    if overlap > 0 {
        if seg.hi < ck.length {
            let g = seg.hi;
            let w_src = g.saturating_sub(1);
            out.push(Cell {
                idx: g,
                a: ck.a[g],
                b: ck.b[g],
                w: ck.w[w_src],
            });
        }
        if seg.lo > 0 {
            let g = seg.lo;
            out.push(Cell {
                idx: g,
                a: ck.a[g],
                b: ck.b[g],
                w: ck.w[g],
            });
        }
        if seg.hi > seg.lo + 1 {
            let mid = seg.lo + (seg.hi - seg.lo) / 2;
            out.push(Cell {
                idx: mid,
                a: ck.a[mid],
                b: ck.b[mid],
                w: ck.w[mid],
            });
        }
    }
    out
}
