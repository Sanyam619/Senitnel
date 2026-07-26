#!/bin/bash
# Oracle: bring the Redis Sentinel seating desk to the durable end-state.
set -euo pipefail

SV=/var/lib/redis
SD=/etc/redis/sentinel.d

cat >"$SD/90-local.conf" <<'EOF'
tip_policy=durable_authority
bind_order=lexical
abort=none
EOF

mkdir -p "$SV/ops/state"
target=$(tr -d '[:space:]' <"$SV/state/gen.target")
cat >"$SV/ops/state/apply.ok" <<EOF
gen=${target}
mode=seal
EOF

sed -i 's/^plane *= *"surface"/plane = "durable"/' "$SV/ops/prefer.toml"

cat >/app/ops/helm_r.sh <<'EOS'
#!/bin/bash
set -euo pipefail
helm_r() {
  local mx="${MONITOR_D:-/etc/redis/monitors.d}"
  local sd="${DROPIN_D:-/etc/redis/sentinel.d}"
  local sv="${REDIS_ROOT:-/var/lib/redis}"
  local plane aim rg rmode ok=0
  mkdir -p "$mx" "$sd" "$sv/ops/state"
  plane=$(sed -n 's/^plane *= *"\([a-z]*\)".*/\1/p' "$sv/ops/prefer.toml" | head -n1)
  aim=$(tr -d '[:space:]' <"$sv/state/gen.target")
  if [[ "$plane" == "durable" && -f "$sv/ops/state/apply.ok" ]]; then
    rg=$(sed -n 's/^gen=\([0-9]*\)$/\1/p' "$sv/ops/state/apply.ok" | head -n1)
    rmode=$(sed -n 's/^mode=\(.*\)$/\1/p' "$sv/ops/state/apply.ok" | head -n1)
    if [[ "$rg" == "$aim" && "$rmode" == "seal" ]]; then
      ok=1
    fi
  fi
  if [[ "$ok" -eq 1 ]]; then
    python3 - "$sv/ops/failover_journal.jsonl" "$aim" "$mx" <<'PY'
import json
import sys
from pathlib import Path

journal, aim_s, monitor_d = sys.argv[1:]
aim = int(aim_s)
row = {}
for line in Path(journal).read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    cand = json.loads(line)
    if (
        cand.get("kind") == "cutover"
        and int(cand.get("gen", -1)) == aim
        and cand.get("mode") == "seal"
    ):
        row = cand
target = Path(monitor_d)
target.mkdir(parents=True, exist_ok=True)
for name, tip in sorted(row.get("tips", {}).items()):
    addr = tip.get("addr", "")
    host = addr.split(":")[0] if addr else "0.0.0.0"
    (target / (name + ".conf")).write_text(
        "sentinel monitor %s %s 6379 2\n"
        "sentinel down-after-milliseconds %s 5000\n" % (name, host, name)
    )
PY
  else
    local row a b host
    while IFS= read -r row || [[ -n "${row:-}" ]]; do
      [[ -z "${row:-}" || "$row" =~ ^# ]] && continue
      a=$(sed -n 's/^\([a-z]*\)=.*/\1/p' <<<"$row")
      b=$(sed -n 's/^[a-z]*=\(.*\)/\1/p' <<<"$row")
      [[ -z "${a:-}" || -z "${b:-}" ]] && continue
      host="${b%%:*}"
      printf 'sentinel monitor %s %s 6379 2\nsentinel down-after-milliseconds %s 5000\n' \
        "$a" "$host" "$a" >"$mx/${a}.conf"
    done <"$sv/ops/surface.monitors"
    if [[ -f "$sv/ops/abort.d/90-local.conf" ]]; then
      cp -f "$sv/ops/abort.d/90-local.conf" "$sd/90-local.conf"
    fi
    rm -f "$sv/ops/state/apply.ok"
    cp -f "$sv/ops/surface.quorum" "$sv/state/quorum.sheet"
  fi
}
helm_r
EOS

cat >/app/ops/axle_n.sh <<'EOS'
#!/bin/bash
set -euo pipefail
axle_n() {
  local sv="${REDIS_ROOT:-/var/lib/redis}"
  local rl="${ROSTER:-/etc/redis/roster.list}"
  local aim
  aim=$(tr -d '[:space:]' <"$sv/state/gen.target")
  mkdir -p "$sv/state"
  python3 - "$sv/ops/failover_journal.jsonl" "$sv/state" "$aim" "$rl" "$sv/floors" <<'PY'
import json
import sys
from pathlib import Path

journal, state_s, aim_s, roster, floor_s = sys.argv[1:]
state = Path(state_s)
floor_d = Path(floor_s)
aim = int(aim_s)
row = {}
for line in Path(journal).read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    cand = json.loads(line)
    if (
        cand.get("kind") == "cutover"
        and int(cand.get("gen", -1)) == aim
        and cand.get("mode") == "seal"
    ):
        row = cand
tips = row.get("tips", {})
names = [
    ln.strip()
    for ln in Path(roster).read_text().splitlines()
    if ln.strip() and not ln.strip().startswith("#")
]
for name in names:
    tip = tips.get(name, {})
    addr = tip.get("addr", "")
    gen = int(tip.get("generation", 0))
    (state / ("tip_" + name + ".addr")).write_text(addr + "\n")
    (state / ("tip_" + name + ".gen")).write_text("%d\n" % gen)
    (state / ("pub_" + name + ".gen")).write_text("%d\n" % gen)
    fp = floor_d / (name + ".floor")
    bar = int(fp.read_text().strip()) if fp.exists() else 0
    (state / ("elig_" + name)).write_text("1\n" if gen >= bar and gen > 0 else "0\n")
(state / "gen.live").write_text("%d\n" % aim)
(state / "quorum.want").write_text("%d\n" % int(row.get("quorum", 0)))
online = list(row.get("sentinels_online", []))
(state / "quorum.online").write_text("%d\n" % len(online))
(state / "quorum.sheet").write_text(
    "quorum=%d\nonline=%s\n" % (int(row.get("quorum", 0)), ",".join(online))
)
PY
}
axle_n
EOS

cat >/app/bag/skim_p.sh <<'EOS'
#!/bin/bash
set -euo pipefail
skim_p() {
  local sv="${REDIS_ROOT:-/var/lib/redis}"
  local rl="${ROSTER:-/etc/redis/roster.list}"
  local plane want online_n name qfile
  mkdir -p "$sv/state"
  plane=$(sed -n 's/^plane *= *"\([a-z]*\)".*/\1/p' "$sv/ops/prefer.toml" | head -n1)
  if [[ "$plane" == "durable" && -f "$sv/state/quorum.sheet" ]]; then
    qfile="$sv/state/quorum.sheet"
  else
    qfile="$sv/ops/surface.quorum"
  fi
  want=$(sed -n 's/^quorum=\([0-9]*\).*/\1/p' "$qfile" | head -n1)
  online_n=$(sed -n 's/^online=\(.*\)/\1/p' "$qfile" | head -n1 | tr ',' '\n' | grep -c . || true)
  printf '%s\n' "$want" >"$sv/state/quorum.want"
  printf '%s\n' "$online_n" >"$sv/state/quorum.online"
  while IFS= read -r name || [[ -n "${name:-}" ]]; do
    [[ -z "${name:-}" || "$name" =~ ^# ]] && continue
    if [[ "$online_n" -ge "$want" && "$want" -gt 0 ]]; then
      printf '1\n' >"$sv/state/quorum_${name}"
    else
      printf '0\n' >"$sv/state/quorum_${name}"
    fi
  done <"$rl"
}
skim_p
EOS

cat >/app/bag/sock_v.sh <<'EOS'
#!/bin/bash
set -euo pipefail
sock_v() {
  local sv="${REDIS_ROOT:-/var/lib/redis}"
  local sheet="${REPLICA_SHEET:-/etc/redis/replica.list}"
  local out="$sv/state/replicas.tsv"
  mkdir -p "$sv/state"
  : >"$out"
  while IFS='|' read -r m addr reported lag || [[ -n "${m:-}" ]]; do
    [[ -z "${m:-}" || "$m" =~ ^# ]] && continue
    tip=$(tr -d '[:space:]' <"$sv/state/tip_${m}.addr" 2>/dev/null || true)
    if [[ "$reported" == "$tip" ]]; then
      printf '%s\t%s\t%s\t1\n' "$m" "$addr" "$lag" >>"$out"
    else
      printf '%s\t%s\t%s\t0\n' "$m" "$addr" "$lag" >>"$out"
    fi
  done <"$sheet"
}
sock_v
EOS

chmod 755 /app/ops/helm_r.sh /app/ops/axle_n.sh /app/bag/skim_p.sh /app/bag/sock_v.sh

/app/ops/run_sentinel_seat.sh
