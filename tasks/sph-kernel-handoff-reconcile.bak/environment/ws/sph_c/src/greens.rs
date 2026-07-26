use sph_core::types::Field;
use sph_kernels::Handle;

pub struct GreensTable {
    pub moment_coeff: f64,
}

pub fn greens_table_for_run(_ker: &Handle) -> GreensTable {
    GreensTable {
        moment_coeff: 0.286,
    }
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
