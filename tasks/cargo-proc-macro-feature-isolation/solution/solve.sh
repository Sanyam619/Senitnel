#!/bin/bash
set -euo pipefail

cd /app

cat > m4/build.rs <<'EOF'
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
    let lane_x = env::var_os("CARGO_FEATURE_LANE_X").is_some();
    let lane_y = env::var_os("CARGO_FEATURE_LANE_Y").is_some();
    let body = format!(
        "pub const LANE_X_ON: bool = {};\npub const LANE_Y_ON: bool = {};\n",
        lane_x, lane_y
    );
    fs::write(out.join("lane_bind.rs"), body)
}
EOF
echo "siteA: bind_k rewritten"

python3 - <<'PY'
from pathlib import Path
r1 = Path("r1/Cargo.toml")
rt = r1.read_text()
rt = rt.replace('lane_x = ["m4/lane_x"]', 'lane_x = ["m4/lane_x", "p2/lane_x"]')
rt = rt.replace('lane_y = ["m4/lane_y"]', 'lane_y = ["m4/lane_y", "p2/lane_y"]')
r1.write_text(rt)
d7 = Path("d7/Cargo.toml")
dt = d7.read_text()
dt = dt.replace('lane_y = ["dep:p2"]', 'lane_y = ["dep:p2", "p2/lane_y"]')
d7.write_text(dt)
print("siteB/C: feature forward lines patched")
PY

cat > d7/build.rs <<'EOF'
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

    let soname = "libflux_cdylib.so.1";
    println!("cargo:rustc-cdylib-link-arg=-Wl,-soname,{}", soname);
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-env-changed=PROFILE");
    println!("cargo:rerun-if-changed=../ops/nx/w7.toml");
    println!("cargo:rerun-if-changed=../config/z9.toml");
    println!("cargo:rerun-if-changed=../config/profiles/ship.toml");
    println!("cargo:rerun-if-changed=../config/profiles/field.toml");
}

/// Writes the tag-family header consumed by stamp_b.
fn fold_hdr(out: &Path) -> std::io::Result<()> {
    let body = concat!(
        "pub const FAMILY_CORE: &[u8] = b\"DY_CORE\\0\";\n",
        "pub const FAMILY_LANE: &[u8] = b\"DY_LANE_Y\\0\";\n",
    );
    fs::write(out.join("tag_family.rs"), body)
}

fn skim_q(root: &Path, cargo_profile: &str) -> String {
    let alias_path = root.join("config/z9.toml");
    let requested = if cargo_profile == "release" {
        "ship"
    } else {
        "field"
    };
    let mapped = map_v(&alias_path, requested).unwrap_or_else(|| requested.to_string());
    let prof_path = root.join(format!("config/profiles/{mapped}.toml"));
    tip_n(&prof_path).unwrap_or_else(|| {
        if cargo_profile == "release" {
            "release".into()
        } else {
            "debug".into()
        }
    })
}

fn map_v(path: &Path, key: &str) -> Option<String> {
    let text = fs::read_to_string(path).ok()?;
    for line in text.lines() {
        let line = line.trim();
        if line.starts_with('#') || !line.contains('=') {
            continue;
        }
        let (k, v) = line.split_once('=')?;
        if k.trim() == key {
            return Some(v.trim().trim_matches('"').to_string());
        }
    }
    None
}

fn tip_n(path: &Path) -> Option<String> {
    let text = fs::read_to_string(path).ok()?;
    for line in text.lines() {
        let line = line.trim();
        if let Some(rest) = line.strip_prefix("libdir_suffix") {
            let v = rest.trim().trim_start_matches('=').trim().trim_matches('"');
            if !v.is_empty() {
                return Some(v.to_string());
            }
        }
    }
    None
}

fn gate_w(root: &Path) -> bool {
    let path = root.join("ops/nx/w7.toml");
    let Ok(text) = fs::read_to_string(path) else {
        return false;
    };
    text.lines().any(|l| {
        let l = l.trim();
        l == "mode = \"sealed\"" || l == "mode=\"sealed\""
    })
}

