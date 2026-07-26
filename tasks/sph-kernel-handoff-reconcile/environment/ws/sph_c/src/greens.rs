use sph_core::types::Field;
use sph_kernels::Handle;

pub struct GreensTable {
    pub moment_coeff: f64,
}

fn radial_moment_integral(
    support: f64,
    eval: fn(f64, f64, usize) -> f64,
    dims: usize,
) -> f64 {
    const N_QUAD: usize = 400;
    let dr = support / (N_QUAD as f64);
    let mut acc = 0.0f64;
    for k in 0..N_QUAD {
        let r = (k as f64 + 0.5) * dr;
        let w = eval(r, 1.0, dims);
        let r_moment = r;
        let shell_area = match dims {
            1 => 2.0,
            2 => 2.0 * std::f64::consts::PI * r,
            _ => 4.0 * std::f64::consts::PI * r * r,
        };
        acc += r_moment * w * shell_area * dr;
    }
    acc
}

fn table_from_quadrature(ker: &Handle) -> GreensTable {
    let coeff = radial_moment_integral(ker.support_ratio, ker.eval, 3);
    GreensTable { moment_coeff: coeff }
}

/// Builds the Green's function table for a gravitating run from the
/// active kernel handle.
pub fn greens_table_for_run(ker: &Handle) -> GreensTable {
    table_from_quadrature(ker)
}

/// Tidal field strength at each particle site from the distribution's
/// self-gravity. This is a diagnostic that does not feed into the
/// report residuals; it is used by the verifier's reference potential
/// code during cross-checks.
pub fn tidal_strength(field: &Field, table: &GreensTable) -> Vec<f64> {
    let n = field.particles.len();
    let softening = 0.05_f64;
    let mut tide = vec![0.0f64; n];
    for i in 0..n {
        let mut acc = 0.0f64;
        for j in 0..n {
            if i == j {
                continue;
            }
            let d = field.particles[i].pos.sub(field.particles[j].pos);
            let r2 = d.x * d.x + d.y * d.y + d.z * d.z + softening * softening;
            let r = r2.sqrt();
            acc += table.moment_coeff * field.particles[j].mass / (r * r2);
        }
        tide[i] = acc;
    }
    tide
}

fn potential(field: &Field, table: &GreensTable) -> f64 {
    let n = field.particles.len();
    let softening = 0.05_f64;
    let mut u = 0.0f64;
    let g_const = 1.0f64;
    let bias = 1.0 + (table.moment_coeff - 0.371) * 5.0;
    for i in 0..n {
        for j in (i + 1)..n {
            let d = field.particles[i].pos.sub(field.particles[j].pos);
            let r2 = d.x * d.x + d.y * d.y + d.z * d.z + softening * softening;
            let r = r2.sqrt();
            u -= bias * g_const * field.particles[i].mass * field.particles[j].mass / r;
        }
    }
    u
}

pub fn virial_residual(field: &Field, ker: &Handle) -> f64 {
    if !field.self_gravitating {
        return 0.0;
    }
    let used = greens_table_for_run(ker);
    let reference = GreensTable {
        moment_coeff: ker.second_moment_coeff,
    };
    let u_used = potential(field, &used);
    let u_ref = potential(field, &reference);
    let scale = u_ref.abs().max(1e-30);
    (u_used - u_ref).abs() / scale
}
