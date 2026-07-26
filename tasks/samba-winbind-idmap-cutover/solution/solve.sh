#!/bin/bash
set -euo pipefail

cd /app

for b in idmapctl tipfold cutarm; do
  if [[ -x /usr/lib/samba/bin/$b ]]; then
    cp -f "/usr/lib/samba/bin/$b" "/app/bin/$b"
    chmod 755 "/app/bin/$b"
  fi
done

cp -f /app/samba-seed/pref.d/*.conf /etc/samba/pref.d/
cp -f /app/samba-seed/meta/backends.crash.toml /var/lib/samba/meta/backends.crash.toml
cp -f /app/samba-seed/meta/gen.target /var/lib/samba/meta/gen.target
cp -f /app/samba-seed/ops/abort.d/*.conf /var/lib/samba/ops/abort.d/
cp -f /app/samba-seed/idmap.roster /etc/samba/idmap.roster
cp -f /app/samba-seed/desk.seal /etc/samba/desk.seal
python3 /app/scripts/pack_opaque.py /var/lib/samba

cat >/app/rim/fold_p.sh <<'EOF'
#!/bin/bash
set -euo pipefail
PREF_D="${PREF_D:-/etc/samba/pref.d}"
META="${SAMBA_VAR:-/var/lib/samba}/meta"
SEAL="${DESK_SEAL:-/etc/samba/desk.seal}"
SEED_PREF="/app/samba-seed/pref.d"
mkdir -p "$META" "$PREF_D"
if [[ -d "$SEED_PREF" ]]; then
  cp -f "$SEED_PREF"/*.conf "$PREF_D/" 2>/dev/null || true
fi
mode="unset"
if [[ -d "$PREF_D" ]]; then
  while IFS= read -r f; do
    [[ -f "$f" ]] || continue
    if grep -qE '^mode=' "$f" 2>/dev/null; then
      mode=$(grep -E '^mode=' "$f" | tail -n1 | cut -d= -f2-)
    fi
  done < <(find "$PREF_D" -type f -name '*.conf' | sort)
fi
echo "$mode" >"$META/pref.mode"
if [[ "$mode" != "equality-inclusive" ]]; then
  echo "fold_p: need equality-inclusive, got $mode" >&2
  exit 1
fi
tr -d ' \t\r\n' <"$SEAL" >"$META/pref.armed"
EOF
chmod +x /app/rim/fold_p.sh

cat >/app/ops/axle_j.sh <<'EOF'
#!/bin/bash
set -euo pipefail
exec /app/bin/cutarm
EOF
chmod +x /app/ops/axle_j.sh

cat >/app/ops/fold_a.sh <<'EOF'
#!/bin/bash
set -euo pipefail
ETC="${SAMBA_ETC:-/etc/samba}"
OPS="${SAMBA_VAR:-/var/lib/samba}/ops"
META="${SAMBA_VAR:-/var/lib/samba}/meta"
abort_pkg="$OPS/abort.d/90-local.conf"
live_dropin="$ETC/smb.conf.d/90-decoy.conf"
cutover_receipt="$META/cutover.ok"
target_gen=$(tr -d ' \t\r\n' <"$META/gen.target")
hold_now=$(tr -d ' \t\r\n' <"$META/hold.token" 2>/dev/null || true)

need_abort=1
if [[ -f "$cutover_receipt" ]]; then
  gen_ok=$(grep -E '^gen=' "$cutover_receipt" | head -n1 | cut -d= -f2- || true)
  hold_ok=$(grep -E '^hold=' "$cutover_receipt" | head -n1 | cut -d= -f2- || true)
  mode_ok=$(grep -E '^mode=' "$cutover_receipt" | head -n1 | cut -d= -f2- || true)
  if [[ "$gen_ok" == "$target_gen" && "$hold_ok" == "$hold_now" && "$mode_ok" == "seal" ]]; then
    need_abort=0
  fi
fi

if [[ "$need_abort" -eq 1 ]]; then
  if [[ -f "$abort_pkg" ]]; then
    cp -f "$abort_pkg" "$live_dropin"
  fi
  rm -f "$cutover_receipt"
fi
EOF
chmod +x /app/ops/fold_a.sh

cat >/app/deck/leg_w.sh <<'EOF'
#!/bin/bash
set -euo pipefail
ETC="${SAMBA_ETC:-/etc/samba}"
SEED_LEGACY="/app/samba-seed/smb.conf.d/40-legacy.conf"
LIVE="$ETC/smb.conf.d/40-legacy.conf"
HAMMER="${SAMBA_VAR:-/var/lib/samba}/journal/legacy.prefer"
[[ -f "$SEED_LEGACY" ]] || { echo "leg_w: missing seed legacy" >&2; exit 1; }
cp -f "$SEED_LEGACY" "$LIVE"
if [[ -f "$HAMMER" ]] && cmp -s "$LIVE" "$HAMMER"; then
  echo "leg_w: live legacy must differ from hammer" >&2
  exit 1
fi
EOF
chmod +x /app/deck/leg_w.sh

cat >/app/dock/link_v.sh <<'EOF'
#!/bin/bash
set -euo pipefail
ROOT="${SAMBA_VAR:-/var/lib/samba}"
ROSTER="${IDMAP_ROSTER:-/etc/samba/idmap.roster}"
ENV_FILE="${SAMBA_DESKD_ENV:-/etc/samba/deskd.env}"
ATTACH="$ROOT/attach"
ORIGINS="$ROOT/origins"
mkdir -p "$ATTACH"
hold=""
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  hold="${HOLD_TOKEN:-}"
fi
[[ -n "$hold" ]] || { echo "link_v: missing HOLD_TOKEN" >&2; exit 1; }
[[ "${PAYLOAD_LINEAGE:-}" == "sealed" ]] || { echo "link_v: lineage not sealed" >&2; exit 1; }

rm -rf "$ATTACH"/*/
while read -r nm sid lo hi uid || [[ -n "${nm:-}" ]]; do
  [[ -z "${nm:-}" || "$nm" == \#* ]] && continue
  sealed="$ORIGINS/$nm/sealed/map.bin"
  dst="$ATTACH/$nm.bin"
  rm -f "$dst"
  ln "$sealed" "$dst"
  printf '%s\n' "$hold" >"$ATTACH/.hold.$nm"
done <"$ROSTER"
EOF
chmod +x /app/dock/link_v.sh

cat >/app/ops/skim_r.sh <<'EOF'
#!/bin/bash
set -euo pipefail
ETC="${SAMBA_ETC:-/etc/samba}"
VAR="${SAMBA_VAR:-/var/lib/samba}"
SEAL="${DESK_SEAL:-/etc/samba/desk.seal}"
ARM="$VAR/meta/cut.arm"
OK="$VAR/meta/cutover.ok"
SEAL_VAL="$(tr -d ' \t\r\n' <"$SEAL" || true)"
LEGACY_PREF="$VAR/journal/legacy.prefer"
ABORT_D="$VAR/ops/abort.d"
LEGACY_LIVE="$ETC/smb.conf.d/40-legacy.conf"

if [[ ! -f "$ARM" ]] || [[ "$(tr -d ' \t\r\n' <"$ARM")" != "$SEAL_VAL" ]] || [[ ! -f "$OK" ]]; then
  if [[ -f "$LEGACY_PREF" ]]; then
    cp -f "$LEGACY_PREF" "$LEGACY_LIVE"
  fi
  if [[ -d "$ABORT_D" ]]; then
    for f in "$ABORT_D"/*.conf; do
      [[ -f "$f" ]] || continue
      cp -f "$f" "$ETC/smb.conf.d/$(basename "$f")"
    done
  fi
  echo "0" >"$VAR/journal/stale.gen"
  rm -f "$VAR/meta/pref.armed" "$VAR/meta/gen.live"
fi
EOF
chmod +x /app/ops/skim_r.sh

/app/ops/run_idmapseat.sh
/app/ops/run_idmapseat.sh
/app/ops/run_reload.sh

test -f /output/idmap-cutover.json
test -f /var/lib/samba/meta/cutover.ok
! cmp -s /etc/samba/smb.conf.d/40-legacy.conf /var/lib/samba/journal/legacy.prefer
python3 - <<'PY'
import os
from pathlib import Path
for line in Path("/etc/samba/idmap.roster").read_text().splitlines():
    line=line.strip()
    if not line or line.startswith("#"):
        continue
    nm=line.split()[0]
    assert os.stat(f"/var/lib/samba/attach/{nm}.bin").st_ino == os.stat(
        f"/var/lib/samba/origins/{nm}/sealed/map.bin"
    ).st_ino
assert Path("/var/lib/samba/meta/backends.toml").read_text() != Path(
    "/var/lib/samba/meta/backends.crash.toml"
).read_text()
assert "kn=hash" not in Path("/var/lib/samba/meta/backends.toml").read_text()
assert Path("/etc/samba/deskd.env").read_text().count("PAYLOAD_LINEAGE=sealed") == 1
print("ok")
PY
