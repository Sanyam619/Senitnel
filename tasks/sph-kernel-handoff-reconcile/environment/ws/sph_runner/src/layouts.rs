use sph_core::types::{Particle, ScenarioSpec, Vec3};

// Deterministic particle synthesis for each scenario. Uses a simple
// linear congruential generator seeded from the scenario spec so the
// runner produces identical particle fields across builds.

pub struct Lcg {
    state: u64,
}

impl Lcg {
    pub fn new(seed: u64) -> Self {
        Lcg { state: seed.wrapping_add(0x9E37_79B9_7F4A_7C15) }
    }
    pub fn next_f64(&mut self) -> f64 {
        self.state = self
            .state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        ((self.state >> 11) as f64) / ((1u64 << 53) as f64)
    }
    pub fn range(&mut self, lo: f64, hi: f64) -> f64 {
        lo + (hi - lo) * self.next_f64()
    }
}

pub fn synthesize(spec: &ScenarioSpec) -> Vec<Particle> {
    match spec.layout.as_str() {
        "sod" => sod(spec),
        "sedov" => sedov(spec),
        "kh" => kelvin_helmholtz(spec),
        "poly" => polytropic_star(spec),
        _ => uniform_cube(spec),
    }
}

fn sod(spec: &ScenarioSpec) -> Vec<Particle> {
    let mut rng = Lcg::new(spec.seed);
    let mut out = Vec::with_capacity(spec.n_particles);
    let n_left = spec.n_particles * 4 / 5;
    let n_right = spec.n_particles - n_left;
    let dx_l = 0.5 / (n_left as f64);
    let dx_r = 0.5 / (n_right as f64);

    for i in 0..n_left {
        let x = -0.5 + (i as f64 + 0.5) * dx_l + rng.range(-0.35 * dx_l, 0.35 * dx_l);
        out.push(Particle {
            pos: Vec3 { x, y: 0.0, z: 0.0 },
            vel: Vec3::zero(),
            mass: 1.0 / (spec.n_particles as f64),
            h: 2.0 * dx_l,
            internal_energy: 2.5 + 0.02 * rng.next_f64(),
        });
    }
    for i in 0..n_right {
        let x = 0.0 + (i as f64 + 0.5) * dx_r + rng.range(-0.35 * dx_r, 0.35 * dx_r);
        out.push(Particle {
            pos: Vec3 { x, y: 0.0, z: 0.0 },
            vel: Vec3::zero(),
            mass: 1.0 / (spec.n_particles as f64),
            h: 2.0 * dx_r,
            internal_energy: 1.795 + 0.02 * rng.next_f64(),
        });
    }
    out
}

fn sedov(spec: &ScenarioSpec) -> Vec<Particle> {
    let mut rng = Lcg::new(spec.seed);
    let mut out = Vec::with_capacity(spec.n_particles);
    let side = (spec.n_particles as f64).powf(1.0 / 3.0).ceil() as usize;
    let dx = 1.0 / (side as f64);
    let jitter = 0.35 * dx;
    let mut count = 0usize;
    'outer: for ix in 0..side {
        for iy in 0..side {
            for iz in 0..side {
                if count >= spec.n_particles {
                    break 'outer;
                }
                let x = (ix as f64 + 0.5) * dx - 0.5 + rng.range(-jitter, jitter);
                let y = (iy as f64 + 0.5) * dx - 0.5 + rng.range(-jitter, jitter);
                let z = (iz as f64 + 0.5) * dx - 0.5 + rng.range(-jitter, jitter);
                let r2 = x * x + y * y + z * z;
                let u = if r2 < 0.02 { 400.0 + 100.0 * rng.next_f64() } else { 1e-3 + 5e-4 * rng.next_f64() };
                out.push(Particle {
                    pos: Vec3 { x, y, z },
                    vel: Vec3 {
                        x: 0.01 * rng.range(-1.0, 1.0),
                        y: 0.01 * rng.range(-1.0, 1.0),
                        z: 0.01 * rng.range(-1.0, 1.0),
                    },
                    mass: 1.0 / (spec.n_particles as f64),
                    h: 1.7 * dx,
                    internal_energy: u,
                });
                count += 1;
            }
        }
    }
    out
}

fn kelvin_helmholtz(spec: &ScenarioSpec) -> Vec<Particle> {
    let mut rng = Lcg::new(spec.seed);
    let mut out = Vec::with_capacity(spec.n_particles);
    let side = (spec.n_particles as f64).sqrt().ceil() as usize;
    let dx = 1.0 / (side as f64);
    let jitter = 0.35 * dx;
    let mut count = 0usize;
    'outer: for iy in 0..side {
        for ix in 0..side {
            if count >= spec.n_particles {
                break 'outer;
            }
            let x = (ix as f64 + 0.5) * dx - 0.5 + rng.range(-jitter, jitter);
            let y = (iy as f64 + 0.5) * dx - 0.5 + rng.range(-jitter, jitter);
            let vx = if y.abs() < 0.25 { 0.5 } else { -0.5 };
            let u = if y.abs() < 0.25 { 2.5 } else { 3.0 };
            out.push(Particle {
                pos: Vec3 { x, y, z: 0.0 },
                vel: Vec3 { x: vx + 0.02 * rng.range(-1.0, 1.0), y: 0.02 * rng.range(-1.0, 1.0), z: 0.0 },
                mass: 1.0 / (spec.n_particles as f64),
                h: 1.7 * dx,
                internal_energy: u,
            });
            count += 1;
        }
    }
    out
}

fn polytropic_star(spec: &ScenarioSpec) -> Vec<Particle> {
    let mut rng = Lcg::new(spec.seed);
    let mut out = Vec::with_capacity(spec.n_particles);
    let mut count = 0usize;
    let radius_max = 0.5f64;
    while count < spec.n_particles {
        let x = rng.range(-radius_max, radius_max);
        let y = rng.range(-radius_max, radius_max);
        let z = rng.range(-radius_max, radius_max);
        let r = (x * x + y * y + z * z).sqrt();
        if r > radius_max {
            continue;
        }
        let accept_prob = 1.0 - (r / radius_max).powi(2);
        if rng.next_f64() > accept_prob {
            continue;
        }
        let m = 1.0 / (spec.n_particles as f64);
        out.push(Particle {
            pos: Vec3 { x, y, z },
            vel: Vec3 {
                x: 0.005 * rng.range(-1.0, 1.0),
                y: 0.005 * rng.range(-1.0, 1.0),
                z: 0.005 * rng.range(-1.0, 1.0),
            },
            mass: m,
            h: 0.08,
            internal_energy: 1.0 + 0.5 * (radius_max - r),
        });
        count += 1;
    }
    out
}

fn uniform_cube(spec: &ScenarioSpec) -> Vec<Particle> {
    let mut rng = Lcg::new(spec.seed);
    let mut out = Vec::with_capacity(spec.n_particles);
    for _ in 0..spec.n_particles {
        out.push(Particle {
            pos: Vec3 {
                x: rng.range(-0.5, 0.5),
                y: rng.range(-0.5, 0.5),
                z: rng.range(-0.5, 0.5),
            },
            vel: Vec3::zero(),
            mass: 1.0 / (spec.n_particles as f64),
            h: 0.1,
            internal_energy: 1.0,
        });
    }
    out
}
