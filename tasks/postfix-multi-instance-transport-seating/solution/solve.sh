#!/bin/bash
set -euo pipefail

cd /app

# One-time desk settle for the solve pass. Helpers must honor prefer.toml as-is
# on later reseats and must never rewrite the preference mode.
cat >/var/lib/postfix/ops/prefer.toml <<'EOF'
mode = "durable"
tag_path = "authority"
EOF

# Ensure durable authority map exists for restore after surface poison.
if [[ -f /var/lib/postfix/ops/maps/nexthop.prefer && ! -f /var/lib/postfix/ops/maps/nexthop.durable ]]; then
  cp -f /var/lib/postfix/ops/maps/nexthop.prefer /var/lib/postfix/ops/maps/nexthop.durable
fi
if [[ -f /app/data/seed/maps/nexthop.prefer ]]; then
  cp -f /app/data/seed/maps/nexthop.prefer /var/lib/postfix/ops/maps/nexthop.durable
fi

cat >/app/ops/helm_r.sh <<'EOF'
#!/bin/bash
set -euo pipefail
helm_r() {
  local pf_x="${PF_ETC:-/etc/postfix}"
  local pf_y="${PF_VAR:-/var/lib/postfix}"
  local abort_pkg="$pf_y/ops/abort.d/90-local.cf"
  local live_dropin="$pf_x/master.d/90-local.cf"
  local cutover_receipt="$pf_y/state/cutover.ok"
  local target_gen gen_ok mode_ok need_abort
  target_gen=$(tr -d ' \t\r\n' <"$pf_y/state/gen.target")
  need_abort=1
  if [[ -f "$cutover_receipt" ]]; then
    gen_ok=$(grep -E '^gen=' "$cutover_receipt" | head -n1 | cut -d= -f2- || true)
    mode_ok=$(grep -E '^mode=' "$cutover_receipt" | head -n1 | cut -d= -f2- || true)
    if [[ "$gen_ok" == "$target_gen" && "$mode_ok" == "seal" ]]; then
      need_abort=0
    fi
  fi
  if [[ "$need_abort" -eq 1 ]]; then
    if [[ -f "$abort_pkg" ]]; then
      cp -f "$abort_pkg" "$live_dropin"
    fi
  fi
}
helm_r
EOF
chmod +x /app/ops/helm_r.sh

cat >/app/ops/axle_n.sh <<'EOF'
#!/bin/bash
set -euo pipefail
axle_n() {
  local pf_x="${PF_ETC:-/etc/postfix}"
  local pf_y="${PF_VAR:-/var/lib/postfix}"
  local sheet_z="/app/config/site_standard.conf"
  local target_gen mode="live"
  mkdir -p "$pf_y/state" "$pf_x/master.d" "$pf_y/ops/maps"
  target_gen=$(tr -d ' \t\r\n' <"$pf_y/state/gen.target")
  if [[ -f "$pf_y/ops/prefer.toml" ]]; then
    mode=$(grep -E '^mode[[:space:]]*=' "$pf_y/ops/prefer.toml" | head -1 \
      | sed 's/.*=[[:space:]]*//;s/"//g;s/[[:space:]]*$//' | tr -d ' ')
  fi
  # Honor current preference: restore working map only on durable/authority.
  case "$mode" in
    durable|authority)
      if [[ -f "$pf_y/ops/maps/nexthop.durable" ]]; then
        cp -f "$pf_y/ops/maps/nexthop.durable" "$pf_y/ops/maps/nexthop.prefer"
      fi
      ;;
  esac
  python3 - <<'PY'
import json, os
from pathlib import Path
var = Path(os.environ.get("PF_VAR", "/var/lib/postfix"))
target = (var / "state" / "gen.target").read_text().strip()
prefer = var / "ops" / "prefer.jsonl"
batches = []
seal_ok = False
for line in prefer.read_text().splitlines():
    if not line.strip():
        continue
    row = json.loads(line)
    if row.get("tag") == "seal" and str(row.get("gen")) == target:
        seal_ok = True
    if row.get("tag") == "batch":
        batches.append(row)
if not seal_ok:
    raise SystemExit("axle_n: missing seal for gen.target")
chosen = None
for batch in batches:
    if str(batch.get("gen")) != target:
        continue
    if batch.get("sealed") is True and batch.get("complete") is True:
        chosen = batch
if chosen is None:
    raise SystemExit("axle_n: no sealed complete batch for gen.target")
tip_dir = var / "state"
for row in chosen.get("rows", []):
    name = row["name"]
    (tip_dir / f"tip_{name}.gen").write_text(f"{target}\n")
    (tip_dir / f"tip_{name}.queue").write_text(f'{row["queue_dir"]}\n')
