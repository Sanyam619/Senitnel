use std::env;
use std::fs;
use std::path::PathBuf;

fn main() {
    println!("cargo:rustc-check-cfg=cfg(cx_tag, values(\"c1\",\"c2\"))");
    println!("cargo:rustc-check-cfg=cfg(cx_lane_c)");

    let manifest_dir = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap());
    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());

    let facet_c = env::var("CARGO_FEATURE_FACET_C").is_ok();
    let c = if facet_c { "1" } else { "0" };

    let map_body = knit_cascade_map(c);
    let map_path = out_dir.join("cascade.map");
    fs::write(&map_path, &map_body).expect("write cascade map");

    for line in map_body.lines() {
        if let Some(rest) = line.strip_prefix("cfg:") {
            println!("cargo:rustc-cfg={}", rest.trim());
        }
    }

    let soname = "libcascade.so.1";
    println!("cargo:rustc-cdylib-link-arg=-Wl,-soname,{}", soname);
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-env-changed=CARGO_FEATURE_FACET_C");

    let notes = manifest_dir.join("../link/abi_notes.toml");
    println!("cargo:rerun-if-changed={}", notes.display());
}

fn knit_cascade_map(c: &str) -> String {
    let facet_c = c == "1";

    let mut out = String::new();
    out.push_str("tag:NEXUS_1\n");
    if facet_c {
        out.push_str("tag:NEXUS_1C\n");
        out.push_str("cfg:cx_lane_c\n");
    }
    out
}
