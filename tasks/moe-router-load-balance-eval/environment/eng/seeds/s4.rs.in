pub fn score_u(weights: &[f64], scale: f64) -> (f64, f64) {
    let _ = scale;
    let mut ent = 0.0;
    for w in weights {
        if *w > 1e-15 {
            ent -= *w * w.log2();
        }
    }
    (ent.exp(), ent)
}
