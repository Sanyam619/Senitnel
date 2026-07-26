#!/bin/bash
set -euo pipefail

# Site-standard realm drop-in (later lexical file wins the fold).
cat >/etc/krb5.conf.d/90-local.conf <<'EOF'
realm=LAB.EXAMPLE.ORG
tip_policy=equality_inclusive
bind_order=lexical
EOF

# Durable prefer.accept matching the sealed tip id.
cat >/var/lib/ipa/ops/prefer.accept <<'EOF'
tip=tip_g7
EOF

cat >/app/ops/tag_r.sh <<'EOF'
#!/bin/bash
tag_r() {
  set -euo pipefail

  ROOT="${IPA_ROOT:-/var/lib/ipa}"
  FLOOR_D="$ROOT/floors"
  HOSTS="${HOSTS:-/etc/ipa/hosts.list}"
  STATE="$ROOT/state"
  JOURNAL="$ROOT/ops/enroll_journal.jsonl"
  TARGET=$(tr -d '[:space:]' <"$STATE/gen.target")

  mkdir -p "$STATE"

  python3 - "$JOURNAL" "$STATE" "$TARGET" "$HOSTS" "$FLOOR_D" <<'PY'
import json
import sys
from pathlib import Path

journal, state, target_s, hosts, floor_d = sys.argv[1:]
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
        tips[name] = {"fpr": str(meta.get("fpr", "")), "gen": int(meta.get("gen", 0))}

(state / "tip_id").write_text(tip_id + "\n")

for ln in Path(hosts).read_text().splitlines():
    ln = ln.strip()
    if not ln or ln.startswith("#"):
        continue
    name = ln.split("\t")[0]
    meta = tips.get(name, {"fpr": "", "gen": 0})
    gen = int(meta["gen"])
    fpr = meta["fpr"]
    (state / f"tip_{name}.gen").write_text(f"{gen}\n")
    (state / f"tip_{name}.fpr").write_text(f"{fpr}\n")
    (state / f"pub_{name}.gen").write_text(f"{gen}\n")
    (state / f"pub_{name}.fpr").write_text(f"{fpr}\n")
    floor_p = floor_d / f"{name}.floor"
    floor = int(floor_p.read_text().strip()) if floor_p.exists() else 0
    elig = 1 if gen >= floor else 0
    (state / f"elig_{name}").write_text(f"{elig}\n")

(state / "gen.live").write_text(f"{target}\n")
PY
}
tag_r
EOF
chmod +x /app/ops/tag_r.sh

cat >/app/ridge/fold_c.sh <<'EOF'
#!/bin/bash
fold_c() {
  set -euo pipefail

  PREF_D="${PREF_D:-/etc/krb5.conf.d}"
  OUT="${EFF_POLICY:-/etc/ipa/effective.conf}"

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
fold_c
EOF
chmod +x /app/ridge/fold_c.sh

cat >/app/span/dom_k.sh <<'EOF'
#!/bin/bash
dom_k() {
  set -euo pipefail

  ROOT="${IPA_ROOT:-/var/lib/ipa}"
  DOM_D="${DOM_D:-/etc/sssd/conf.d}"
  STATE="$ROOT/state"
  CLOCK=$(tr -d '[:space:]' <"$STATE/clock.epoch")

  mkdir -p "$STATE"
  : >"$STATE/aborts.tsv"

  shopt -s nullglob
  for f in $(ls -1 "$DOM_D"/*.conf 2>/dev/null | sort); do
    [[ -f "$f" ]] || continue
    key=$(basename "$f" .conf)
    abort_until=0
    host="$key"
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ "$line" == abort_until=* ]] && abort_until="${line#abort_until=}"
      [[ "$line" == host=* ]] && host="${line#host=}"
    done <"$f"
    printf '%s\t%s\n' "$host" "$abort_until" >>"$STATE/aborts.tsv"
    if (( abort_until > CLOCK )); then
      printf '1\n' >"$STATE/abort_block_${host}"
    else
      printf '0\n' >"$STATE/abort_block_${host}"
    fi
  done
  shopt -u nullglob
}
dom_k
EOF
chmod +x /app/span/dom_k.sh

cat >/app/ops/bind_v.sh <<'EOF'
#!/bin/bash
bind_v() {
  set -euo pipefail

  SURFACE="${SURFACE_REALM:-/var/lib/ipa/ops/surface.realm}"
  SSSD="${SSSD_CONF:-/etc/sssd/sssd.conf}"
  RECEIPT="${PREFER_ACCEPT:-/var/lib/ipa/ops/prefer.accept}"
  STATE="${IPA_ROOT:-/var/lib/ipa}/state"
  SITE="${SITE_STD:-/app/config/site_standard.conf}"
  TIP_FILE="$STATE/tip_id"

  want=""
  [[ -f "$TIP_FILE" ]] && want=$(tr -d '[:space:]' <"$TIP_FILE")

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
    REALM=""
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      case "$line" in
        realm=*) REALM="${line#realm=}" ;;
      esac
    done <"$SITE"
  else
    REALM=$(tr -d '[:space:]' <"$SURFACE")
  fi

  if [[ -f "$SSSD" && -n "$REALM" ]]; then
    python3 - "$SSSD" "$REALM" <<'PY'
import pathlib, re, sys
path, realm = pathlib.Path(sys.argv[1]), sys.argv[2]
text = path.read_text()
text = re.sub(r"ipa_domain = \S+", f"ipa_domain = {realm}", text)
text = re.sub(r"krb5_realm = \S+", f"krb5_realm = {realm}", text)
path.write_text(text)
PY
  fi
}
bind_v
EOF
chmod +x /app/ops/bind_v.sh

cat >/app/deck/emit_x.sh <<'EOF'
#!/bin/bash
emit_x() {
  set -euo pipefail
  exec /app/bin/ipaseatd
}
emit_x
EOF
chmod +x /app/deck/emit_x.sh

/app/ops/run_ipa_seat.sh
/app/ops/run_ipa_seat.sh
