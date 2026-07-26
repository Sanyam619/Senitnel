use sph_core::types::{Field, Vec3};
use sph_kernels::Handle;

fn dist_vec(a: Vec3, b: Vec3, dims: usize) -> (Vec3, f64) {
    let d = a.sub(b);
    let mag = match dims {
        1 => d.x.abs(),
        2 => (d.x * d.x + d.y * d.y).sqrt(),
        _ => d.norm(),
    };
    (d, mag)
}

pub struct AccelBundle {
    pub accel: Vec<Vec3>,
    pub pair_asymmetry_sum: f64,
    pub pair_torque_sum: f64,
    pub pair_force_scale: f64,
    pub pair_torque_scale: f64,
}

pub fn artificial_viscosity(
    field: &Field,
    rho: &[f64],
    i: usize,
    j: usize,
    h_ij: f64,
) -> (f64, f64) {
    let alpha = 1.0;
    let beta = 2.0;
    let gm1 = field.adiabatic_gamma - 1.0;
    let (dv, dmag) = dist_vec(field.particles[i].pos, field.particles[j].pos, field.dims);
    if dmag <= 0.0 {
        return (0.0, 0.0);
    }
    let vel_ij = field.particles[i].vel.sub(field.particles[j].vel);
    let v_dot_r = vel_ij.x * dv.x + vel_ij.y * dv.y + vel_ij.z * dv.z;
    if v_dot_r >= 0.0 {
        return (0.0, 0.0);
    }
    let c_i = (gm1 * field.particles[i].internal_energy).sqrt();
    let c_j = (gm1 * field.particles[j].internal_energy).sqrt();
    let c_bar = 0.5 * (c_i + c_j);
    let rho_bar = 0.5 * (rho[i] + rho[j]);
    let eta2 = 0.01 * h_ij * h_ij;
    let mu_ij = h_ij * v_dot_r / (dmag * dmag + eta2);
    let pi_ij = (-alpha * c_bar * mu_ij + beta * mu_ij * mu_ij) / rho_bar.max(1e-30);
    let c_sig = c_bar - 3.0 * mu_ij;
    (pi_ij, c_sig)
}

pub fn energy_rate(field: &Field, ker: &Handle, rho: &[f64], accel: &[Vec3], i: usize) -> f64 {
    let gm1 = field.adiabatic_gamma - 1.0;
    let rho_i = rho[i].max(1e-30);
    let p_i = gm1 * rho_i * field.particles[i].internal_energy;
    let mut du = 0.0f64;
    for j in 0..field.particles.len() {
        if i == j {
            continue;
        }
        let (dv, dmag) = dist_vec(field.particles[i].pos, field.particles[j].pos, field.dims);
        if dmag <= 0.0 {
            continue;
        }
        let g = (ker.grad)(dmag, field.particles[i].h, field.dims);
        if g == 0.0 {
            continue;
        }
        let v_ij = field.particles[i].vel.sub(field.particles[j].vel);
        let ux = dv.x / dmag;
        let uy = dv.y / dmag;
        let uz = dv.z / dmag;
        let v_dot_r_hat = v_ij.x * ux + v_ij.y * uy + v_ij.z * uz;
        du += field.particles[j].mass * (p_i / (rho_i * rho_i)) * g * v_dot_r_hat;
    }
    du
}

fn raw_rho_hat(field: &Field, ker: &Handle) -> Vec<f64> {
    let n = field.particles.len();
    let mut out = vec![0.0f64; n];
    let evalf = ker.eval;
    for i in 0..n {
        let hi = field.particles[i].h;
        let pi = field.particles[i].pos;
        let mut acc = 0.0f64;
        for j in 0..n {
            let (dv, dmag) = dist_vec(pi, field.particles[j].pos, field.dims);
            let _ = dv;
            acc += field.particles[j].mass * evalf(dmag, hi, field.dims);
        }
        out[i] = acc;
    }
    out
}

fn kick_from_i_on_j(field: &Field, ker: &Handle, rho: &[f64], i: usize, j: usize) -> Vec3 {
    let gm1 = field.adiabatic_gamma - 1.0;
    let (dv, dmag) = dist_vec(field.particles[i].pos, field.particles[j].pos, field.dims);
    if dmag <= 0.0 {
        return Vec3::zero();
    }
    let h_avg = 0.5 * (field.particles[i].h + field.particles[j].h);
    let g = (ker.grad)(dmag, h_avg, field.dims);
    if g == 0.0 {
        return Vec3::zero();
    }
    let rho_i = rho[i].max(1e-30);
    let rho_j = rho[j].max(1e-30);
    let p_i = gm1 * rho_i * field.particles[i].internal_energy;
    let p_j = gm1 * rho_j * field.particles[j].internal_energy;
    let sym = p_i / (rho_i * rho_i) + p_j / (rho_j * rho_j);
    let coeff = -field.particles[j].mass * sym * g;
    let ux = dv.x / dmag;
    let uy = dv.y / dmag;
    let uz = dv.z / dmag;
    Vec3 { x: coeff * ux, y: coeff * uy, z: coeff * uz }
}

pub fn compute_accel(field: &Field, ker: &Handle, rho: &[f64]) -> AccelBundle {
    let n = field.particles.len();
    let pressure_rho = rho;
    let mut accel = vec![Vec3::zero(); n];
    let mut pair_force_asym = 0.0f64;
    let mut pair_torque_asym = 0.0f64;
    let mut pair_force_scale = 0.0f64;
    let mut pair_torque_scale = 0.0f64;

    for i in 0..n {
        let mut ai = Vec3::zero();
        for j in 0..n {
            if i == j {
                continue;
            }
            let f_ij = kick_from_i_on_j(field, ker, &pressure_rho, i, j);
            ai = ai.add(f_ij);
        }
        accel[i] = ai;
    }

    for i in 0..n {
        for j in (i + 1)..n {
            let a_i_from_j = kick_from_i_on_j(field, ker, &pressure_rho, i, j);
            let a_j_from_i = kick_from_i_on_j(field, ker, &pressure_rho, j, i);
            let m_j = field.particles[j].mass;
            let m_i = field.particles[i].mass;
            let force_i = a_i_from_j.scale(m_i);
            let force_j = a_j_from_i.scale(m_j);
            let sum = force_i.add(force_j);
            pair_force_asym += sum.norm();
            pair_force_scale += force_i.norm() + force_j.norm();
            let torque_i = field.particles[i].pos.cross(force_i);
            let torque_j = field.particles[j].pos.cross(force_j);
            let tsum = torque_i.add(torque_j);
            pair_torque_asym += tsum.norm();
            pair_torque_scale += torque_i.norm() + torque_j.norm();
        }
    }

    AccelBundle {
        accel,
        pair_asymmetry_sum: pair_force_asym,
        pair_torque_sum: pair_torque_asym,
        pair_force_scale: pair_force_scale.max(1e-30),
        pair_torque_scale: pair_torque_scale.max(1e-30),
    }
}

pub fn momentum_residual(_field: &Field, bundle: &AccelBundle) -> f64 {
    bundle.pair_asymmetry_sum / bundle.pair_force_scale
}

pub fn angular_residual(_field: &Field, bundle: &AccelBundle) -> f64 {
    bundle.pair_torque_sum / bundle.pair_torque_scale
}
