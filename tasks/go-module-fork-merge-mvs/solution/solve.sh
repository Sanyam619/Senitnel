#!/bin/bash
set -euo pipefail

repo_root=/app/src
out_path=/output/build-matrix.json
mkdir -p /output

test -x /app/bin/matrixci
test -f /app/docs/security-pin-policy.md

cat > "$repo_root/go.mod" <<'GOMOD'
module internal.example/rootapp

go 1.22

toolchain go1.23

require (
	example.org/logstream v1.4.3
	example.org/httpmux v0.5.2
	example.org/toolchain v0.9.5
	example.org/serde v2.0.0+incompatible
	example.org/mathkit v0.1.0
	internal.example/platform v0.1.0
)

replace example.org/httpmux => example.org/httpmux-fork v0.5.4

exclude example.org/toolchain v0.9.0
exclude example.org/logstream v1.4.2
GOMOD

cat > "$repo_root/svc/go.mod" <<'SUBMOD'
module internal.example/rootapp/submodule

go 1.22

require (
	example.org/logstream v1.4.3
	example.org/httpmux v0.5.2
	example.org/toolchain v0.9.5
	example.org/serde v2.0.0+incompatible
	internal.example/logging v0.2.0
)

replace example.org/httpmux => example.org/httpmux-fork v0.5.4
SUBMOD

cat > "$repo_root/bnd/modules.txt" <<'VENDOR'
# example.org/httpmux v0.5.2 => example.org/httpmux-fork v0.5.4
## explicit; go 1.23
example.org/httpmux
example.org/httpmux/muxutil
example.org/httpmux/internal/router
# example.org/logstream v1.4.3
## explicit; go 1.20
example.org/logstream
example.org/logstream/emitter
example.org/logstream/format
# example.org/mathkit v0.1.0
## explicit; go 1.20
example.org/mathkit
example.org/mathkit/statistics
example.org/mathkit/geometry
# example.org/serde v2.0.0+incompatible
## explicit; go 1.20
example.org/serde
example.org/serde/codec
example.org/serde/wire
# example.org/toolchain v0.9.5
## explicit; go 1.20
example.org/toolchain
example.org/toolchain/probe
example.org/toolchain/hasher
VENDOR

cat > "$repo_root/tools.go" <<'TOOLS'
//go:build tools

package rootapp

import (
	_ "example.org/toolchain/probe"
)
TOOLS

/app/bin/matrixci report --out "$out_path"

python3 <<'PY'
import json, sys
from pathlib import Path

data = json.loads(Path("/output/build-matrix.json").read_text())
required_keys = {
    "toolchains", "cve_floor", "retract",
    "replace_conflicts", "vendor_incompatible_drift",
    "required_excludes", "prohibited_replaces", "retained_forks", "proxy_digest",
}
missing = required_keys - set(data)
if missing:
    print("missing keys:", missing, file=sys.stderr)
    sys.exit(1)

for prof in ("go1.22", "go1.23"):
    for mode in ("mod", "vendor"):
        cell = data["toolchains"][prof][mode]
        if cell["status"] != "ok":
            print(f"{prof}/{mode}: {cell['status']} :: {cell.get('diagnostics')}", file=sys.stderr)
            sys.exit(2)

if not data["cve_floor"]["respected"]:
    print("floor/cap not respected:", data["cve_floor"], file=sys.stderr)
    sys.exit(3)
if not data["retract"]["avoided"]:
    print("retract not avoided:", data["retract"], file=sys.stderr)
    sys.exit(4)
if data["replace_conflicts"]:
    print("replace conflicts:", data["replace_conflicts"], file=sys.stderr)
    sys.exit(5)
if data["vendor_incompatible_drift"]:
    print("vendor drift:", data["vendor_incompatible_drift"], file=sys.stderr)
    sys.exit(6)
if not data["required_excludes"]["respected"]:
    print("required excludes missing:", data["required_excludes"], file=sys.stderr)
    sys.exit(7)
if not data["prohibited_replaces"]["respected"]:
    print("prohibited replaces present:", data["prohibited_replaces"], file=sys.stderr)
    sys.exit(8)
if not data["retained_forks"]["respected"]:
    print("retained forks missing:", data["retained_forks"], file=sys.stderr)
    sys.exit(9)
print("matrix ok")
PY
