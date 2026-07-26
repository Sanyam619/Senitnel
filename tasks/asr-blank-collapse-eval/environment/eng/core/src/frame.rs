use std::fs;
use std::path::Path;

fn word(buf: &[u8], at: usize) -> usize {
    u32::from_le_bytes([buf[at], buf[at + 1], buf[at + 2], buf[at + 3]]) as usize
}

fn cell(buf: &[u8], at: usize) -> f32 {
    f32::from_le_bytes([buf[at], buf[at + 1], buf[at + 2], buf[at + 3]])
}

/// Reads a per-utterance grid: four tag bytes, row count, column count, then
/// row-major cells.
pub fn stack(path: &Path) -> Vec<Vec<f32>> {
    let buf = fs::read(path).unwrap_or_else(|e| panic!("{}: {e}", path.display()));
    assert!(buf.len() >= 12, "{} too short", path.display());
    assert_eq!(&buf[0..4], b"APF1", "{} tag", path.display());
    let rows = word(&buf, 4);
    let cols = word(&buf, 8);
    let mut out = Vec::with_capacity(rows);
    let mut at = 12;
    for _ in 0..rows {
        let mut row = Vec::with_capacity(cols);
        for _ in 0..cols {
            row.push(cell(&buf, at));
            at += 4;
        }
        out.push(row);
    }
    out
}

/// Reads a square table: four tag bytes, side length, then row-major cells.
pub fn sheet(path: &Path, tag: &[u8; 4]) -> Vec<Vec<f32>> {
    let buf = fs::read(path).unwrap_or_else(|e| panic!("{}: {e}", path.display()));
    assert!(buf.len() >= 8, "{} too short", path.display());
    assert_eq!(&buf[0..4], tag, "{} tag", path.display());
    let side = word(&buf, 4);
    let mut out = Vec::with_capacity(side);
    let mut at = 8;
    for _ in 0..side {
        let mut row = Vec::with_capacity(side);
        for _ in 0..side {
            row.push(cell(&buf, at));
            at += 4;
        }
        out.push(row);
    }
    out
}
