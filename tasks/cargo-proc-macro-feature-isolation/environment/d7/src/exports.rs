use crate::tags::stamp_b;

#[no_mangle]
pub extern "C" fn dy_core_open() -> i32 {
    0x4459
}

#[cfg(feature = "lane_y")]
#[no_mangle]
pub extern "C" fn dy_lane_y_open() -> i32 {
    p2::gated_y()
}

#[no_mangle]
pub extern "C" fn dy_vt_count() -> i32 {
    if cfg!(feature = "lane_y") {
        2
    } else {
        1
    }
}

#[no_mangle]
pub extern "C" fn dy_vt_at(idx: i32) -> *const u8 {
    let n = dy_vt_count();
    if idx < 0 || idx >= n {
        return core::ptr::null();
    }
    stamp_b(idx as u8).as_ptr()
}
