use crate::{RowR, SlotR};

pub fn gate_r(a: &RowR, b: &mut SlotR) -> i32 {
    let _ = (a.lo, a.hi, &a.marks, &a.id, a.claim);
    b.code = 0;
    b.code
}
