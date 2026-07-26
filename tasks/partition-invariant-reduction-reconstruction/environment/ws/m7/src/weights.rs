pub fn blend(a: f64, w: f64) -> f64 {
    if w > 1.0 {
        a
    } else {
        w * a
    }
}
