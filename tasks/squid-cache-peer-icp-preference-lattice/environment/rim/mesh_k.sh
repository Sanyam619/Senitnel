#!/bin/bash
set -euo pipefail
# mesh_k
mesh_k() {
  local sq_x="${SQ_ETC:-/etc/squid}"
  local sq_y="${SQ_VAR:-/var/lib/squid}"
  mkdir -p "$sq_y/state"
  python3 - <<'PY'
import os
from pathlib import Path
etc = Path(os.environ.get("SQ_ETC", "/etc/squid"))
var = Path(os.environ.get("SQ_VAR", "/var/lib/squid"))
acl = {}
aborts = set()
lines_out = []
for path in sorted((etc / "conf.d").glob("*.cfg")):
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if k.startswith("acl."):
            acl[k] = v
            lines_out.append(f"{k}={v}")
        elif k == "abort":
            if v:
                aborts.add(v)
            lines_out.append(f"abort={v}")
        else:
            lines_out.append(f"{k}={v}")
(var / "state" / "effective.conf").write_text("\n".join(lines_out) + ("\n" if lines_out else ""))
(var / "state" / "abort.set").write_text("".join(f"{n}\n" for n in sorted(aborts)))
acl_lines = [f"{k.split('.',1)[1]}={v}" for k, v in sorted(acl.items())]
(var / "state" / "acl.fold").write_text("".join(f"{ln}\n" for ln in acl_lines))
PY
}
mesh_k
