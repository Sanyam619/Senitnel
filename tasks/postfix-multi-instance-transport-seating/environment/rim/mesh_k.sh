#!/bin/bash
set -euo pipefail
# mesh_k — transport fold + abort-fragment honor set
mesh_k() {
  local pf_x="${PF_ETC:-/etc/postfix}"
  local pf_y="${PF_VAR:-/var/lib/postfix}"
  mkdir -p "$pf_y/state"
  python3 - <<'PY'
import os
from pathlib import Path

var = Path(os.environ.get("PF_VAR", "/var/lib/postfix"))
prefer_map = var / "ops" / "maps" / "nexthop.prefer"
abort_pkg = var / "ops" / "abort.d" / "90-local.cf"

def parse_map(path: Path) -> list[tuple[str, str]]:
    rows = []
    if not path.exists():
        return rows
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        rows.append((parts[0], parts[1]))
    return rows

def abort_patterns(path: Path) -> set[str]:
    found: set[str] = set()
    if not path.exists():
        return found
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" in line.split(None, 1)[0]:
            # key=value master tokens are not transport patterns
            if "=" in line and not line[0].isalnum() and line[0] not in "._":
                continue
        if "=" in line and line.split("=", 1)[0] in {
            "mail_policy", "bind_order", "transport_maps"
        }:
            continue
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0] not in {
            "mail_policy", "bind_order", "transport_maps"
        }:
            # transport-looking line in abort package
            if parts[0][0] in "._" or "." in parts[0]:
                found.add(parts[0])
    return found

rows = parse_map(prefer_map)
aborts = abort_patterns(abort_pkg)
fold_lines = []
honor_lines = []
for pattern, nexthop in rows:
    honored = pattern not in aborts
    fold_lines.append(f"{pattern}\t{nexthop}")
    honor_lines.append(f"{pattern}={'1' if honored else '0'}")

(var / "state" / "transport.fold").write_text(
    "\n".join(fold_lines) + ("\n" if fold_lines else "")
)
(var / "state" / "honor.set").write_text(
    "".join(f"{ln}\n" for ln in honor_lines)
)
(var / "state" / "abort.patterns").write_text(
    "".join(f"{p}\n" for p in sorted(aborts))
)
PY
}
mesh_k
