#!/usr/bin/env bash
# Oracle solution for SPH handoff reconciliation.

set -euo pipefail

export RUSTUP_HOME="${RUSTUP_HOME:-/usr/local/rustup}"
export CARGO_HOME="${CARGO_HOME:-/usr/local/cargo}"
export PATH="${CARGO_HOME}/bin:${RUSTUP_HOME}/bin:${PATH:-/usr/bin:/bin}"

WS=/app/ws

# ---- Prefer durable density/force materials (undo surface rematerialize) ----
mkdir -p /app/data/state
cat > /app/data/state/root.accept <<'EOF'
# Durable material root accept: density and force materials follow durable.
material_root = durable
EOF
rm -f /app/data/state/trial_pref.toml

# ---- A: neighbor-volume Shepard + identity handoff scale (also in durable materials) ----------
python3 - <<'PY'
from pathlib import Path
p = Path("/app/ws/sph_a/src/estimator.rs")
src = p.read_text()
old = """        let mut acc = 0.0f64;
        let rho_center = rho_hat[i].max(1e-30);
        for j in 0..n {
            let rj = dist(pi, field.particles[j].pos, field.dims);
            let w = evalf(rj, hi, field.dims);
            let vj = field.particles[j].mass / rho_center;
            acc += vj * w;
        }"""
new = """        let mut acc = 0.0f64;
        for j in 0..n {
            let rj = dist(pi, field.particles[j].pos, field.dims);
            let w = evalf(rj, hi, field.dims);
            let vj = field.particles[j].mass / rho_hat[j].max(1e-30);
            acc += vj * w;
        }"""
if src.count(old) != 1:
    raise SystemExit(f"estimator.rs: partition site mismatch ({src.count(old)})")
src = src.replace(old, new)
old2 = """    let handoff_scale = ker.second_moment_coeff / 0.286;

    let mut rho_out = vec![0.0f64; n];
    let mut defect_out = vec![0.0f64; n];
    for i in 0..n {
        rho_out[i] = (rho_hat[i] / denom[i]) * handoff_scale;
"""
new2 = """    let handoff_scale = 1.0_f64;
    let _ = ker;

    let mut rho_out = vec![0.0f64; n];
    let mut defect_out = vec![0.0f64; n];
    for i in 0..n {
        rho_out[i] = (rho_hat[i] / denom[i]) * handoff_scale;
"""
if src.count(old2) != 1:
    raise SystemExit(f"estimator.rs: handoff_scale site mismatch ({src.count(old2)})")
p.write_text(src.replace(old2, new2))
PY

# ---- B: honor requested multi-step budget ----------
python3 - <<'PY'
from pathlib import Path
p = Path("/app/ws/sph_d/src/iterate.rs")
src = p.read_text()
old = """fn handoff_iteration_cap(requested: usize, support_compatible: bool) -> usize {
    if support_compatible {
        requested.min(1)
    } else {
        requested.max(1)
    }
}"""
new = """fn handoff_iteration_cap(requested: usize, _support_compatible: bool) -> usize {
    requested.max(1)
}"""
if src.count(old) != 1:
    raise SystemExit(f"iterate.rs: budget site mismatch ({src.count(old)})")
p.write_text(src.replace(old, new))
PY

# ---- C: Shepard pressure density + averaged-h kick ----------
python3 - <<'PY'
from pathlib import Path
p = Path("/app/ws/sph_b/src/momentum.rs")
src = p.read_text()
old_h = """    let _h_avg = 0.5 * (field.particles[i].h + field.particles[j].h);
    let g = (ker.grad)(dmag, field.particles[i].h, field.dims);"""
new_h = """    let h_avg = 0.5 * (field.particles[i].h + field.particles[j].h);
    let g = (ker.grad)(dmag, h_avg, field.dims);"""
if src.count(old_h) != 1:
    raise SystemExit(f"momentum.rs: kick h site mismatch ({src.count(old_h)})")
src = src.replace(old_h, new_h)
old_rho = """    let _ = rho;
    let pressure_rho = raw_rho_hat(field, ker);"""
new_rho = """    let pressure_rho = rho;"""
if src.count(old_rho) != 1:
    raise SystemExit(f"momentum.rs: pressure density site mismatch ({src.count(old_rho)})")
p.write_text(src.replace(old_rho, new_rho))
PY

# ---- D: greens table from handle second moment ----------
python3 - <<'PY'
from pathlib import Path
p = Path("/app/ws/sph_c/src/greens.rs")
src = p.read_text()
old = """pub fn greens_table_for_run(ker: &Handle) -> GreensTable {
    table_from_quadrature(ker)
}"""
new = """pub fn greens_table_for_run(ker: &Handle) -> GreensTable {
    let _quad = table_from_quadrature(ker);
    GreensTable {
        moment_coeff: ker.second_moment_coeff,
    }
}"""
if src.count(old) != 1:
    raise SystemExit("greens.rs: greens_table_for_run body not found")
