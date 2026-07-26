use std::env;
use std::fs;
use std::path::PathBuf;

fn main() {
    println!("cargo:rustc-check-cfg=cfg(nx_tag, values(\"v1\",\"v2\"))");
    println!("cargo:rustc-check-cfg=cfg(nx_lane_b)");
    println!("cargo:rustc-check-cfg=cfg(nx_lane_c)");

    let manifest_dir = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap());
    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());

    let facet_a = env::var("CARGO_FEATURE_FACET_A").is_ok();
    let facet_b = env::var("CARGO_FEATURE_FACET_B").is_ok();
    let facet_c = env::var("CARGO_FEATURE_FACET_C").is_ok();
    let a = if facet_a { "1" } else { "0" };
    let b = if facet_b { "1" } else { "0" };
    let c = if facet_c { "1" } else { "0" };

    let map_body = knit_map_a(a, b, c);
    let map_path = out_dir.join("nuclide.map");
    fs::write(&map_path, &map_body).expect("write map notes");

    for line in map_body.lines() {
        if let Some(rest) = line.strip_prefix("cfg:") {
            println!("cargo:rustc-cfg={}", rest.trim());
        }
    }

    let soname = "libnuclide.so.2";
    println!("cargo:rustc-cdylib-link-arg=-Wl,-soname,{}", soname);
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-env-changed=CARGO_FEATURE_FACET_A");
    println!("cargo:rerun-if-env-changed=CARGO_FEATURE_FACET_B");
    println!("cargo:rerun-if-env-changed=CARGO_FEATURE_FACET_C");

    let notes = manifest_dir.join("../link/abi_notes.toml");
    println!("cargo:rerun-if-changed={}", notes.display());
}

/// Compose linker/cfg map text from feature environment probes.
fn knit_map_a(a: &str, b: &str, c: &str) -> String {
    let facet_a = a == "1";
    let facet_b = b == "1";
    let facet_c = c == "1";

    let mut out = String::new();
    out.push_str("tag:NEXUS_1\n");
    if facet_a {
        out.push_str("cfg:nx_tag=\"v1\"\n");
        out.push_str("tag:NEXUS_1\n");
    }
    if facet_b {
        out.push_str("tag:NEXUS_1B\n");
        out.push_str("cfg:nx_lane_b\n");
    }
    if facet_c {
        out.push_str("tag:NEXUS_1\n");
    }
    out
}
