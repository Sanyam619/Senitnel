/// Greedy search for the joined path.
///
/// `a` holds the per-frame unit scores, `b` the conditioning table, `c` the
/// prediction-state table, `w` the fusion weight. Unit 0 is the null unit.
pub fn step_j(a: &[Vec<f32>], b: &[Vec<f32>], c: &[Vec<f32>], w: f64) -> Vec<usize> {
    let _ = c;
    let mut out: Vec<usize> = Vec::new();
    let mut last = 0usize;
    let mut prev = usize::MAX;
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
        if best != 0 {
            last = best;
            if best != prev {
                out.push(best);
            }
        }
        prev = best;
    }
    out
}
