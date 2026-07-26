#!/bin/bash
set -euo pipefail

cd /app

python3 <<'PYEOF'
from pathlib import Path

# ── Site 1: q3/Cargo.toml feature propagation ──
# facet_b and facet_c must forward features to n7 so its gated code compiles.
q3_cargo = Path("q3/Cargo.toml")
ct = q3_cargo.read_text()
ct = ct.replace(
    'facet_b = ["dep:n7"]',
    'facet_b = ["dep:n7", "n7/facet_b"]',
)
ct = ct.replace(
    'facet_c = ["dep:n7"]',
    'facet_c = ["dep:n7", "n7/facet_c"]',
)
q3_cargo.write_text(ct)
print("site1: q3/Cargo.toml feature forwarding fixed")

# ── Site 2: q3/build.rs tag map ──
# knit_map_a must emit v2 (not v1) for facet_a, plus NEXUS_2 tag,
# and NEXUS_1C tag for facet_c with the nx_lane_c cfg.
build = Path("q3/build.rs")
text = build.read_text()
start = text.index("fn knit_map_a")
end = text.index("\n}", start) + 2
replacement = (
    'fn knit_map_a(a: &str, b: &str, c: &str) -> String {\n'
    '    let facet_a = a == "1";\n'
    '    let facet_b = b == "1";\n'
    '    let facet_c = c == "1";\n'
    '\n'
    '    let mut out = String::new();\n'
    '    out.push_str("tag:NEXUS_1\\n");\n'
    '    if facet_a {\n'
    '        out.push_str("cfg:nx_tag=\\"v2\\"\\n");\n'
    '        out.push_str("tag:NEXUS_2\\n");\n'
    '    }\n'
    '    if facet_b {\n'
    '        out.push_str("tag:NEXUS_1B\\n");\n'
    '        out.push_str("cfg:nx_lane_b\\n");\n'
    '    }\n'
    '    if facet_c {\n'
    '        out.push_str("tag:NEXUS_1C\\n");\n'
    '        out.push_str("cfg:nx_lane_c\\n");\n'
    '    }\n'
    '    out\n'
    '}'
)
build.write_text(text[:start] + replacement + text[end:])
print("site2: q3/build.rs knit_map_a fixed")

# ── Site 3: q3/src/slot.rs cfg gate polarity ──
# facet_b exports must compile when facet_b IS enabled, not when it is NOT.
slot = Path("q3/src/slot.rs")
stext = slot.read_text()
stext = stext.replace(
    "    if !b {\n        mask |= 0x4;\n    }",
    "    if b {\n        mask |= 0x4;\n    }",
    1,
)
slot.write_text(stext)
print("site3: q3/src/slot.rs gate polarity fixed")

# ── Site 4: q5/build.rs version tag namespace ──
# cascade must use CASCADE_* tags, not NEXUS_*, and must emit cx_tag="c1"
# for the facet_c ABI version tag export.
q5_build = Path("q5/build.rs")
q5bt = q5_build.read_text()
start5 = q5bt.index("fn knit_cascade_map")
end5 = q5bt.index("\n}", start5) + 2
q5_replacement = (
    'fn knit_cascade_map(c: &str) -> String {\n'
    '    let facet_c = c == "1";\n'
    '\n'
    '    let mut out = String::new();\n'
    '    out.push_str("tag:CASCADE_1\\n");\n'
    '    if facet_c {\n'
    '        out.push_str("cfg:cx_tag=\\"c1\\"\\n");\n'
    '        out.push_str("tag:CASCADE_1C\\n");\n'
    '        out.push_str("cfg:cx_lane_c\\n");\n'
    '    }\n'
    '    out\n'
    '}'
)
q5_build.write_text(q5bt[:start5] + q5_replacement + q5bt[end5:])
print("site4: q5/build.rs CASCADE tags and cx_tag fixed")

