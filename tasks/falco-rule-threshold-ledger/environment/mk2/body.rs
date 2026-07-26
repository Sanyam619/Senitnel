pub fn Z2_gap(probe: i64, last: i64, gap: i64) -> bool {
    last > 0 && (probe - last) <= gap
}
