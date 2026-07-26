#!/bin/bash
set -euo pipefail

cd /app

python3 <<'PYEOF'
from pathlib import Path

# ── knit_xv_a: call is (profile, lane); musl/target needs static-PIE stamps ──
Path("h4/mk/knit_xv_a.mk").write_text(
    "# Emits host CC/LD flag fragments from profile probes during the C host build.\n"
    "# Usage: $(eval $(call knit_xv_a,<profile>,<lane>))\n"
    "\n"
    "define knit_xv_a\n"
    "XV_CC := gcc\n"
    "XV_TLS := initial-exec\n"
    "XV_PIE :=\n"
    "XV_EXTRA :=\n"
    "XV_RPATH :=\n"
    "XV_ABI := host\n"
    "ifeq ($(2),musl)\n"
    "ifeq ($(1),target)\n"
    "XV_CC := musl-gcc\n"
    "XV_TLS := global-dynamic\n"
    "XV_PIE := -fPIE -pie\n"
    "XV_EXTRA := -Wl,-z,relro\n"
    "XV_RPATH :=\n"
    "XV_ABI := target\n"
    "else\n"
    "XV_CC := musl-gcc\n"
    "XV_TLS := global-dynamic\n"
    "XV_PIE := -fPIE -pie\n"
    "XV_EXTRA :=\n"
    "XV_RPATH :=\n"
    "XV_ABI := musl\n"
    "endif\n"
    "else\n"
    "ifeq ($(1),builder)\n"
    "XV_CC := gcc\n"
    "XV_TLS := initial-exec\n"
    "XV_PIE :=\n"
    "XV_EXTRA := -Wl,-z,relro\n"
    "XV_RPATH := /usr/lib\n"
    "XV_ABI := builder\n"
    "else\n"
    "XV_CC := gcc\n"
    "XV_TLS := initial-exec\n"
    "XV_PIE :=\n"
    "XV_EXTRA := -Wl,-z,relro\n"
    "XV_RPATH :=\n"
    "XV_ABI := legacy\n"
    "endif\n"
    "endif\n"
    "endef\n"
)
print("knit_xv_a: lane/profile branches aligned")

# ── cargo cfg: drop legacy packing invert (runtime + seed) ──
Path(".cargo").mkdir(parents=True, exist_ok=True)
cleared = (
    "# Workspace cargo config after cutover.\n"
    "# Do not force packing cfgs here; packing follows crate features.\n"
)
Path(".cargo/config.toml").write_text(cleared)
Path("config/rust/cargo_config.toml").write_text(cleared)
print("cargo: legacy packing cfg cleared")

# ── p7 feature forward ──
p7 = Path("p7/Cargo.toml")
p7.write_text(
    "[package]\n"
    'name = "p7"\n'
    'version = "0.1.0"\n'
    'edition = "2021"\n'
    "\n"
    "[lib]\n"
    'crate-type = ["cdylib", "rlib"]\n'
    'name = "p7slot"\n'
    "\n"
    "[features]\n"
    'default = ["trunk"]\n'
    "trunk = []\n"
    'wide_frame = ["k2/wide_layout"]\n'
    "\n"
    "[dependencies]\n"
    'k2 = { path = "../k2" }\n'
)
print("p7: wide_frame forwards wide_layout")

# ── slot packing: cutover polarity (no legacy invert / mask clear) ──
slot_path = Path("p7/src/slot.rs")
slot = slot_path.read_text()
start = slot.index("pub fn fold_slot_b")
end = slot.index("\nfn wide_enabled", start)
replacement = (
    "pub fn fold_slot_b(a: bool, b: bool) -> u32 {\n"
    "    let mut mask = 0x1u32;\n"
    "    let wide = if cfg!(xv_legacy_pack) {\n"
    "        !a\n"
    "    } else {\n"
    "        a\n"
    "    };\n"
    "    let trunk = b;\n"
    "    if wide {\n"
    "        mask |= 0x2;\n"
    "    }\n"
    "    if trunk {\n"
    "        mask |= 0x4;\n"
    "    }\n"
    "    if !trunk && wide {\n"
    "        mask |= 0x8;\n"
    "    }\n"
    "    mask\n"
    "}\n"
)
slot_path.write_text(slot[:start] + replacement + slot[end:])
print("slot: cutover packing polarity restored")

# ── target profile [cgo] must match locked cgo_policy ──
Path("config/profiles/target.toml").write_text(
    "# Musl target profile for static-PIE cutover cells.\n"
    'lane = "musl"\n'
    "\n"
    "[host]\n"
    'cc = "musl-gcc"\n'
    'tls_model = "global-dynamic"\n'
    "pie = true\n"
    "\n"
    "[cgo]\n"
    'cc = "musl-gcc"\n'
    'include = "/app/include"\n'
    "pic = true\n"
)
print("target.toml: cgo section aligned")

# ── emit_xv must read [cgo], not [host] ──
emit = Path("g3/emit_xv.go")
emit_text = emit.read_text()
if 'readNamedSection(profPath, "host")' in emit_text:
    emit.write_text(
        emit_text.replace(
            'readNamedSection(profPath, "host")',
            'readNamedSection(profPath, "cgo")',
        )
    )
else:
    raise SystemExit("emit_xv.go missing expected host-section read")
print("emit_xv: profile section reader selected")
PYEOF

/app/tools/lattice_probe
