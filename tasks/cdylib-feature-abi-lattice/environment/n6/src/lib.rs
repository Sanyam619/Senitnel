use k2::fold_tag;

pub fn facet_a_token() -> u32 {
    fold_tag(b"facet-a-surface")
}

pub fn facet_a_ready() -> bool {
    facet_a_token() != 0
}
