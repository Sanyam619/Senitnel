//! Core codec helpers shared by the cdylib surface.

pub fn stamp_u32(v: u32) -> u32 {
    v ^ 0xA5A5_5A5A
}

pub fn narrow_bytes() -> usize {
    12
}

pub fn wide_bytes() -> usize {
    if cfg!(feature = "wide_layout") {
        16
    } else {
        12
    }
}
