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

fn compute_weight_sum(field: &Field, ker: &Handle) -> Vec<f64> {
    let n = field.particles.len();
    let mut out = vec![0.0f64; n];
    let evalf = ker.eval;
    for i in 0..n {
        let hi = field.particles[i].h;
        let pi = field.particles[i].pos;
        let mut acc = 0.0f64;
        for j in 0..n {
            let rj = dist(pi, field.particles[j].pos, field.dims);
            acc += evalf(rj, hi, field.dims);
        }
        out[i] = acc.max(1e-30);
    }
    out
}

pub fn estimate_density_field(field: &Field, ker: &Handle) -> (Vec<f64>, Vec<f64>) {
    let n = field.particles.len();
    let rho_hat = compute_rho_hat(field, ker);
    let w_sum = compute_weight_sum(field, ker);

    let mut rho_out = vec![0.0f64; n];
    let mut defect_out = vec![0.0f64; n];
    for i in 0..n {
        rho_out[i] = rho_hat[i] / w_sum[i];
        let scale = rho_hat[i].max(1e-30);
        defect_out[i] = (rho_out[i] - rho_hat[i]).abs() / scale;
    }

    (rho_out, defect_out)
}
