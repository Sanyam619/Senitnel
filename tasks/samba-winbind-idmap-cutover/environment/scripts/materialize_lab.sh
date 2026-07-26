#!/bin/bash
set -euo pipefail

SEED="${1:-/app/samba-seed}"
ETC="${SAMBA_ETC:-/etc/samba}"
VAR="${SAMBA_VAR:-/var/lib/samba}"

mkdir -p "$ETC/smb.conf.d" "$ETC/pref.d" "$VAR/meta" "$VAR/journal" \
  "$VAR/ops/abort.d" "$VAR/origins" "$VAR/attach" "$VAR/volumes" /output /var/run/samba

cp -f "$SEED/smb.conf" "$ETC/smb.conf"
cp -f "$SEED/smb.conf.d/"*.conf "$ETC/smb.conf.d/"
cp -f "$SEED/pref.d/"*.conf "$ETC/pref.d/" 2>/dev/null || true
cp -f "$SEED/idmap.roster" "$ETC/idmap.roster"
cp -f "$SEED/desk.seal" "$ETC/desk.seal"
cp -f "$SEED/deskd.env" "$ETC/deskd.env"
cp -f "$SEED/meta/backends.crash.toml" "$VAR/meta/backends.crash.toml"
cp -f "$SEED/meta/backends.crash.toml" "$VAR/meta/backends.toml"
cp -f "$SEED/meta/gen.target" "$VAR/meta/gen.target"
cp -f "$SEED/ops/abort.d/"*.conf "$VAR/ops/abort.d/" 2>/dev/null || true

# JSONL beside opaque streams (pack_opaque writes tips.bin / journal.bin).
cat >"$VAR/journal/tips.jsonl" <<'EOF'
{"kn":"hash","lo":90000,"hi":99999,"rk":99,"gen":17,"tag":""}
{"kn":"rid","lo":30000,"hi":39999,"rk":8,"gen":17,"tag":""}
{"kn":"autorid","lo":10000,"hi":19999,"rk":7,"gen":17,"tag":""}
EOF
cat >"$VAR/ops/journal.jsonl" <<'EOF'
{"tag":"abort","mode":"rollback","gen":17,"hold":"lab-tmp"}
{"tag":"cutover","mode":"seal","gen":99,"hold":"bait-hold"}
EOF

python3 /app/scripts/pack_opaque.py "$VAR"

cat >"$VAR/journal/legacy.prefer" <<'EOF'
kn=rid
lo=30000
hi=39999
rk=20
EOF

cp -f "$VAR/journal/legacy.prefer" "$ETC/smb.conf.d/40-legacy.conf"
while read -r nm sid lo hi uid || [[ -n "${nm:-}" ]]; do
  [[ -z "${nm:-}" || "$nm" == \#* ]] && continue
  mkdir -p "$VAR/origins/$nm/sealed" "$VAR/origins/$nm/decoy" \
    "$VAR/volumes/$nm/host" "$VAR/volumes/$nm/sealed"
  printf '%s %s %s\n' "$sid" "$uid" "$uid" >"$VAR/origins/$nm/sealed/map.bin"
  bait=$((90000 + ${uid: -2}))
  printf '%s %s %s\n' "$sid" "$bait" "$bait" >"$VAR/origins/$nm/decoy/map.bin"
  cp -f "$VAR/origins/$nm/sealed/map.bin" "$VAR/volumes/$nm/sealed/payload.bin"
done <"$ETC/idmap.roster"

echo "0" >"$VAR/journal/stale.gen"
rm -f "$VAR/meta/cut.arm" "$VAR/meta/active.kn" "$VAR/meta/cutover.ok" \
  "$VAR/meta/gen.live" "$VAR/meta/pref.armed" "$VAR/meta/attach.intent" \
  "$VAR/meta/hold.token" "$VAR/meta/tip.ok"
rm -rf "$VAR/attach"
mkdir -p "$VAR/attach"
