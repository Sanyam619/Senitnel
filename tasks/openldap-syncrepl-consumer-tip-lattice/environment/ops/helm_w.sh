#!/bin/bash
helm_w() {
  set -euo pipefail

  SURFACE="${SURFACE_URI:-/var/lib/ldap/ops/surface.uri}"
  SLAPD="${SLAPD_DB:-/etc/ldap/slapd.d/cn=config/olcDatabase=mdb.ldif}"
  URI=$(tr -d '[:space:]' <"$SURFACE")

  python3 - "$SLAPD" "$URI" <<'PY'
import pathlib, re, sys
path, uri = pathlib.Path(sys.argv[1]), sys.argv[2]
if not path.is_file():
    raise SystemExit(0)
text = path.read_text()
text2 = re.sub(r"provider=\S+", f"provider={uri}", text)
path.write_text(text2)
PY
}
helm_w
