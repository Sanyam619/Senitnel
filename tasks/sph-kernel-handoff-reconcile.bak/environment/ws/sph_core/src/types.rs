// Shared value types used across the runner crates.
//
// The core state is a bag of particles in up to three spatial dimensions
// plus a small metadata record about the run's origin. The runner crates
// consume `Field` values and never touch on-disk representations
// themselves; parsing lives in `sph_core::input`.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum KernelId {
    CubicSpline,
    WendlandC4,
}

impl KernelId {
    pub fn parse(s: &str) -> Option<KernelId> {
        match s.trim() {
            "cubic_spline" => Some(KernelId::CubicSpline),
            "wendland_c4" => Some(KernelId::WendlandC4),
            _ => None,
        }
    }

    pub fn label(self) -> &'static str {
        match self {
            KernelId::CubicSpline => "cubic_spline",
            KernelId::WendlandC4 => "wendland_c4",
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub struct Vec3 {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

impl Vec3 {
    pub fn zero() -> Self {
        Vec3 { x: 0.0, y: 0.0, z: 0.0 }
    }

    pub fn add(self, other: Vec3) -> Vec3 {
        Vec3 {
            x: self.x + other.x,
            y: self.y + other.y,
            z: self.z + other.z,
        }
    }

    pub fn sub(self, other: Vec3) -> Vec3 {
        Vec3 {
            x: self.x - other.x,
            y: self.y - other.y,
            z: self.z - other.z,
        }
    }

    pub fn scale(self, s: f64) -> Vec3 {
        Vec3 { x: self.x * s, y: self.y * s, z: self.z * s }
    }

    pub fn norm(self) -> f64 {
        (self.x * self.x + self.y * self.y + self.z * self.z).sqrt()
    }

    pub fn cross(self, other: Vec3) -> Vec3 {
        Vec3 {
            x: self.y * other.z - self.z * other.y,
            y: self.z * other.x - self.x * other.z,
            z: self.x * other.y - self.y * other.x,
        }
    }
}

#[derive(Clone, Debug)]
pub struct Particle {
    pub pos: Vec3,
    pub vel: Vec3,
    pub mass: f64,
    pub h: f64,
    pub internal_energy: f64,
}

#[derive(Clone, Debug)]
pub struct Field {
    pub particles: Vec<Particle>,
    pub dims: usize,
    pub eta: f64,
    pub adiabatic_gamma: f64,
    pub scenario_id: String,
    pub embedded_kernel: KernelId,
    pub self_gravitating: bool,
}

#[derive(Clone, Debug)]
pub struct Bands {
    pub moment_zero: f64,
    pub h_consistency: f64,
    pub momentum: f64,
    pub angular: f64,
    pub mass: f64,
    pub gravity_virial: f64,
    pub chunk_stability: f64,
}

#[derive(Clone, Debug)]
pub struct ScenarioSpec {
    pub scenario: String,
    pub layout: String,
    pub source_kernel: KernelId,
    pub n_particles: usize,
    pub seed: u64,
    pub dims: usize,
    pub eta: f64,
    pub gamma: f64,
    pub self_gravitating: bool,
    pub bands: Bands,
}