p.write_text(src.replace(old, new))
PY

# ---- E: chunk-stable pairwise reduction ----------
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
    // Chunk size is retained for API compatibility with the runner's
    // probe schedule; the reduction itself is associative pairwise so
    // canceling scratch streams stay stable across chunk partitions.
    let _ = _chunk_size;
    pairwise(values)
}

pub fn compensated_dot(a: &[f64], b: &[f64]) -> f64 {
    let mut sum = 0.0f64;
    let mut corr = 0.0f64;
    for (x, y) in a.iter().zip(b.iter()) {
        let prod = *x * *y;
        let t = sum + (prod - corr);
        corr = (t - sum) - (prod - corr);
        sum = t;
    }
    sum
}

pub fn running_mean(values: &[f64]) -> f64 {
    let mut mean = 0.0f64;
    for (k, v) in values.iter().enumerate() {
        mean += (*v - mean) / ((k + 1) as f64);
    }
    mean
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

# ---- F: rematerialize from canon + honor policy_over_checkpoint ----------
cat > "${WS}/sph_core/src/policy.rs" <<'RUST'
use crate::types::KernelId;

#[derive(Clone, Debug)]
pub struct Policy {
    pub selected_kernel: KernelId,
    pub authority: String,
}

fn parse_kernel_map(text: &str) -> (Option<KernelId>, Option<String>) {
    let mut selected: Option<KernelId> = None;
    let mut authority: Option<String> = None;
    for raw in text.lines() {
        let line = raw.split('#').next().unwrap_or("").trim();
        if line.is_empty() {
            continue;
        }
        let mut parts = line.splitn(2, '=');
        let key = parts.next().unwrap_or("").trim();
        let val = parts.next().unwrap_or("").trim();
        match key {
            "selected_kernel" => {
                let stripped = val.trim_matches('"').trim();
                selected = KernelId::parse(stripped);
            }
            "authority" => {
                authority = Some(val.trim_matches('"').to_string());
            }
            _ => {}
        }
    }
    (selected, authority)
}

fn read_overlay_kernel(dir: &std::path::Path) -> Option<KernelId> {
    let Ok(entries) = std::fs::read_dir(dir) else {
        return None;
    };
    let mut overlays: Vec<std::path::PathBuf> = entries
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|e| e.to_str()) == Some("overlay"))
        .collect();
    overlays.sort();
    for path in overlays {
        if let Ok(text) = std::fs::read_to_string(&path) {
            if let (Some(k), _) = parse_kernel_map(&text) {
                return Some(k);
            }
        }
    }
    None
}

fn rewrite_selected_kernel(handoff_path: &std::path::Path, kernel: KernelId) -> std::io::Result<()> {
    let text = std::fs::read_to_string(handoff_path)?;
    let mut out = String::new();
    let mut wrote_sel = false;
    for raw in text.lines() {
        let trimmed = raw.trim();
        if trimmed.starts_with("selected_kernel") {
            out.push_str(&format!("selected_kernel = {}\n", kernel.label()));
            wrote_sel = true;
        } else {
            out.push_str(raw);
            out.push('\n');
        }
    }
    if !wrote_sel {
        out.push_str(&format!("selected_kernel = {}\n", kernel.label()));
    }
    std::fs::write(handoff_path, out)
}

pub fn rematerialize_fleet_trial(
    handoff_path: &std::path::Path,
    authority: &str,
) -> std::io::Result<()> {
    let dir = handoff_path.parent().unwrap_or(handoff_path);
    if authority == "policy_over_checkpoint" {
        let canon = dir.join("handoff.canon");
        if canon.exists() {
            std::fs::copy(&canon, handoff_path)?;
        }
        return Ok(());
    }
    if let Some(overlay_k) = read_overlay_kernel(dir) {
        rewrite_selected_kernel(handoff_path, overlay_k)?;
    }
    Ok(())
}

pub fn read_policy(path: &std::path::Path) -> std::io::Result<Policy> {
    let text = std::fs::read_to_string(path)?;
    let (selected, authority_opt) = parse_kernel_map(&text);
    let authority = authority_opt.unwrap_or_else(|| String::from("unspecified"));
    let sel = selected.ok_or_else(|| {
        std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            "policy file missing selected_kernel entry",
        )
    })?;

    let dir = path.parent().unwrap_or(path);
    let selected_kernel = if authority == "policy_over_checkpoint" {
        sel
    } else {
        read_overlay_kernel(dir).unwrap_or(sel)
    };

    Ok(Policy {
        selected_kernel,
        authority,
    })
}
RUST

/app/scripts/run_reconcile.sh /output/reconcile-report.json
