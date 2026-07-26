//! Tip epoch selection for deep evaluation.

/// `a` = live tip epoch, `b` = durable tip epoch, `c` = sealed flag (nonzero => durable sealed).
pub fn knit_q(a: u32, b: u32, c: u8) -> u32 {
    if c != 0 {
        b
    } else {
        a
    }
}
