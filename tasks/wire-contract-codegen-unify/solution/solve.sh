#!/bin/bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/cargo/bin:/app/bin:/opt/java/openjdk/bin:${PATH}"

mkdir -p /output

# Align Go lane dependency pin matrix to live plugin under yank policy.
cat > /app/gox/pins.toml <<'K9'
# go lane dependency pin matrix
lane = "go"
health_bin = "/app/bin/lanehealth"
fold_bin = "/app/bin/foldctl"
plugin_key = "pg-core@0.9.2"
mirror_plugin = "pg-core@0.9.1"
archive_plugin = "pg-core@0.9.0"
fallback_plugin = "pg-core@0.9.2"
mirror_prefer = false
honor_yanks = true
tag_owner = "live"
oneof_owner = "live"
gomod_plugin = "pg-core@0.9.2"
reject_mirror_preferred = true
allow_yanked_transitive = false
pin_epoch = 12
note = "compile-only surface for go tree"
K9

# Align Rust lane dependency pin matrix away from skim/archive owners.
cat > /app/rsx/pins.toml <<'M2'
# rust lane dependency pin matrix
lane = "rust"
health_bin = "/app/bin/lanehealth"
sieve_bin = "/app/bin/sievectl"
plugin_key = "pg-core@0.9.2"
skim_plugin = "pg-core@0.9.0"
archive_plugin = "pg-core@0.9.0"
fallback_plugin = "pg-core@0.9.2"
skim_prefer = false
json_owner = "live"
optional_owner = "live"
cargo_plugin = "pg-core@0.9.2"
reject_skim_archive = true
allow_yanked_transitive = false
pin_epoch = 12
note = "compile-only surface for rust tree"
M2

# Align Java lane dependency pin matrix for full digest and ok probes.
cat > /app/jvx/pins.toml <<'P7'
# java lane dependency pin matrix
lane = "java"
health_bin = "/app/bin/lanehealth"
java_main = "org.lab.p7.LaneMain"
plugin_key = "pg-core@0.9.2"
bom_plugin = "pg-core@0.9.1"
fallback_plugin = "pg-core@0.9.2"
bom_prefer = false
maven_plugin = "pg-core@0.9.2"
digest_mode = "full"
reject_slots_only_digest = true
allow_yanked_transitive = false
pin_epoch = 12
note = "compile-only surface for java tree"
P7

# Keep module metadata pins consistent with the live selection.
cat > /app/gox/go.mod <<'GOMOD'
module lab.local/gox

go 1.22

// codegen_plugin=pg-core@0.9.2
GOMOD

cat > /app/rsx/core/Cargo.toml <<'CARGO'
[package]
name = "core"
version = "0.1.0"
edition = "2021"

[lib]
path = "src/lib.rs"

[package.metadata.codegen]
plugin = "pg-core@0.9.2"
CARGO

python3 - <<'PY'
from pathlib import Path
pom = Path("/app/jvx/pom.xml")
text = pom.read_text()
text = text.replace(
    "<codegen.plugin.key>pg-core@0.9.1</codegen.plugin.key>",
    "<codegen.plugin.key>pg-core@0.9.2</codegen.plugin.key>",
)
pom.write_text(text)
PY

lanehealth all
/app/bin/xlink report --out /output/wire-unify.json
