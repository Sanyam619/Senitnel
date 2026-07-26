use crate::types::{Bands, KernelId, ScenarioSpec};

// Parses the /app/data/checkpoints/*.spec key=value manifest into a
// ScenarioSpec value. The particle field is reconstructed downstream
// from (layout, seed, n_particles, dims) by sph_runner so on-disk
// checkpoints stay small.

pub fn read_scenario(path: &std::path::Path) -> std::io::Result<ScenarioSpec> {
    let text = std::fs::read_to_string(path)?;
    let mut scenario = String::new();
    let mut layout = String::new();
    let mut source_kernel: Option<KernelId> = None;
    let mut n_particles: usize = 0;
    let mut seed: u64 = 0;
    let mut dims: usize = 3;
    let mut eta: f64 = 1.2;
    let mut gamma: f64 = 5.0 / 3.0;
    let mut self_grav: bool = false;
    let mut moment_zero: f64 = 0.0;
    let mut h_consistency: f64 = 0.0;
    let mut momentum: f64 = 0.0;
    let mut angular: f64 = 0.0;
    let mut mass: f64 = 0.0;
    let mut gravity_virial: f64 = f64::INFINITY;
    let mut chunk_stability: f64 = 0.0;

    for raw in text.lines() {
        let line = raw.split('#').next().unwrap_or("").trim();
        if line.is_empty() {
            continue;
        }
        let mut parts = line.splitn(2, '=');
        let key = parts.next().unwrap_or("").trim();
        let val = parts.next().unwrap_or("").trim();
        let val = val.trim_matches('"');
        match key {
            "scenario" => scenario = val.to_string(),
            "layout" => layout = val.to_string(),
            "source_kernel" => source_kernel = KernelId::parse(val),
            "n_particles" => n_particles = val.parse().unwrap_or(0),
            "seed" => seed = val.parse().unwrap_or(0),
            "dims" => dims = val.parse().unwrap_or(3),
            "eta" => eta = val.parse().unwrap_or(1.2),
            "gamma" => gamma = val.parse().unwrap_or(5.0 / 3.0),
            "self_gravitating" => self_grav = val.eq_ignore_ascii_case("true"),
            "band_moment_zero" => moment_zero = val.parse().unwrap_or(0.0),
            "band_h_consistency" => h_consistency = val.parse().unwrap_or(0.0),
            "band_momentum" => momentum = val.parse().unwrap_or(0.0),
            "band_angular" => angular = val.parse().unwrap_or(0.0),
            "band_mass" => mass = val.parse().unwrap_or(0.0),
            "band_gravity_virial" => gravity_virial = val.parse().unwrap_or(f64::INFINITY),
            "band_chunk_stability" => chunk_stability = val.parse().unwrap_or(0.0),
            _ => {}
        }
    }

    let src = source_kernel.ok_or_else(|| {
        std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            "checkpoint spec missing source_kernel entry",
        )
    })?;

    Ok(ScenarioSpec {
        scenario,
        layout,
        source_kernel: src,
        n_particles,
        seed,
        dims,
        eta,
        gamma,
        self_gravitating: self_grav,
        bands: Bands {
            moment_zero,
            h_consistency,
            momentum,
            angular,
            mass,
            gravity_virial,
            chunk_stability,
        },
    })
}
