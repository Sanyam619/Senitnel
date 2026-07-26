#!/bin/bash
set -euo pipefail
# vane_t
vane_t() {
  local pd_x="${PD_ETC:-/etc/powerdns}"
  local pd_y="${PD_VAR:-/var/lib/powerdns}"
  mkdir -p "$pd_y/state"
  python3 - <<'PY'
import os
from pathlib import Path
etc = Path(os.environ.get("PD_ETC", "/etc/powerdns"))
var = Path(os.environ.get("PD_VAR", "/var/lib/powerdns"))
opts = {}
aborts = set()
lines_out = []
for path in sorted((etc / "pdns.d").glob("*.conf")):
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if k.startswith("opt."):
            opts[k] = v
            lines_out.append(f"{k}={v}")
        elif k == "abort-zone":
            if v:
                aborts.add(v)
            lines_out.append(f"abort-zone={v}")
        else:
            lines_out.append(f"{k}={v}")
(var / "state" / "effective.conf").write_text("\n".join(lines_out) + ("\n" if lines_out else ""))
(var / "state" / "abort.set").write_text("".join(f"{n}\n" for n in sorted(aborts)))
opt_lines = [f"{k.split('.',1)[1]}={v}" for k, v in sorted(opts.items())]
(var / "state" / "opts.fold").write_text("".join(f"{ln}\n" for ln in opt_lines))
PY
}
vane_t