# ── Site 5: q5/src/exports.rs symbol namespace ──
# cascade must use cx_ prefix exclusively; remove the stray nx_trunk_open.
q5_exp = Path("q5/src/exports.rs")
q5et = q5_exp.read_text()
lines = []
skip = False
for line in q5et.splitlines():
    if 'fn nx_trunk_open' in line:
        skip = True
        # also remove preceding #[no_mangle]
        if lines and lines[-1].strip() == '#[no_mangle]':
            lines.pop()
        continue
    if skip:
        if line.strip() == '}':
            skip = False
            continue
        continue
    lines.append(line)
q5_exp.write_text('\n'.join(lines) + '\n')
print("site5: q5/src/exports.rs nx_trunk_open removed")

# ── Site 6: q5/Cargo.toml feature propagation ──
# facet_c pulls in n7 crate but must also forward n7/facet_c so
# n7::facet_c_ready() returns the real token instead of the fallback 0.
q5_cargo = Path("q5/Cargo.toml")
q5ct = q5_cargo.read_text()
q5ct = q5ct.replace(
    'facet_c = ["dep:n7"]',
    'facet_c = ["dep:n7", "n7/facet_c"]',
)
q5_cargo.write_text(q5ct)
print("site6: q5/Cargo.toml feature forwarding fixed")

# ── Site 7: k9/src/meta.rs dual-library metadata ──
# meta_emit must use the requested soname/tags instead of hardcoding legacy values.
meta = Path("k9/src/meta.rs")
meta.write_text("""use std::fs;
use std::io;
use std::path::Path;

/// Writes pkg-config and soname metadata consumed by host builds and abi_probe.
pub fn write_meta_c(a: &str, b: &str, c: &str) -> io::Result<()> {
    let out_dir = Path::new(a);
    let lib_dir = out_dir.join("lib");
    fs::create_dir_all(&lib_dir)?;

    let soname = if b.trim().is_empty() {
        "libnuclide.so.2".to_string()
    } else {
        b.trim().to_string()
    };
    let tags = if c.trim().is_empty() {
        vec![
            "NEXUS_1".to_string(),
            "NEXUS_2".to_string(),
            "NEXUS_1B".to_string(),
        ]
    } else {
        c.split(',')
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .collect::<Vec<_>>()
    };

    let legacy = lib_dir.join("libnuclide_legacy.so");
    if legacy.exists() {
        fs::remove_file(&legacy)?;
    }

    let lib_name = if soname.contains("cascade") {
        "cascade"
    } else {
        "nuclide"
    };

    let pc = format!(
        "prefix=/app\\n\\
         libdir=${{prefix}}/pkg/lib\\n\\
         includedir=${{prefix}}/pkg/include\\n\\
         \\n\\
         Name: {lib_name}\\n\\
         Description: {lib_name} plugin ABI\\n\\
         Version: 2.0.0\\n\\
         Libs: -L${{libdir}} -l{lib_name}\\n\\
         Cflags: -I${{includedir}}\\n"
    );
    fs::write(out_dir.join("nuclide.pc"), pc)?;
    fs::write(out_dir.join("soname.txt"), format!("{soname}\\n"))?;
    let mut versions = String::new();
    for tag in &tags {
        versions.push_str(tag);
        versions.push('\\n');
    }
    fs::write(out_dir.join("symbol_versions.txt"), versions)?;
    Ok(())
}
""")
print("site7: k9/src/meta.rs dual-library metadata fixed")
PYEOF

rm -rf /app/target /app/pkg/lib
rm -f /app/pkg/nuclide.pc /app/pkg/soname.txt /app/pkg/symbol_versions.txt
mkdir -p /output /app/pkg
/app/bin/abi_probe

python3 <<'PYEOF'
import json
from pathlib import Path
report = json.loads(Path("/output/abi-matrix.json").read_text())
for cid, cell in sorted(report["cells"].items()):
    assert cell["status"] == "ok", (cid, cell)
assert report["nuclide_soname"] == "libnuclide.so.2"
print("oracle matrix green:", sorted(report["cells"]))
PYEOF
