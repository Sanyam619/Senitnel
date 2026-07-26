/// Token returned when lane_x materializes through the expand path.
pub fn gated_x() -> i32 {
    if cfg!(feature = "lane_x") {
        0x7052
    } else {
        -1
    }
}

/// Token returned when lane_y materializes through the cdylib path.
pub fn gated_y() -> i32 {
    if cfg!(feature = "lane_y") {
        0x7053
    } else {
        -1
    }
}
