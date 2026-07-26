//! Build-time authority guard.
//!
//! Deep attestation must be driven by durable authority. Until the operator
//! commits a durable-authority preference (`/app/ops/prefer.toml` selecting the
//! durable source, and `/app/ops/tip_bind.accept` naming the authority class the
//! trust policy selects), this guard rematerializes the evaluator sources from
//! the surface baseline on every rebuild. Source-level repairs made while the
//! preference still points at the surface snapshot do not survive a rebuild.

use std::fs;
use std::path::{Path, PathBuf};

const OPS_ROOT: &str = "/app/ops";
const GUARDED: [&str; 5] = ["fold_a", "sieve_b", "main", "emit_c", "skim_fold"];

fn toml_value(text: &str, key: &str) -> Option<String> {
    for line in text.lines() {
        let t = line.trim();
        if t.starts_with('#') {
            continue;
        }
        if let Some(rest) = t.strip_prefix(key) {
            let rest = rest.trim_start();
            if let Some(v) = rest.strip_prefix('=') {
                return Some(v.trim().trim_matches('"').to_string());
            }
        }
    }
    None
}

fn read_opt(path: &Path) -> String {
    fs::read_to_string(path).unwrap_or_default()
}

/// The guard stands down only when the durable-authority preference is
/// committed and its bind acceptance names the policy-selected authority class.
fn durable_committed() -> bool {
    let ops = Path::new(OPS_ROOT);
    let prefer = read_opt(&ops.join("prefer.toml"));
    let policy = read_opt(&ops.join("trust_policy.toml"));
    let accept = read_opt(&ops.join("tip_bind.accept"));

    let source = toml_value(&prefer, "source").unwrap_or_default();
    let authority = toml_value(&policy, "authority").unwrap_or_default();
    let bind = toml_value(&accept, "bind").unwrap_or_default();

    !authority.is_empty() && source == "durable" && bind == authority
}

fn main() {
    let manifest_dir = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap_or_default());
    let src_dir = manifest_dir.join("src");
    let seed_dir = manifest_dir.join("seeds");

    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed={}/prefer.toml", OPS_ROOT);
    println!("cargo:rerun-if-changed={}/tip_bind.accept", OPS_ROOT);
    println!("cargo:rerun-if-changed={}/trust_policy.toml", OPS_ROOT);
    for name in GUARDED {
        println!("cargo:rerun-if-changed=src/{}.rs", name);
    }

    if durable_committed() {
        return;
    }

    // Surface preference still in force: rematerialize each guarded evaluator
    // source from the surface baseline, discarding source-level repairs.
    for name in GUARDED {
        let seed = seed_dir.join(format!("{}.rs.seed", name));
        let dst = src_dir.join(format!("{}.rs", name));
        let Ok(seed_body) = fs::read_to_string(&seed) else {
            continue;
        };
        let current = fs::read_to_string(&dst).unwrap_or_default();
        if current != seed_body {
            let _ = fs::write(&dst, seed_body);
        }
    }
}
