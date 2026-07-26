// Verifier-owned behavioral checker. tests/conftest.py copies this over
// /app/ws/sph_verify/src/main.rs on every verifier invocation so it
// always links against the current internal crates.

use sph_core::types::{Field, KernelId, Particle, Vec3};
use sph_a::estimator::estimate_density_field;
use sph_a::reduce::{chunk_stability_delta, reduce_chunks};
use sph_b::momentum::{angular_residual, compute_accel, momentum_residual};
use sph_c::greens::greens_table_for_run;
use sph_d::iterate::refine;
use sph_kernels::resolve;

fn die(msg: String) -> ! {
    eprintln!("{}", msg);
    std::process::exit(1);
}

fn active_kernel() -> sph_kernels::Handle {
    resolve(KernelId::WendlandC4)
}

fn irregular_3d_field(n_side: usize, dims: usize) -> Field {
    let mut parts: Vec<Particle> = Vec::new();
    let step = 1.0 / (n_side as f64);
    for ix in 0..n_side {
        for iy in 0..n_side {
            let iz_max = if dims >= 3 { n_side } else { 1 };
            for iz in 0..iz_max {
                let px = -0.5 + (ix as f64 + 0.5) * step;
                let py = if dims >= 2 { -0.5 + (iy as f64 + 0.5) * step } else { 0.0 };
                let pz = if dims >= 3 { -0.5 + (iz as f64 + 0.5) * step } else { 0.0 };
                let jit = |k: usize, salt: f64| -> f64 {
                    let x = ((k as f64) * 12.9898 + salt).sin() * 43758.5453;
                    (x - x.floor()) * 0.25 * step - 0.125 * step
                };
                let idx = ix * n_side * n_side + iy * n_side + iz;
                parts.push(Particle {
                    pos: Vec3 {
                        x: px + jit(idx, 1.0),
                        y: py + if dims >= 2 { jit(idx, 2.0) } else { 0.0 },
                        z: pz + if dims >= 3 { jit(idx, 3.0) } else { 0.0 },
                    },
                    vel: Vec3::zero(),
                    mass: 1.0 / ((n_side * n_side * iz_max) as f64),
                    h: 1.6 * step,
                    internal_energy: 1.0 + 0.1 * (idx as f64),
                });
            }
        }
    }
    Field {
        particles: parts,
        dims,
        eta: 1.2,
        adiabatic_gamma: 5.0 / 3.0,
        scenario_id: "verifier".to_string(),
        embedded_kernel: KernelId::WendlandC4,
        self_gravitating: false,
    }
}

fn dist(a: Vec3, b: Vec3, dims: usize) -> f64 {
    let d = a.sub(b);
    match dims {
        1 => d.x.abs(),
        2 => (d.x * d.x + d.y * d.y).sqrt(),
        _ => d.norm(),
    }
}

fn reference_density(field: &Field, ker: &sph_kernels::Handle) -> Vec<f64> {
    let n = field.particles.len();
    let evalf = ker.eval;
    let mut rho_hat = vec![0.0f64; n];
    for i in 0..n {
        let hi = field.particles[i].h;
        let pi = field.particles[i].pos;
        let mut acc = 0.0f64;
        for j in 0..n {
            let rj = dist(pi, field.particles[j].pos, field.dims);
            acc += field.particles[j].mass * evalf(rj, hi, field.dims);
        }
        rho_hat[i] = acc;
    }
    let mut out = vec![0.0f64; n];
    for i in 0..n {
        let hi = field.particles[i].h;
        let pi = field.particles[i].pos;
        let mut denom = 0.0f64;
        for j in 0..n {
            let rj = dist(pi, field.particles[j].pos, field.dims);
            let w = evalf(rj, hi, field.dims);
            let vj = field.particles[j].mass / rho_hat[j].max(1e-30);
            denom += vj * w;
        }
        out[i] = rho_hat[i] / denom.max(1e-30);
    }
    out
}

fn check_normalization() {
    let field = irregular_3d_field(3, 3);
    let ker = active_kernel();
    let (rho, _) = estimate_density_field(&field, &ker);
    let expect = reference_density(&field, &ker);
    if rho.len() != expect.len() {
        die(format!("probe density: length mismatch {} vs {}", rho.len(), expect.len()));
    }
    for i in 0..rho.len() {
        let scale = expect[i].abs().max(1e-30);
        let err = (rho[i] - expect[i]).abs() / scale;
        if !err.is_finite() || err > 1.0e-10 {
            die(format!(
                "probe density: particle {} relative error {:.3e}",
                i, err
            ));
        }
        if !rho[i].is_finite() || rho[i] <= 0.0 {
            die(format!("probe density: non-positive rho at {}: {:e}", i, rho[i]));
        }
    }
}

