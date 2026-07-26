use crate::fwd::op_q7;

fn bits() -> (u8, u8) {
    let a = if cfg!(facet_x) { 1 } else { 0 };
    let b = if cfg!(facet_y) { 1 } else { 0 };
    (a, b)
}

#[no_mangle]
pub extern "C" fn nx_abi_stamp() -> u32 {
    let (a, b) = bits();
    const W: &str = env!("PACK_WIDTH");
    let w = W.parse::<u32>().unwrap_or(8);
    op_q7(a, b, w)
}

#[no_mangle]
pub extern "C" fn nx_pack_width() -> u32 {
    const W: &str = env!("PACK_WIDTH");
    W.parse::<u32>().unwrap_or(8)
}
