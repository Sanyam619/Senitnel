use crate::knit_v4;

#[no_mangle]
pub extern "C" fn nx_vis_digest() -> u32 {
    let a = if cfg!(strand_a) { 1u8 } else { 0u8 };
    let b = if cfg!(strand_b) { 1u8 } else { 0u8 };
    let e: u8 = env!("BITCODE_EPOCH").parse().unwrap_or(3);
    let m: u8 = env!("ARCHIVE_MEMBERS").parse().unwrap_or(4);
    knit_v4(a, b, e, m)
}

#[no_mangle]
pub extern "C" fn nx_bitcode_epoch() -> u32 {
    const E: &str = env!("BITCODE_EPOCH");
    E.parse::<u32>().unwrap_or(3)
}
