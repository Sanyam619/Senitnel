use std::env;
use std::fs;
use std::path::{Path, PathBuf};

fn main() {
    let manifest = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap());
    let root = manifest.join("..");
    let out = PathBuf::from(env::var("OUT_DIR").unwrap());
    let profile = env::var("PROFILE").unwrap_or_else(|_| "debug".to_string());
    let _ = fold_hdr(&out);
    let _ = emit_c(&profile, &root);
    println!("cargo:rustc-cdylib-link-arg=-Wl,-soname,libflux_cdylib.so.1");
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=../ops/nx/w7.toml");
    println!("cargo:rerun-if-changed=../config/z9.toml");
    println!("cargo:rerun-if-changed=../config/profiles/ship.toml");
    println!("cargo:rerun-if-changed=../config/profiles/field.toml");
}

/// Writes the tag-family header consumed by stamp_b.
fn fold_hdr(out: &Path) -> std::io::Result<()> {
    let body = concat!(
        "pub const FAMILY_CORE: &[u8] = b\"MG_CORE\\0\";\n",
        "pub const FAMILY_LANE: &[u8] = b\"MG_LANE_Y\\0\";\n",
    );
    fs::write(out.join("tag_family.rs"), body)
}

/// Writes pkg-config text for the active profile into the install tree.
fn emit_c(profile: &str, root: &Path) -> std::io::Result<()> {
    let _ = profile;
    let pkg = root.join("pkg");
    fs::create_dir_all(pkg.join("lib"))?;
    let templates = root.join("pkg/templates");
    let mono = fs::read_to_string(templates.join("legacy_mono.pc.in"))?;
    let text = mono
        .replace("@PREFIX@", "/app")
        .replace("@LIBDIR@", "/app/pkg/lib/debug")
        .replace("@VERSION@", "0.3.0");
    fs::write(pkg.join("flux_mono.pc"), text)?;
    Ok(())
}
