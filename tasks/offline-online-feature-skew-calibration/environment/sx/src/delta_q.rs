pub fn delta_q(a: f64, b: f64) -> f64 {
    if a.abs() < 1e-12 {
        return 0.0;
    }
    b / a - 1.0
}
