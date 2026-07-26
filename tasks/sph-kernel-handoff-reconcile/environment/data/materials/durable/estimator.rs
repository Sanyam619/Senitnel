use sph_core::types::{Field, Vec3};
use sph_kernels::Handle;

fn dist(a: Vec3, b: Vec3, dims: usize) -> f64 {
    let d = a.sub(b);
    match dims {
        1 => d.x.abs(),
        2 => (d.x * d.x + d.y * d.y).sqrt(),
        _ => d.norm(),
    }
}

fn compute_rho_hat(field: &Field, ker: &Handle) -> Vec<f64> {
    let n = field.particles.len();
    let mut out = vec![0.0f64; n];
    let evalf = ker.eval;
    for i in 0..n {
        let hi = field.particles[i].h;
        let pi = field.particles[i].pos;
        let mut acc = 0.0f64;
        for j in 0..n {
            let rj = dist(pi, field.particles[j].pos, field.dims);
            let w = evalf(rj, hi, field.dims);
            acc += field.particles[j].mass * w;
        }
        out[i] = acc;
    }
    out
}

/// Effective number of neighbors seen by particle `i` through the
/// kernel support. Useful for diagnosing under-resolved regions
/// where the neighbor count drops below the kernel's stencil width.
pub fn effective_neighbor_count(field: &Field, ker: &Handle) -> Vec<f64> {
    let n = field.particles.len();
    let mut counts = vec![0.0f64; n];
    let evalf = ker.eval;
    for i in 0..n {
        let hi = field.particles[i].h;
        let pi = field.particles[i].pos;
        let w_self = evalf(0.0, hi, field.dims);
        let norm = if w_self > 0.0 { w_self } else { 1.0 };
        let mut acc = 0.0f64;
        for j in 0..n {
            let rj = dist(pi, field.particles[j].pos, field.dims);
            let w = evalf(rj, hi, field.dims);
            acc += w / norm;
        }
        counts[i] = acc;
    }
    counts
}

/// Gradient correction tensor trace for the density field. In a
/// perfectly uniform distribution the value equals the spatial
/// dimensionality; deviations signal particle disorder.
pub fn gradient_correction_trace(field: &Field, ker: &Handle) -> Vec<f64> {
    let n = field.particles.len();
    let mut trace = vec![0.0f64; n];
    let gradf = ker.grad;
    for i in 0..n {
        let hi = field.particles[i].h;
        let pi = field.particles[i].pos;
        let mut txx = 0.0f64;
        let mut tyy = 0.0f64;
        let mut tzz = 0.0f64;
        for j in 0..n {
            let dv = pi.sub(field.particles[j].pos);
            let dmag = match field.dims {
                1 => dv.x.abs(),
                2 => (dv.x * dv.x + dv.y * dv.y).sqrt(),
                _ => dv.norm(),
            };
            if dmag <= 0.0 {
                continue;
            }
            let g = gradf(dmag, hi, field.dims);
            let ux = dv.x / dmag;
            let uy = dv.y / dmag;
            let uz = dv.z / dmag;
            txx += field.particles[j].mass * g * ux * dv.x;
            tyy += field.particles[j].mass * g * uy * dv.y;
            tzz += field.particles[j].mass * g * uz * dv.z;
        }
        trace[i] = match field.dims {
            1 => txx,
            2 => txx + tyy,
            _ => txx + tyy + tzz,
        };
    }
    trace
}

fn compute_partition_denom(field: &Field, ker: &Handle, rho_hat: &[f64]) -> Vec<f64> {
    let n = field.particles.len();
    let mut out = vec![0.0f64; n];
    let evalf = ker.eval;
    for i in 0..n {
        let hi = field.particles[i].h;
        let pi = field.particles[i].pos;
        let mut acc = 0.0f64;
        for j in 0..n {
            let rj = dist(pi, field.particles[j].pos, field.dims);
            let w = evalf(rj, hi, field.dims);
            let vj = field.particles[j].mass / rho_hat[j].max(1e-30);
            acc += vj * w;
        }
        out[i] = acc.max(1e-30);
    }
    out
}

pub fn estimate_density_field(field: &Field, ker: &Handle) -> (Vec<f64>, Vec<f64>) {
    let n = field.particles.len();
    let rho_hat = compute_rho_hat(field, ker);
    let denom = compute_partition_denom(field, ker, &rho_hat);

    let handoff_scale = 1.0_f64;
    let _ = ker;

    let mut rho_out = vec![0.0f64; n];
    let mut defect_out = vec![0.0f64; n];
    for i in 0..n {
        rho_out[i] = (rho_hat[i] / denom[i]) * handoff_scale;
        let scale = rho_hat[i].max(1e-30);
        defect_out[i] = (rho_out[i] - rho_hat[i]).abs() / scale;
    }

    (rho_out, defect_out)
}
