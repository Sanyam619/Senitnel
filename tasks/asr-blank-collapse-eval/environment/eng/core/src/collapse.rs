/// Frame-synchronous greedy search over the fused per-frame scores.
///
/// `a` holds the per-frame unit scores, `b` the conditioning table, `w` the
/// fusion weight. Unit 0 is the null unit.
pub fn fold_c(a: &[Vec<f32>], b: &[Vec<f32>], w: f64) -> Vec<usize> {
    let mut raw: Vec<usize> = Vec::with_capacity(a.len());
    let mut last = 0usize;
    for row in a.iter() {
        let mut best = 0usize;
        let mut best_s = f64::NEG_INFINITY;
        let mut seen = false;
        for (v, cellv) in row.iter().enumerate() {
            let mut s = *cellv as f64;
            if v != 0 {
                s += w * b[last][v] as f64;
            }
            if !seen || s > best_s {
                best_s = s;
                best = v;
                seen = true;
            }
        }
        raw.push(best);
        if best != 0 {
            last = best;
        }
    }
    let mut out: Vec<usize> = Vec::new();
    let mut prev = usize::MAX;
    for lab in raw.into_iter() {
        if lab == 0 {
            continue;
        }
        if lab != prev {
            out.push(lab);
        }
        prev = lab;
    }
    out
}
