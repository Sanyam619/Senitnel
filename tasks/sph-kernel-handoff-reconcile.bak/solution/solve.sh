#!/usr/bin/env bash
# Oracle solution for SPH handoff reconciliation.

set -euo pipefail

WS=/app/ws

# ---- Fix A: Shepard-normalized density publish --------------------
cat > "${WS}/sph_a/src/estimator.rs" <<'RUST'
use sph_core::types::{Field, Vec3};
use sph_kernels::Handle;

fn dist(a: Vec3, b: Vec3, dims: usize) -> f64 {
    let d = a.sub(b);
    match dims {
        1 => d.x.abs(),
        2 => (d.x * d.x + d.y * d.y).sqrt(),
        _ => d.norm(),
    }
}

fn compute_rho_hat(field: &Field, ker: &Handle) -> Vec<f64> {
    let n = field.particles.len();
    let mut out = vec![0.0f64; n];
    let evalf = ker.eval;
    for i in 0..n {
        let hi = field.particles[i].h;
        let pi = field.particles[i].pos;
        let mut acc = 0.0f64;
        for j in 0..n {
            let rj = dist(pi, field.particles[j].pos, field.dims);
            let w = evalf(rj, hi, field.dims);
            acc += field.particles[j].mass * w;
        }
        out[i] = acc;
    }
    out
}

fn compute_shepard_hat(field: &Field, ker: &Handle, rho_hat: &[f64]) -> Vec<f64> {
    let n = field.particles.len();
    let mut out = vec![0.0f64; n];
    let evalf = ker.eval;
    for i in 0..n {
        let hi = field.particles[i].h;
        let pi = field.particles[i].pos;
        let mut acc = 0.0f64;
        for j in 0..n {
            let rj = dist(pi, field.particles[j].pos, field.dims);
            let w = evalf(rj, hi, field.dims);
            let vj = field.particles[j].mass / rho_hat[j].max(1e-30);
            acc += vj * w;
        }
        out[i] = acc.max(1e-30);
    }
    out
}

pub fn estimate_density_field(field: &Field, ker: &Handle) -> (Vec<f64>, Vec<f64>) {
    let n = field.particles.len();
    let rho_hat = compute_rho_hat(field, ker);
    let shepard_hat = compute_shepard_hat(field, ker, &rho_hat);

    let mut rho_out = vec![0.0f64; n];
    let mut defect_out = vec![0.0f64; n];
    for i in 0..n {
        let target = rho_hat[i] / shepard_hat[i];
        rho_out[i] = target;
        let scale = rho_hat[i].max(1e-30);
        defect_out[i] = (rho_out[i] - target).abs() / scale;
    }

    (rho_out, defect_out)
}
RUST

# ---- Fix B: honor max_steps budget (was clamped to 1) -------------
python3 - <<'PY'
from pathlib import Path
p = Path("/app/ws/sph_d/src/iterate.rs")
src = p.read_text()
old = "    let budget = max_steps.max(1).min(1);"
new = "    let budget = max_steps.max(1);"
if src.count(old) != 1:
    raise SystemExit(f"iterate.rs: expected one clamp site, got {src.count(old)}")
p.write_text(src.replace(old, new))
PY

# ---- Fix C: symmetric pairwise pressure kick ----------------------
python3 - <<'PY'
from pathlib import Path
p = Path("/app/ws/sph_b/src/momentum.rs")
src = p.read_text()
old = """fn kick_from_i_on_j(field: &Field, ker: &Handle, rho: &[f64], i: usize, j: usize) -> Vec3 {
    let gm1 = field.adiabatic_gamma - 1.0;
    let (dv, dmag) = dist_vec(field.particles[i].pos, field.particles[j].pos, field.dims);
    if dmag <= 0.0 {
        return Vec3::zero();
    }
    let g = (ker.grad)(dmag, field.particles[i].h, field.dims);
    if g == 0.0 {
        return Vec3::zero();
    }
    let rho_i = rho[i].max(1e-30);
    let p_i = gm1 * rho_i * field.particles[i].internal_energy;
    let coeff = -field.particles[j].mass * (p_i / (rho_i * rho_i)) * g;
    let ux = dv.x / dmag;
    let uy = dv.y / dmag;
    let uz = dv.z / dmag;
    Vec3 { x: coeff * ux, y: coeff * uy, z: coeff * uz }
}
"""
new = """fn kick_from_i_on_j(field: &Field, ker: &Handle, rho: &[f64], i: usize, j: usize) -> Vec3 {
    let gm1 = field.adiabatic_gamma - 1.0;
    let (dv, dmag) = dist_vec(field.particles[i].pos, field.particles[j].pos, field.dims);
    if dmag <= 0.0 {
        return Vec3::zero();
    }
    let h_avg = 0.5 * (field.particles[i].h + field.particles[j].h);
    let g = (ker.grad)(dmag, h_avg, field.dims);
    if g == 0.0 {
        return Vec3::zero();
    }
    let rho_i = rho[i].max(1e-30);
    let rho_j = rho[j].max(1e-30);
    let p_i = gm1 * rho_i * field.particles[i].internal_energy;
    let p_j = gm1 * rho_j * field.particles[j].internal_energy;
    let sym = p_i / (rho_i * rho_i) + p_j / (rho_j * rho_j);
    let coeff = -field.particles[j].mass * sym * g;
    let ux = dv.x / dmag;
    let uy = dv.y / dmag;
    let uz = dv.z / dmag;
    Vec3 { x: coeff * ux, y: coeff * uy, z: coeff * uz }
}
"""
if src.count(old) != 1:
    raise SystemExit("momentum.rs: kick_from_i_on_j body not found")
p.write_text(src.replace(old, new))
PY

# ---- Fix D: greens coefficient from active kernel -----------------
python3 - <<'PY'
from pathlib import Path
p = Path("/app/ws/sph_c/src/greens.rs")
src = p.read_text()
old = """pub fn greens_table_for_run(_ker: &Handle) -> GreensTable {
    GreensTable {
        moment_coeff: 0.286,
    }
}
"""
new = """pub fn greens_table_for_run(ker: &Handle) -> GreensTable {
    GreensTable {
        moment_coeff: ker.second_moment_coeff,
    }
}
"""
if src.count(old) != 1:
    raise SystemExit("greens.rs: greens_table_for_run body not found")
p.write_text(src.replace(old, new))
PY

# ---- Fix E: pairwise-tree reduction -------------------------------
cat > "${WS}/sph_a/src/reduce.rs" <<'RUST'
fn pairwise(vals: &[f64]) -> f64 {
    if vals.is_empty() {
        return 0.0;
    }
    if vals.len() <= 8 {
        let mut s = 0.0f64;
        for &v in vals {
            s += v;
        }
        return s;
    }
    let mid = vals.len() / 2;
    pairwise(&vals[..mid]) + pairwise(&vals[mid..])
}

pub fn reduce_chunks(values: &[f64], _chunk_size: usize) -> f64 {
    pairwise(values)
}

pub fn chunk_stability_delta(values: &[f64], probes: &[usize]) -> f64 {
    if probes.is_empty() {
        return 0.0;
    }
    let mut lo = f64::INFINITY;
    let mut hi = f64::NEG_INFINITY;
    for &p in probes {
        let v = reduce_chunks(values, p);
        if v < lo {
            lo = v;
        }
        if v > hi {
            hi = v;
        }
    }
    let scale = hi.abs().max(lo.abs()).max(1e-30);
    (hi - lo).abs() / scale
}
RUST

/app/scripts/run_reconcile.sh /output/reconcile-report.json
