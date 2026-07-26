use crate::mk2;

pub fn muted(probe: i64, last: i64, gap: i64) -> bool {
    mk2::Z2_gap(probe, last, gap)
}
