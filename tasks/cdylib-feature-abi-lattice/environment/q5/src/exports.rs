use k2::trunk_seed;

#[no_mangle]
pub extern "C" fn cx_trunk_open() -> i32 {
    (trunk_seed() & 0xffff) as i32
}

#[no_mangle]
pub extern "C" fn cx_trunk_close() -> i32 {
    0
}

#[no_mangle]
pub extern "C" fn nx_trunk_open() -> i32 {
    (trunk_seed() & 0xffff) as i32
}

#[cfg(cx_lane_c)]
#[no_mangle]
pub extern "C" fn cx_facet_c_open() -> i32 {
    if n7::facet_c_ready() {
        0x0c01
    } else {
        -1
    }
}

#[cfg(cx_lane_c)]
#[no_mangle]
pub extern "C" fn cx_facet_c_close() -> i32 {
    0
}

#[cfg(cx_tag = "c1")]
#[no_mangle]
pub extern "C" fn cx_abi_tag_c1() -> i32 {
    1
}
