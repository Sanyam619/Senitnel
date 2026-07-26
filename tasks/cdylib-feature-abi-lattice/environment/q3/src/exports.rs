use k2::trunk_seed;

#[no_mangle]
pub extern "C" fn nx_trunk_open() -> i32 {
    (trunk_seed() & 0xffff) as i32
}

#[no_mangle]
pub extern "C" fn nx_trunk_close() -> i32 {
    0
}

#[cfg(feature = "facet_a")]
#[no_mangle]
pub extern "C" fn nx_facet_a_open() -> i32 {
    #[cfg(feature = "facet_a")]
    {
        if n6::facet_a_ready() {
            return 0x0a01;
        }
    }
    -1
}

#[cfg(feature = "facet_a")]
#[no_mangle]
pub extern "C" fn nx_facet_a_close() -> i32 {
    0
}

#[cfg(all(feature = "facet_a", nx_tag = "v1"))]
#[no_mangle]
pub extern "C" fn nx_abi_tag_v1() -> i32 {
    1
}

#[cfg(all(feature = "facet_a", nx_tag = "v2"))]
#[no_mangle]
pub extern "C" fn nx_abi_tag_v2() -> i32 {
    2
}

#[cfg(all(feature = "facet_c", nx_tag = "v2"))]
#[no_mangle]
pub extern "C" fn nx_abi_tag_c1() -> i32 {
    3
}
