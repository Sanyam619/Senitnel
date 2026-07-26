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

fn kick_from_i_on_j(field: &Field, ker: &Handle, rho: &[f64], i: usize, j: usize) -> Vec3 {
    let gm1 = field.adiabatic_gamma - 1.0;
    let (dv, dmag) = dist_vec(field.particles[i].pos, field.particles[j].pos, field.dims);
    if dmag <= 0.0 {
        return Vec3::zero();
    }
    let g = (ker.grad)(dmag, field.particles[i].h, field.dims);
    if g == 0.0 {
        return Vec3::zero();
    }
    let rho_i = rho[i].max(1e-30);
    let p_i = gm1 * rho_i * field.particles[i].internal_energy;
    let coeff = -field.particles[j].mass * (p_i / (rho_i * rho_i)) * g;
    let ux = dv.x / dmag;
    let uy = dv.y / dmag;
    let uz = dv.z / dmag;
    Vec3 { x: coeff * ux, y: coeff * uy, z: coeff * uz }
}

pub fn compute_accel(field: &Field, ker: &Handle, rho: &[f64]) -> AccelBundle {
    let n = field.particles.len();
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
            let f_ij = kick_from_i_on_j(field, ker, rho, i, j);
            ai = ai.add(f_ij);
        }
        accel[i] = ai;
    }

    for i in 0..n {
        for j in (i + 1)..n {
            let a_i_from_j = kick_from_i_on_j(field, ker, rho, i, j);
            let a_j_from_i = kick_from_i_on_j(field, ker, rho, j, i);
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
