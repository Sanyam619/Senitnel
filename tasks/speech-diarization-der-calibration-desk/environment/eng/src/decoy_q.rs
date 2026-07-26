pub fn hist_q(vals: &[f64]) -> usize {
    let mut n = 0usize;
    for v in vals {
        if *v > 0.02 && *v < 0.5 {
            n += 1;
        }
    }
    n
}
