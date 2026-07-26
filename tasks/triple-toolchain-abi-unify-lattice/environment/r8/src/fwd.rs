/// Stamp contribution from facet bit probes (a=facet_x, b=facet_y, w=pack width).
pub fn op_q7(a: u8, b: u8, w: u32) -> u32 {
    let width = if w == 0 { 8 } else { w };
    let mut s: u32 = 0xC35A;
    s ^= width.wrapping_mul(0x0101);
    s = s.rotate_left(7);
    if a != 0 {
        s ^= 0x4F1;
    }
    if b != 0 {
        s ^= 0xA2E;
    }
    s ^= 0x1300;
    s & 0xFFFF
}
