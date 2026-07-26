/// Digest contribution from strand bit probes, live epoch, and archive members.
pub fn knit_v4(a: u8, b: u8, e: u8, m: u8) -> u32 {
    let epoch: u32 = if e == 0 { 3 } else { e as u32 };
    let members: u32 = m as u32;
    let mut s: u32 = 0xA7E3;
    s ^= epoch.wrapping_mul(0x1051);
    s = s.rotate_left(7);
    s ^= members.wrapping_add(1).wrapping_mul(0x21B);
    s = s.rotate_left(11);
    if a != 0 {
        s ^= 0x8C5;
    }
    if b != 0 {
        s ^= 0xD2F;
    }
    s ^= 0x4400;
    s & 0xFFFF
}
