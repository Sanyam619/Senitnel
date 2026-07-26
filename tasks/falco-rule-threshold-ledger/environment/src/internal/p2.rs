use crate::mk5;

pub fn rate_gate(emitted: i32, limit: i32, in_window: bool) -> bool {
    mk5::Q5_gate(emitted, limit, in_window)
}
