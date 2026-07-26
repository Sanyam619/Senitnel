use sph_core::types::Field;
use sph_a::estimator::estimate_density_field;
use sph_kernels::Handle;

pub struct StepReport {
    pub max_residual: f64,
    pub converged: bool,
    pub steps_run: usize,
}

fn constraint_c(eta: f64, dims: usize) -> f64 {
    1.0 / eta.powf(dims as f64)
}

fn residual_i(mass: f64, rho: f64, h: f64, eta: f64, dims: usize) -> f64 {
    let target = constraint_c(eta, dims) * rho * h.powi(dims as i32);
    let scale = mass.abs().max(target.abs()).max(1e-30);
    (mass - target).abs() / scale
}

pub fn refine(
    field: &mut Field,
    ker: &Handle,
    tol: f64,
    max_steps: usize,
) -> StepReport {
    let n = field.particles.len();
    let c = constraint_c(field.eta, field.dims);
    let mut worst = f64::INFINITY;
    let mut steps = 0usize;

    let budget = max_steps.max(1).min(1);
    for _ in 0..budget {
        let (rho, _) = estimate_density_field(field, ker);
        for i in 0..n {
            let rho_i = rho[i].max(1e-30);
            let mass_i = field.particles[i].mass;
            let target = mass_i / (c * rho_i);
            let new_h = target.powf(1.0 / (field.dims as f64));
            field.particles[i].h = new_h.max(1e-6);
        }
        let (rho1, _) = estimate_density_field(field, ker);
        worst = 0.0;
        for i in 0..n {
            let r = residual_i(
                field.particles[i].mass,
                rho1[i],
                field.particles[i].h,
                field.eta,
                field.dims,
            );
            if r > worst {
                worst = r;
            }
        }
        steps += 1;
        if worst <= tol {
            break;
        }
    }

    StepReport {
        max_residual: worst,
        converged: worst <= tol,
        steps_run: steps,
    }
}
