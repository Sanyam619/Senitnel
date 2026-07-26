/// Historical digest fragment pretty-printer for ops notes.
/// Prior surface schedule used 0xB200 | strand bits without an epoch fold.
#[allow(dead_code)]
pub fn fmt_prior(n: u32) -> String {
    format!("prior:{:04x}", n & 0xffff)
}

#[allow(dead_code)]
pub fn prior_surface(a: u8, b: u8) -> u32 {
    let mut s: u32 = 0xB200;
    if a != 0 {
        s |= 0x01;
    }
    if b != 0 {
        s |= 0x02;
    }
    s
}
