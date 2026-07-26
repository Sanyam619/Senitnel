use std::env;
use std::fs;
use std::path::PathBuf;

fn main() {
    let out = PathBuf::from(env::var("OUT_DIR").unwrap());
    let _ = bind_k(&out);
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-env-changed=CARGO_FEATURE_LANE_X");
    println!("cargo:rerun-if-env-changed=CARGO_FEATURE_LANE_Y");
}

/// Emits the lane bind constants consumed by the expand path.
fn bind_k(out: &PathBuf) -> std::io::Result<()> {
    let lane_x = env::var_os("CARGO_FEATURE_LANE_X").is_none();
    let lane_y = env::var_os("CARGO_FEATURE_LANE_Y").is_none();
    let body = format!(
        "pub const LANE_X_ON: bool = {};\npub const LANE_Y_ON: bool = {};\n",
        lane_x, lane_y
    );
    fs::write(out.join("lane_bind.rs"), body)
}
