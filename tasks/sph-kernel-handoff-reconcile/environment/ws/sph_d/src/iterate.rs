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

/// Collects per-particle residuals for diagnostic output. Returns
/// (worst, mean, count_above_tol) where `worst` is the largest
/// residual, `mean` is the arithmetic mean, and the count is how
/// many particles exceed the given tolerance.
pub fn residual_statistics(
    field: &Field,
    rho: &[f64],
    tol: f64,
) -> (f64, f64, usize) {
    let mut worst = 0.0f64;
    let mut sum = 0.0f64;
    let mut above = 0usize;
    for (i, part) in field.particles.iter().enumerate() {
        let r = residual_i(part.mass, rho[i], part.h, field.eta, field.dims);
        if r > worst {
            worst = r;
        }
        sum += r;
        if r > tol {
            above += 1;
        }
    }
    let mean = if field.particles.is_empty() {
        0.0
    } else {
        sum / (field.particles.len() as f64)
    };
    (worst, mean, above)
}

/// Damping factor for the h-update to prevent oscillatory divergence
/// in strongly non-uniform distributions. Returns a blending weight
/// in [0, 1] where 1 means full Newton step and lower values damp.
pub fn damping_weight(worst_residual: f64, eta: f64) -> f64 {
    let threshold = 0.5 * eta;
    if worst_residual < threshold {
        1.0
    } else {
        (threshold / worst_residual.max(1e-30)).min(1.0).max(0.3)
    }
}

fn supports_compatible(ker: &Handle) -> bool {
    (ker.support_ratio - 2.0).abs() < 1e-12
}

fn handoff_iteration_cap(requested: usize, support_compatible: bool) -> usize {
    if support_compatible {
        requested.min(1)
    } else {
        requested.max(1)
    }
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

    let budget = handoff_iteration_cap(max_steps, supports_compatible(ker));
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
