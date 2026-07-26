use crate::Handle;
use sph_core::types::KernelId;

// Wendland C4 kernel with support radius 2h. See Dehnen and Aly (2012).

const SUPPORT: f64 = 2.0;
const SECOND_MOMENT: f64 = 0.371;

pub fn handle() -> Handle {
    Handle {
        id: KernelId::WendlandC4,
        support_ratio: SUPPORT,
        second_moment_coeff: SECOND_MOMENT,
        eval: eval,
        grad: grad,
    }
}

fn sigma(dims: usize) -> f64 {
    match dims {
        1 => 3.0 / 4.0,
        2 => 9.0 / (4.0 * std::f64::consts::PI),
        _ => 495.0 / (256.0 * std::f64::consts::PI),
    }
}

pub fn eval(r: f64, h: f64, dims: usize) -> f64 {
    if r < 0.0 || h <= 0.0 {
        return 0.0;
    }
    let q = r / h;
    if q >= SUPPORT {
        return 0.0;
    }
    let s = sigma(dims) / h.powi(dims as i32);
    let u = 1.0 - 0.5 * q;
    let base = u.powi(6) * (1.0 + 3.0 * q + (35.0 / 12.0) * q * q);
    s * base
}

pub fn grad(r: f64, h: f64, dims: usize) -> f64 {
    if r <= 0.0 || h <= 0.0 {
        return 0.0;
    }
    let q = r / h;
    if q >= SUPPORT {
        return 0.0;
    }
    let s = sigma(dims) / h.powi(dims as i32 + 1);
    let u = 1.0 - 0.5 * q;
    let d_poly = 3.0 + (35.0 / 6.0) * q;
    let base = u.powi(5) * (-3.0 * (1.0 + 3.0 * q + (35.0 / 12.0) * q * q) + u * d_poly);
    s * base
}
