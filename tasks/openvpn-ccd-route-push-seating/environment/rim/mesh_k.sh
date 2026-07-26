#!/bin/bash
set -euo pipefail
# mesh_k
mesh_k() {
  local ov_x="${OV_ETC:-/etc/openvpn}"
  local ov_y="${OV_VAR:-/var/lib/openvpn}"
  mkdir -p "$ov_y/state"
  python3 - <<'PY'
import os
import re
from pathlib import Path

etc = Path(os.environ.get("OV_ETC", "/etc/openvpn"))
var = Path(os.environ.get("OV_VAR", "/var/lib/openvpn"))
pool_kv = {}
aborts = set()
lines_out = []
for path in sorted((etc / "server" / "conf.d").glob("*.conf")):
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if k.startswith("pool."):
            pool_kv[k] = v
            lines_out.append(f"{k}={v}")
        elif k == "abort":
            if v:
                aborts.add(v)
            lines_out.append(f"abort={v}")
        else:
            lines_out.append(f"{k}={v}")
(var / "state" / "effective.conf").write_text("\n".join(lines_out) + ("\n" if lines_out else ""))
(var / "state" / "abort.set").write_text("".join(f"{n}\n" for n in sorted(aborts)))
fold_lines = [f"{k.split('.',1)[1]}={v}" for k, v in sorted(pool_kv.items())]
(var / "state" / "pool.fold").write_text("".join(f"{ln}\n" for ln in fold_lines))

def prefer_mode() -> str:
    pref = var / "ops" / "prefer.toml"
    if not pref.exists():
        return "live"
    m = re.search(r'^mode\s*=\s*"?([A-Za-z_]+)"?', pref.read_text(), re.M)
    return m.group(1) if m else "live"

pools = []
mode = prefer_mode()
durable_ok = mode in {"durable", "authority"}
for raw in (var / "ops" / "pools.toml").read_text().splitlines():
    line = raw.split("#", 1)[0].strip()
    if not line or "=" not in line:
        continue
    name, rest = line.split("=", 1)
    name = name.strip()
    cidr, mark = [p.strip() for p in rest.split(",", 1)]
    prefer_selected = mark == "prefer"
    active = prefer_selected and durable_ok and pool_kv.get(f"pool.{name}", "skip") == "match"
    if not durable_ok and mark == "decoy":
        active = True
    pools.append(f"{name}|{cidr}|{1 if active else 0}")
(var / "state" / "pools.active").write_text("".join(f"{p}\n" for p in pools))
PY
}
mesh_k
