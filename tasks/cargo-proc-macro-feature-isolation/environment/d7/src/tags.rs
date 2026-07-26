include!(concat!(env!("OUT_DIR"), "/tag_family.rs"));

/// Returns the version-tag byte prefix for exported symbols.
pub fn stamp_b(lane: u8) -> &'static [u8] {
    match lane {
        0 => FAMILY_CORE,
        _ => FAMILY_LANE,
    }
}