fn check_h_iterate() {
    let mut field = irregular_3d_field(3, 3);
    for p in field.particles.iter_mut() {
        p.h *= 1.9;
    }
    let ker = active_kernel();
    let tol = 1.0e-6f64;
    let step = refine(&mut field, &ker, tol, 30);
    if !step.max_residual.is_finite() {
        die(format!("probe h-pass: non-finite residual {}", step.max_residual));
    }
    if step.max_residual > tol {
        die(format!(
            "probe h-pass: residual {:.3e} exceeds tol {:.3e} after {} steps",
            step.max_residual, tol, step.steps_run
        ));
    }
    if !step.converged {
        die(format!(
            "probe h-pass: residual {:.3e} but converged=false",
            step.max_residual
        ));
    }
    if step.steps_run < 2 {
        die(format!(
            "probe h-pass: expected multi-step refinement, got steps_run={}",
            step.steps_run
        ));
    }
}

fn check_symmetry() {
    let mut parts: Vec<Particle> = Vec::new();
    let positions = [
        (0.10, 0.05, 0.02),
        (-0.08, 0.11, -0.06),
        (0.03, -0.13, 0.09),
        (-0.12, -0.02, -0.05),
    ];
    let masses = [1.0, 1.4, 0.9, 1.2];
    let energies = [1.0, 1.8, 0.7, 1.3];
    for (i, (px, py, pz)) in positions.iter().enumerate() {
        parts.push(Particle {
            pos: Vec3 { x: *px, y: *py, z: *pz },
            vel: Vec3::zero(),
            mass: masses[i],
            h: 0.20 + 0.03 * (i as f64),
            internal_energy: energies[i],
        });
    }
    let field = Field {
        particles: parts,
        dims: 3,
        eta: 1.2,
        adiabatic_gamma: 5.0 / 3.0,
        scenario_id: "verifier-sym".to_string(),
        embedded_kernel: KernelId::WendlandC4,
        self_gravitating: false,
    };
    let ker = active_kernel();
    let (rho, _) = estimate_density_field(&field, &ker);
    let bundle = compute_accel(&field, &ker, &rho);
    let m = momentum_residual(&field, &bundle);
    let a = angular_residual(&field, &bundle);
    if !m.is_finite() || m > 1.0e-12 {
        die(format!("probe pairwise: linear residual {:.3e}", m));
    }
    if !a.is_finite() || a > 1.0e-12 {
        die(format!("probe pairwise: angular residual {:.3e}", a));
    }
}

fn check_greens() {
    let ker = active_kernel();
    let used = greens_table_for_run(&ker);
    if (used.moment_coeff - ker.second_moment_coeff).abs() > 1.0e-15 {
        die(format!(
            "probe greens: coeff {:.6} vs handle {:.6}",
            used.moment_coeff, ker.second_moment_coeff
        ));
    }
}

fn check_chunk_reduce() {
    let n = 400usize;
    let mut vals: Vec<f64> = Vec::with_capacity(n * 3);
    for i in 0..n {
        let x = i as f64;
        let phys = 1.0e-6 * ((x * 0.017).sin() + 1.25);
        let scratch = 1.0e10 * ((x * 0.031).cos() + 1.5);
        vals.push(phys);
        vals.push(scratch);
        vals.push(-scratch);
    }
    let probes: [usize; 6] = [1, 3, 7, 13, 128, vals.len()];
    let ref_val = reduce_chunks(&vals, probes[0]);
    for &p in probes.iter() {
        let v = reduce_chunks(&vals, p);
        let diff = (v - ref_val).abs();
        let scale = ref_val.abs().max(v.abs()).max(1.0e-30);
        if diff / scale > 1.0e-12 {
            die(format!(
                "probe reduce: chunk {} relative drift {:.3e}",
                p,
                diff / scale
            ));
        }
    }
    let delta = chunk_stability_delta(&vals, &probes);
    if !delta.is_finite() || delta > 1.0e-12 {
        die(format!("probe reduce: stability delta {:.3e}", delta));
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let sub = args.get(1).map(|s| s.as_str()).unwrap_or("");
    match sub {
        "normalization" => check_normalization(),
        "hiterate" => check_h_iterate(),
        "symmetry" => check_symmetry(),
        "greens" => check_greens(),
        "chunkreduce" => check_chunk_reduce(),
        "all" => {
            check_normalization();
            check_h_iterate();
            check_symmetry();
            check_greens();
            check_chunk_reduce();
        }
        _ => die("usage: sph-verify <normalization|hiterate|symmetry|greens|chunkreduce|all>".to_string()),
    }
    println!("OK");
}
