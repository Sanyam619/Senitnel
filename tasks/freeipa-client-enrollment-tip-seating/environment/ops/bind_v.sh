#!/bin/bash
bind_v() {
  set -euo pipefail

  SURFACE="${SURFACE_REALM:-/var/lib/ipa/ops/surface.realm}"
  SSSD="${SSSD_CONF:-/etc/sssd/sssd.conf}"
  REALM=$(tr -d '[:space:]' <"$SURFACE")

  python3 - "$SSSD" "$REALM" <<'PY'
import pathlib, re, sys
path, realm = pathlib.Path(sys.argv[1]), sys.argv[2]
if not path.is_file():
    raise SystemExit(0)
text = path.read_text()
text = re.sub(r"ipa_domain = \S+", f"ipa_domain = {realm}", text)
text = re.sub(r"krb5_realm = \S+", f"krb5_realm = {realm}", text)
path.write_text(text)
PY
}
bind_v
