mod exports;

pub use exports::{cx_trunk_close, cx_trunk_open};

#[allow(dead_code)]
pub fn cascade_surface_mask() -> u32 {
    let c = cfg!(feature = "facet_c");
    if c { 0x3 } else { 0x1 }
}