fn hold_m(root: &Path) -> bool {
    let path = root.join("ops/nx/w7.toml");
    let Ok(text) = fs::read_to_string(path) else {
        return true;
    };
    text.lines().any(|l| {
        let l = l.trim();
        l == "prefer = \"archive\"" || l == "prefer=\"archive\""
    })
}

/// Writes pkg-config text for the active profile into the install tree.
fn emit_c(profile: &str, root: &Path) -> std::io::Result<()> {
    let pkg = root.join("pkg");
    fs::create_dir_all(pkg.join("lib/debug"))?;
    fs::create_dir_all(pkg.join("lib/release"))?;
    let templates = root.join("pkg/templates");

    if !gate_w(root) {
        let sheet = root.join("ops/nx/w7.toml");
        if sheet.exists() {
            let mut text = fs::read_to_string(&sheet)?;
            if !text.contains("prefer = \"archive\"") {
                text.push_str("\nprefer = \"archive\"\n");
                fs::write(&sheet, text)?;
            }
        }
    }

    if hold_m(root) || !gate_w(root) {
        let mono = fs::read_to_string(templates.join("legacy_mono.pc.in"))?;
        let text = mono
            .replace("@PREFIX@", "/app")
            .replace("@LIBDIR@", "/app/pkg/lib/debug")
            .replace("@VERSION@", "0.3.0");
        fs::write(pkg.join("flux_mono.pc"), text)?;
        return Ok(());
    }

    let suffix = skim_q(root, profile);
    let pairs = [
        ("flux_macro", "flux_macro.pc.in"),
        ("flux_cdylib", "flux_cdylib.pc.in"),
    ];
    let profiles = ["debug", "release"];

    for (name, tmpl) in pairs {
        let raw = fs::read_to_string(templates.join(tmpl))?;
        for prof in profiles {
            let libdir = format!("/app/pkg/lib/{prof}");
            let text = raw
                .replace("@PREFIX@", "/app")
                .replace("@LIBDIR@", &libdir)
                .replace("@VERSION@", "0.3.0");
            fs::write(pkg.join(format!("{name}.{prof}.pc")), &text)?;
        }
        let libdir = format!("/app/pkg/lib/{suffix}");
        let text = raw
            .replace("@PREFIX@", "/app")
            .replace("@LIBDIR@", &libdir)
            .replace("@VERSION@", "0.3.0");
        fs::write(pkg.join(format!("{name}.pc")), text)?;
        let text = raw
            .replace("@PREFIX@", "/app")
            .replace("@LIBDIR@", &libdir)
            .replace("@VERSION@", "0.3.0");
        fs::write(pkg.join(format!("{name}.{suffix}.pc")), text)?;
    }

    let mono = pkg.join("flux_mono.pc");
    if mono.exists() {
        fs::remove_file(mono)?;
    }
    Ok(())
}
EOF
echo "siteD: d7/build.rs rewritten"

cat > config/z9.toml <<'EOF'
# Opaque alias table for profile name mapping.

ship = "ship"
field = "field"
EOF
echo "siteE: z9 alias rewritten"

cat > ops/nx/w7.toml <<'EOF'
# Opaque emission policy sheet.

mode = "sealed"
prefer = "live"
EOF
echo "siteF: w7 policy rewritten"

rm -rf /app/target
rm -f /app/pkg/flux_mono.pc
mkdir -p /output /app/pkg
/app/bin/abi_probe

python3 <<'PYEOF'
import json
from pathlib import Path

report = json.loads(Path("/output/abi-matrix.json").read_text())
assert report["schema_tag"] == "abi-matrix-v1"
cells = {c["id"]: c for c in report["cells"]}
for cid, cell in cells.items():
    assert cell["status"] == "ok", (cid, cell.get("error"))
eps = cells["epsilon"]
macro = set(eps["tag_families"]["macro_surface"])
cdylib = set(eps["tag_families"]["cdylib"])
assert not (macro & cdylib), (macro, cdylib)
assert "MG_LANE_X" in macro
assert "DY_CORE" in cdylib
assert not Path("/app/pkg/flux_mono.pc").exists()
rel = Path("/app/pkg/flux_cdylib.release.pc")
assert rel.is_file() and "/app/pkg/lib/release" in rel.read_text()
print("oracle matrix green:", sorted(cells))
PYEOF
