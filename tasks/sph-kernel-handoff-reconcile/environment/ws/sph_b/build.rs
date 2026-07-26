// Rematerialize pressure-kick materials from the active handoff
// preference before compiling. Missing preference paths (image build)
// leave the checked-in sources untouched.

use std::path::{Path, PathBuf};

fn parse_root(text: &str) -> Option<String> {
    for raw in text.lines() {
        let line = raw.split('#').next().unwrap_or("").trim();
        if let Some(rest) = line.strip_prefix("material_root") {
            let val = rest
                .trim()
                .trim_start_matches('=')
                .trim()
                .trim_matches('"');
            if !val.is_empty() {
                return Some(val.to_string());
            }
        }
    }
    None
}

fn prefer_durable() -> bool {
    let accept = Path::new("/app/data/state/root.accept");
    let trial = Path::new("/app/data/state/trial_pref.toml");
    if !accept.is_file() || trial.is_file() {
        return false;
    }
    std::fs::read_to_string(accept)
        .ok()
        .and_then(|t| parse_root(&t))
        .map(|r| r == "durable")
        .unwrap_or(false)
}

fn main() {
    let manifest = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
    let dest = manifest.join("src/momentum.rs");
    let durable = Path::new("/app/data/materials/durable/momentum.rs");
    let surface = Path::new("/app/data/materials/surface/momentum.rs");

    println!("cargo:rerun-if-changed=/app/data/state/root.accept");
    println!("cargo:rerun-if-changed=/app/data/state/trial_pref.toml");
    println!("cargo:rerun-if-changed=/app/data/materials/durable/momentum.rs");
    println!("cargo:rerun-if-changed=/app/data/materials/surface/momentum.rs");

    let src = if prefer_durable() { durable } else { surface };
    if src.is_file() {
        let _ = std::fs::copy(src, &dest);
    }
}
