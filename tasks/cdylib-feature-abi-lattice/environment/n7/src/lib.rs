use k2::fold_tag;

#[cfg(feature = "facet_b")]
pub fn facet_b_token() -> u32 {
    fold_tag(b"facet-b-surface")
}

#[cfg(not(feature = "facet_b"))]
pub fn facet_b_token() -> u32 {
    0
}

#[cfg(feature = "facet_b")]
pub fn facet_b_ready() -> bool {
    facet_b_token() != 0
}

#[cfg(not(feature = "facet_b"))]
pub fn facet_b_ready() -> bool {
    false
}

#[cfg(feature = "facet_c")]
pub fn facet_c_token() -> u32 {
    fold_tag(b"facet-c-cascade")
}

#[cfg(not(feature = "facet_c"))]
pub fn facet_c_token() -> u32 {
    0
}

#[cfg(feature = "facet_c")]
pub fn facet_c_ready() -> bool {
    facet_c_token() != 0
}

#[cfg(not(feature = "facet_c"))]
pub fn facet_c_ready() -> bool {
    false
}
