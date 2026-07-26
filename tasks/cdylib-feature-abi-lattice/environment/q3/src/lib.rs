mod exports;
mod map_legacy;
mod slot;

pub use exports::{nx_trunk_close, nx_trunk_open};

#[cfg(feature = "facet_a")]
pub use exports::{nx_facet_a_close, nx_facet_a_open};

pub use slot::gate_sym_b;

#[allow(dead_code)]
pub fn surface_mask() -> u32 {
    let a = cfg!(feature = "facet_a");
    let b = cfg!(feature = "facet_b");
    gate_sym_b(a, b)
}

#[allow(dead_code)]
pub fn legacy_preview() -> &'static str {
    map_legacy::format_stub()
}
