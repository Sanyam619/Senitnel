pub mod wendland;
pub mod cubic;

use sph_core::types::KernelId;

// A common kernel handle so downstream crates do not care which of
// the two implementations they resolved. `sigma_d(dims)` returns the
// dimension-dependent normalization constant. `support_ratio` is the
// dimensionless radius at which the kernel drops to zero (in units of
// the smoothing length h).

#[derive(Clone, Copy)]
pub struct Handle {
    pub id: KernelId,
    pub support_ratio: f64,
    pub second_moment_coeff: f64,
    pub eval: fn(f64, f64, usize) -> f64,
    pub grad: fn(f64, f64, usize) -> f64,
}

pub fn resolve(id: KernelId) -> Handle {
    match id {
        KernelId::CubicSpline => cubic::handle(),
        KernelId::WendlandC4 => wendland::handle(),
    }
}
