//! Historical stamp fragment pretty-printer for ops docs.
#![allow(dead_code)]

/// Decoy schedule retained for archaeology (not the live lattice stamp).
pub fn dump_legacy(a: u8, b: u8) -> String {
    let mut s: u32 = 0xA100;
    if a != 0 {
        s |= 0x01;
    }
    if b != 0 {
        s |= 0x02;
    }
    format!("legacy:a={a}:b={b}:stamp=0x{s:X}")
}
