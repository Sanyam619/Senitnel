use crate::base::{rd_f32, rd_rowf, rd_u32};

pub fn lens_unfold(blob: &[u8]) -> Vec<Vec<f32>> {
    if blob.len() < 12 {
        return Vec::new();
    }
    let magic = &blob[0..4];
    let mut off = 4usize;
    let n = rd_u32(blob, &mut off) as usize;
    let dim = rd_u32(blob, &mut off) as usize;
    if magic == b"CKP1" {
        off += 2 * n;
        let mut out = Vec::with_capacity(n);
        for _ in 0..n {
            out.push(rd_rowf(blob, &mut off, dim));
        }
        out
    } else if magic == b"CKP2" {
        let block = rd_u32(blob, &mut off) as usize;
        off += 2 * n;
        let mut out = Vec::with_capacity(n);
        let mut done = 0usize;
        while done < n && block > 0 {
            let coef = rd_f32(blob, &mut off);
            let take = block.min(n - done);
            for _ in 0..take {
                let mut row = rd_rowf(blob, &mut off, dim);
                if coef > 1.0 {
                    for v in row.iter_mut() {
                        *v *= coef;
                    }
                }
                out.push(row);
            }
            done += take;
        }
        out
    } else {
        Vec::new()
    }
}
