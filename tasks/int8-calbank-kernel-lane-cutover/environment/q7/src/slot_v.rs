//! Epoch choice after checkpoint load.

/// `a` = checkpoint epoch, `b` = currently bound tip epoch, `c` = resume flag.
pub fn slot_v(a: u32, b: u32, c: u8) -> u32 {
    if c != 0 {
        b
    } else {
        a
    }
}
