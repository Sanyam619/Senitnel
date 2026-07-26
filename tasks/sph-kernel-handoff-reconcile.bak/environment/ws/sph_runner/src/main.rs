mod report;
mod layouts;

use std::path::{Path, PathBuf};

use sph_core::input::read_scenario;
use sph_core::policy::read_policy;
use sph_core::types::{Field, KernelId, ScenarioSpec};
use sph_a::estimator::estimate_density_field;
use sph_a::reduce::chunk_stability_delta;
use sph_b::momentum::{angular_residual, compute_accel, momentum_residual};
use sph_c::greens::virial_residual;
use sph_d::iterate::refine;

use report::{Report, ScenarioRow};

fn build_field(spec: &ScenarioSpec, target: KernelId) -> Field {
    let particles = layouts::synthesize(spec);
    Field {
        particles,
        dims: spec.dims,
        eta: spec.eta,
        adiabatic_gamma: spec.gamma,
        scenario_id: spec.scenario.clone(),
        embedded_kernel: target,
        self_gravitating: spec.self_gravitating,
    }
}

fn kernel_mass_residual(field: &Field, ker: &sph_kernels::Handle) -> f64 {
    let (rho, _) = estimate_density_field(field, ker);
    let d = field.dims as f64;
    let c = 1.0 / field.eta.powf(d);
    let mut worst = 0.0f64;
    for (i, part) in field.particles.iter().enumerate() {
        let target = c * rho[i] * part.h.powi(field.dims as i32);
        let scale = part.mass.abs().max(target.abs()).max(1e-30);
        let r = (part.mass - target).abs() / scale;
        if r > worst {
            worst = r;
        }
    }
    worst
}

fn per_particle_reduction_probes(field: &Field, ker: &sph_kernels::Handle) -> Vec<f64> {
    // Build a mixed-magnitude, mixed-sign probe stream. Each particle
    // contributes:
    //   - its physical contribution (mass * moment_zero * (rho + 1))
    //   - a large positive scratch value
    //   - the exact negation of that scratch value
    // In exact arithmetic the scratch pair cancels; in plain FP the
    // pairing depends on chunk boundaries, so any reducer whose output
    // is not chunk-size invariant shifts by a chunk-dependent amount
    // that swamps the physical signal.
    let (rho, moment_zero) = estimate_density_field(field, ker);
    let mut out = Vec::with_capacity(field.particles.len() * 3);
    for (i, part) in field.particles.iter().enumerate() {
        let phys = part.mass * moment_zero[i] * (rho[i] + 1.0);
        let scratch = 1.0e10_f64 * ((i as f64).sin() + 1.25);
        out.push(phys);
        out.push(scratch);
        out.push(-scratch);
    }
    out
}

fn run_scenario(spec: &ScenarioSpec, target: KernelId) -> ScenarioRow {
    let ker = sph_kernels::resolve(target);
    let mut field = build_field(spec, target);

    let step = refine(&mut field, &ker, 1e-2, 30);
    let (_, defect) = estimate_density_field(&field, &ker);
    let mz_resid = defect.iter().fold(0.0f64, |acc, m| acc.max(m.abs()));

    let h_resid = kernel_mass_residual(&field, &ker);

    let (rho, _) = estimate_density_field(&field, &ker);
    let bundle = compute_accel(&field, &ker, &rho);
    let mom = momentum_residual(&field, &bundle);
    let ang = angular_residual(&field, &bundle);

    let virial = virial_residual(&field, &ker);

    let contribs = per_particle_reduction_probes(&field, &ker);
    let chunk_delta = chunk_stability_delta(&contribs, &[1, 8, 32, contribs.len().max(1)]);

    ScenarioRow {
        scenario: spec.scenario.clone(),
        kernel_source: spec.source_kernel.label().to_string(),
        kernel_target: target.label().to_string(),
        particles: field.particles.len(),
        converged: step.converged,
        moment_zero_residual: mz_resid,
        h_consistency_residual: h_resid,
        momentum_residual: mom,
        angular_residual: ang,
        gravity_virial_residual: virial,
        chunk_stability_delta: chunk_delta,
    }
}

fn discover_checkpoints(dir: &Path) -> Vec<PathBuf> {
    let mut out: Vec<PathBuf> = Vec::new();
    if let Ok(read) = std::fs::read_dir(dir) {
        for ent in read.flatten() {
            let p = ent.path();
            if p.extension().and_then(|e| e.to_str()) == Some("spec") {
                out.push(p);
            }
        }
    }
    out.sort();
    out
}

fn main() -> std::io::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    let out_path = args.get(1).cloned().unwrap_or_else(|| {
        "/output/reconcile-report.json".to_string()
    });

    let policy_path = Path::new("/app/data/policy/handoff.spec");
    let policy = read_policy(policy_path)?;
    let target = policy.selected_kernel;

    let ck_dir = Path::new("/app/data/checkpoints");
    let files = discover_checkpoints(ck_dir);

    let mut rows: Vec<ScenarioRow> = Vec::new();
    for f in files {
        let spec = read_scenario(&f)?;
        rows.push(run_scenario(&spec, target));
    }

    let report = Report {
        schema_tag: "sph-reconcile-v1".to_string(),
        scenarios: rows,
    };
    let rendered = report::render(&report);

    if let Some(parent) = Path::new(&out_path).parent() {
        std::fs::create_dir_all(parent)?;
    }
    std::fs::write(&out_path, rendered)?;
    Ok(())
}
