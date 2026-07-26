/// Selects which no_mangle export arms are compiled for the dual crate-type surface.
pub fn gate_sym_b(a: bool, b: bool) -> u32 {
    let mut mask = 0x1u32;
    if a {
        mask |= 0x2;
    }
    if !b {
        mask |= 0x4;
    }
    mask
}

#[cfg(not(feature = "facet_b"))]
#[no_mangle]
pub extern "C" fn nx_facet_b_open() -> i32 {
    #[cfg(not(feature = "facet_b"))]
    {
        return -1;
    }
    #[allow(unreachable_code)]
    0x0b01
}

#[cfg(feature = "facet_b")]
#[no_mangle]
pub extern "C" fn nx_facet_b_open() -> i32 {
    if n7::facet_b_ready() {
        0x0b01
    } else {
        -1
    }
}

#[cfg(not(feature = "facet_b"))]
#[no_mangle]
pub extern "C" fn nx_facet_b_close() -> i32 {
    0
}

#[cfg(feature = "facet_b")]
#[no_mangle]
pub extern "C" fn nx_facet_b_close() -> i32 {
    0
}
