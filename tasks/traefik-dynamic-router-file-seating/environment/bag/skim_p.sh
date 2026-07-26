#!/bin/bash
set -euo pipefail
skim_p() {
  local trf_x="${TRF_ETC:-/etc/traefik}"
  local trf_y="${TRF_VAR:-/var/lib/traefik}"
  mkdir -p "$trf_y/ops/state"
  python3 - <<'PY'
from pathlib import Path
import os, re
etc = Path(os.environ.get("TRF_ETC", "/etc/traefik"))
var = Path(os.environ.get("TRF_VAR", "/var/lib/traefik"))
text = (etc / "dynamic" / "40-middlewares.yml").read_text()
names = []
mw_list = etc / "mw.list"
if mw_list.exists():
    names = [ln.strip() for ln in mw_list.read_text().splitlines() if ln.strip()]
out = var / "ops" / "state" / "mw.attach"
lines = []
for name in names:
    m = re.search(rf"{name}:\s*\n(?:.*\n)*?\s*attached:\s*(true|false)", text)
    attached = m.group(1) if m else "true"
    typ_m = re.search(rf"{name}:\s*\n\s*type:\s*(\S+)", text)
    typ = typ_m.group(1) if typ_m else name
    lines.append(f"{name}|{typ}|{attached}")
out.write_text("\n".join(lines) + ("\n" if lines else ""))
PY
}
skim_p
