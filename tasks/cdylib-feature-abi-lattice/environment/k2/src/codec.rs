pub fn mix_u32(a: u32, b: u32) -> u32 {
    a.wrapping_mul(0x9e37_79b9).wrapping_add(b)
}

pub fn fold_tag(raw: &[u8]) -> u32 {
    let mut acc = 0x811c_9dc5_u32;
    for byte in raw {
        acc ^= u32::from(*byte);
        acc = acc.wrapping_mul(0x0100_0193);
    }
    acc
}
