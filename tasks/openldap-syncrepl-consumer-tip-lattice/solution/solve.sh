#!/bin/bash
set -euo pipefail

# Site-standard prefer drop-in (abort package / surface residue stays forensic).
cat >/etc/ldap/prefer.d/90-local.conf <<'EOF'
providerURI=ldap://provider-a.lab:389
tip_policy=equality_inclusive
bind_order=lexical
EOF

# Durable prefer.accept matching sealed tip id.
cat >/var/lib/ldap/ops/prefer.accept <<'EOF'
tip=tip_g7
EOF

cat >/app/rim/mesh_x.sh <<'EOF'
#!/bin/bash
mesh_x() {
  set -euo pipefail

  PREF_D="${PREF_D:-/etc/ldap/prefer.d}"
  OUT="${EFF_POLICY:-/etc/ldap/effective.conf}"

  mkdir -p "$(dirname "$OUT")"
  declare -A kv=()
  shopt -s nullglob
  for f in $(ls -1 "$PREF_D"/*.conf 2>/dev/null | sort); do
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ -z "$line" ]] && continue
      [[ "$line" != *=* ]] && continue
      k="${line%%=*}"
      v="${line#*=}"
      kv["$k"]="$v"
    done <"$f"
  done
  shopt -u nullglob

  {
    for k in $(printf '%s\n' "${!kv[@]}" | sort); do
      printf '%s=%s\n' "$k" "${kv[$k]}"
    done
  } >"$OUT"
}
mesh_x
EOF
chmod +x /app/rim/mesh_x.sh

cat >/app/ops/axle_y.sh <<'EOF'
#!/bin/bash
axle_y() {
  set -euo pipefail

  ROOT="${LDAP_ROOT:-/var/lib/ldap}"
  FLOOR_D="$ROOT/floors"
  ROSTER="${ROSTER:-/etc/ldap/roster.list}"
  STATE="$ROOT/state"
  JOURNAL="$ROOT/ops/csn_journal.jsonl"
  TARGET=$(tr -d '[:space:]' <"$STATE/gen.target")

  mkdir -p "$STATE"

  python3 - "$JOURNAL" "$STATE" "$TARGET" "$ROSTER" "$FLOOR_D" <<'PY'
import json
import sys
from pathlib import Path

journal, state, target_s, roster, floor_d = sys.argv[1:]
state = Path(state)
floor_d = Path(floor_d)
target = int(target_s)

sealed = None
for line in Path(journal).read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    row = json.loads(line)
    if row.get("kind") == "seal" and int(row.get("gen", -1)) == target and row.get("mode") == "seal":
        sealed = row

tips = {}
tip_id = ""
if sealed:
    tip_id = str(sealed.get("tip_id", ""))
    raw = sealed.get("tips", {}) or {}
    for name, meta in raw.items():
        tips[name] = {
            "csn": str(meta.get("csn", "")),
            "gen": int(meta.get("gen", 0)),
        }

(state / "tip_id").write_text(tip_id + "\n")

for ln in Path(roster).read_text().splitlines():
    ln = ln.strip()
    if not ln or ln.startswith("#"):
        continue
    name = ln.split("\t")[0]
    meta = tips.get(name, {"csn": "", "gen": 0})
    tip = int(meta["gen"])
    csn = meta["csn"]
    (state / f"tip_{name}.gen").write_text(f"{tip}\n")
    (state / f"tip_{name}.csn").write_text(f"{csn}\n")
    (state / f"pub_{name}.gen").write_text(f"{tip}\n")
    (state / f"pub_{name}.csn").write_text(f"{csn}\n")
    floor_p = floor_d / f"{name}.floor"
    floor = int(floor_p.read_text().strip()) if floor_p.exists() else 0
    elig = 1 if tip >= floor else 0
    (state / f"elig_{name}").write_text(f"{elig}\n")

(state / "gen.live").write_text(f"{target}\n")
PY
}
axle_y
EOF
chmod +x /app/ops/axle_y.sh

cat >/app/bag/skim_z.sh <<'EOF'
#!/bin/bash
skim_z() {
  set -euo pipefail

  ROOT="${LDAP_ROOT:-/var/lib/ldap}"
  HOLD_D="$ROOT/holds"
  STATE="$ROOT/state"
  CLOCK=$(tr -d '[:space:]' <"$STATE/clock.epoch")

  mkdir -p "$STATE"
  : >"$STATE/holds.tsv"

  shopt -s nullglob
  for f in $(ls -1 "$HOLD_D"/*.hold 2>/dev/null | sort); do
    [[ -f "$f" ]] || continue
    key=$(basename "$f" .hold)
    until_epoch=0
    suffix="dc=${key},dc=lab"
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ "$line" == until_epoch=* ]] && until_epoch="${line#until_epoch=}"
      [[ "$line" == suffix=* ]] && suffix="${line#suffix=}"
    done <"$f"
    printf '%s\t%s\t%s\n' "$key" "$suffix" "$until_epoch" >>"$STATE/holds.tsv"
    if (( until_epoch > CLOCK )); then
      printf '1\n' >"$STATE/hold_block_${key}"
    else
      printf '0\n' >"$STATE/hold_block_${key}"
    fi
  done
  shopt -u nullglob
}
skim_z
EOF
chmod +x /app/bag/skim_z.sh

cat >/app/ops/helm_w.sh <<'EOF'
#!/bin/bash
helm_w() {
  set -euo pipefail

  SURFACE="${SURFACE_URI:-/var/lib/ldap/ops/surface.uri}"
  SLAPD="${SLAPD_DB:-/etc/ldap/slapd.d/cn=config/olcDatabase=mdb.ldif}"
  RECEIPT="${PREFER_ACCEPT:-/var/lib/ldap/ops/prefer.accept}"
  STATE="${LDAP_ROOT:-/var/lib/ldap}/state"
  SITE="${SITE_STD:-/app/config/site_standard.conf}"
  TIP_FILE="$STATE/tip_id"

  want=""
  if [[ -f "$TIP_FILE" ]]; then
    want=$(tr -d '[:space:]' <"$TIP_FILE")
  fi

  got=""
  if [[ -f "$RECEIPT" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      case "$line" in
        tip=*) got="${line#tip=}" ;;
      esac
    done <"$RECEIPT"
  fi

  if [[ -n "$want" && "$got" == "$want" ]]; then
    URI=""
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      case "$line" in
        providerURI=*) URI="${line#providerURI=}" ;;
      esac
    done <"$SITE"
  else
    URI=$(tr -d '[:space:]' <"$SURFACE")
  fi

  if [[ -f "$SLAPD" && -n "${URI}" ]]; then
    python3 - "$SLAPD" "$URI" <<'PY'
import pathlib, re, sys
path, uri = pathlib.Path(sys.argv[1]), sys.argv[2]
text = path.read_text()
path.write_text(re.sub(r"provider=\S+", f"provider={uri}", text))
PY
  fi
}
helm_w
EOF
chmod +x /app/ops/helm_w.sh

cat >/app/deck/emit_q.sh <<'EOF'
#!/bin/bash
emit_q() {
  set -euo pipefail
  exec /app/bin/seatctl
}
emit_q
EOF
chmod +x /app/deck/emit_q.sh

/app/ops/run_ldap_seat.sh
/app/ops/run_ldap_seat.sh