(tip_dir / "gen.live").write_text(f"{target}\n")
(tip_dir / "tip.batch").write_text(json.dumps(chosen) + "\n")
(var / "ops" / "tip_bind.accept").write_text(f"gen={target}\ntip=prefer\n")
PY
  cp -f "$sheet_z" "$pf_x/master.d/90-local.cf"
  {
    echo "gen=${target_gen}"
    echo "mode=seal"
  } >"$pf_y/state/cutover.ok"
}
axle_n
EOF
chmod +x /app/ops/axle_n.sh

cat >/app/wire/sock_v.sh <<'EOF'
#!/bin/bash
set -euo pipefail
sock_v() {
  local pf_x="${PF_ETC:-/etc/postfix}"
  local pf_y="${PF_VAR:-/var/lib/postfix}"
  mkdir -p "$pf_y/state"
  python3 - <<'PY'
import os
from pathlib import Path
etc = Path(os.environ.get("PF_ETC", "/etc/postfix"))
var = Path(os.environ.get("PF_VAR", "/var/lib/postfix"))
roster = [ln.strip() for ln in (etc / "roster.list").read_text().splitlines() if ln.strip()]
admitted = {ln.strip() for ln in (var / "state" / "admit.set").read_text().splitlines() if ln.strip()}
prefer_map = "hash:/var/lib/postfix/ops/maps/nexthop.prefer"
active = []
for name in roster:
    queue_dir = (var / "state" / f"tip_{name}.queue").read_text().strip()
    gen = int((var / "state" / f"tip_{name}.gen").read_text().strip())
    floor = int((var / "floors" / f"{name}.floor").read_text().strip())
    inst = Path(f"/etc/postfix-{name}")
    inst.mkdir(parents=True, exist_ok=True)
    (inst / "main.cf").write_text(
        f"queue_directory = {queue_dir}\n"
        f"transport_maps = {prefer_map}\n"
        f"myhostname = {name}.seat.local\n"
    )
    ok = name in admitted and gen >= floor
    if ok:
        active.append(name)
(var / "state" / "active.set").write_text("".join(f"{n}\n" for n in active))
(var / "state" / "socket.applied").write_text("1\n")
PY
}
sock_v
EOF
chmod +x /app/wire/sock_v.sh

cat >/app/wire/knit_q.sh <<'EOF'
#!/bin/bash
# knit_q — surface rematerialize gated on preference + tip bind
set -euo pipefail
knit_q() {
  local pf_x="${PF_ETC:-/etc/postfix}"
  local pf_y="${PF_VAR:-/var/lib/postfix}"
  local surf="$pf_y/surface"
  local pref="$pf_y/ops/prefer.toml"
  local bind="$pf_y/ops/tip_bind.accept"
  local mode="live"
  local target_gen gen_ok need_surface=1
  mkdir -p "$pf_y/state" "$pf_y/ops/maps"
  target_gen=$(tr -d ' \t\r\n' <"$pf_y/state/gen.target")
  if [[ -f "$pref" ]]; then
    mode=$(grep -E '^mode[[:space:]]*=' "$pref" | head -1 \
      | sed 's/.*=[[:space:]]*//;s/"//g;s/[[:space:]]*$//' | tr -d ' ')
  fi
  gen_ok=""
  if [[ -f "$bind" ]]; then
    gen_ok=$(grep -E '^gen=' "$bind" | head -n1 | cut -d= -f2- || true)
  fi
  case "$mode" in
    durable|authority)
      if [[ "$gen_ok" == "$target_gen" ]]; then
        need_surface=0
      fi
      ;;
  esac
  if [[ "$need_surface" -eq 1 ]]; then
    if [[ -d "$surf/tips" ]]; then
      cp -a "$surf/tips/." "$pf_y/state/"
    fi
    # Overwrite working prefer map only — never the durable authority copy.
    if [[ -f "$surf/maps/nexthop.prefer" ]]; then
      cp -f "$surf/maps/nexthop.prefer" "$pf_y/ops/maps/nexthop.prefer"
    fi
    if [[ -d "$surf/main.d" ]]; then
      local name
      while IFS= read -r name || [[ -n "${name:-}" ]]; do
        [[ -z "$name" ]] && continue
        if [[ -f "$surf/main.d/$name/main.cf" ]]; then
          mkdir -p "/etc/postfix-${name}"
          cp -f "$surf/main.d/$name/main.cf" "/etc/postfix-${name}/main.cf"
        fi
      done <"$pf_x/roster.list"
    fi
  fi
  date +%s >"$pf_y/state/probe.stamp"
  printf '%s\n' "$mode" >"$pf_y/state/mode.active"
}
knit_q
EOF
chmod +x /app/wire/knit_q.sh

/app/ops/run_postfix_seat.sh
/app/ops/run_postfix_seat.sh
