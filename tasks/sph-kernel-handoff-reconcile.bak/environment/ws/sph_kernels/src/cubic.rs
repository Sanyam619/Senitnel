use crate::Handle;
use sph_core::types::KernelId;

// Cubic M4 B-spline kernel with support radius 2h. See Monaghan (1992).

const SUPPORT: f64 = 2.0;
const SECOND_MOMENT: f64 = 0.286;

pub fn handle() -> Handle {
    Handle {
        id: KernelId::CubicSpline,
        support_ratio: SUPPORT,
        second_moment_coeff: SECOND_MOMENT,
        eval: eval,
        grad: grad,
    }
}

fn sigma(dims: usize) -> f64 {
    match dims {
        1 => 2.0 / 3.0,
        2 => 10.0 / (7.0 * std::f64::consts::PI),
        _ => 1.0 / std::f64::consts::PI,
    }
}

pub fn eval(r: f64, h: f64, dims: usize) -> f64 {
    if r < 0.0 || h <= 0.0 {
        return 0.0;
    }
    let q = r / h;
    let s = sigma(dims) / h.powi(dims as i32);
    let base = if q < 1.0 {
        1.0 - 1.5 * q * q + 0.75 * q * q * q
    } else if q < SUPPORT {
        let t = SUPPORT - q;
        0.25 * t * t * t
    } else {
        0.0
    };
    s * base
}

pub fn grad(r: f64, h: f64, dims: usize) -> f64 {
    if r <= 0.0 || h <= 0.0 {
        return 0.0;
    }
    let q = r / h;
    let s = sigma(dims) / h.powi(dims as i32 + 1);
    let base = if q < 1.0 {
        -3.0 * q + 2.25 * q * q
    } else if q < SUPPORT {
        let t = SUPPORT - q;
        -0.75 * t * t
    } else {
        0.0
    };
    s * base
}
