#!/bin/bash
set -euo pipefail

app_root=/app
ops_root=/var/lib/multipath/ops

# Durable preference — stop surface rematerialize from owning the substrate.
cat > "$ops_root/prefer.toml" <<'EOF'
mode = "durable"
tag_path = "authority"
EOF

# weld_p: rematerialize the live substrate from durable truth under durable
# preference; only fall back to surface materials when not durable.
cat > "$app_root/ops/weld_p.sh" <<'EOF'
#!/bin/bash
set -euo pipefail

pref=/var/lib/multipath/ops/prefer.toml
truth=/app/data/sysfs
surf=/app/config/surface/candidates
cand=/var/lib/multipath/candidates

mkdir -p "$cand" /var/lib/multipath/ops

mode=surface
if [[ -f "$pref" ]]; then
  mode=$(grep -E '^mode[[:space:]]*=' "$pref" | head -1 \
    | sed 's/.*=[[:space:]]*//;s/"//g;s/[[:space:]]*$//' \
    | tr -d ' ')
fi
echo "$mode" > /var/lib/multipath/ops/mode.active

case "$mode" in
  durable|authority) src="$truth" ;;
  *) src="$surf" ;;
esac

rm -f "$cand"/*.json 2>/dev/null || true
for f in "$src"/*.json; do
  [[ -f "$f" ]] || continue
  cp "$f" "$cand/"
done
EOF
chmod 755 "$app_root/ops/weld_p.sh"

# stitch_r: fold conf.d drop-ins ascending, last layer wins per map.
cat > "$app_root/ops/stitch_r.sh" <<'EOF'
#!/bin/bash
set -euo pipefail

dir=/etc/multipath/conf.d
out=/var/lib/multipath/ops/group.map
mkdir -p /var/lib/multipath/ops

python3 - <<'PY'
import pathlib

d = pathlib.Path("/etc/multipath/conf.d")
weights = {}
for f in sorted(d.glob("*.conf")):
    for line in f.read_text().splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[0] == "weight":
            weights[parts[1]] = parts[2]
out = pathlib.Path("/var/lib/multipath/ops/group.map")
out.write_text(
    "".join(f"{k} {v}\n" for k, v in sorted(weights.items()))
)
PY
EOF
chmod 755 "$app_root/ops/stitch_r.sh"

# latch_m: install the durable hold window with its epochs.
cat > "$app_root/ops/latch_m.sh" <<'EOF'
#!/bin/bash
set -euo pipefail
mkdir -p /var/lib/multipath/ops

python3 - <<'PY'
import pathlib
import re

src = pathlib.Path("/var/lib/multipath/ops/holds.toml")
held = []
until = {}
if src.exists():
    text = src.read_text()
    m = re.search(r"held\s*=\s*\[([^\]]*)\]", text)
    if m:
        held = [x.strip().strip('"').strip("'") for x in m.group(1).split(",") if x.strip()]
    in_until = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("[until]"):
            in_until = True
            continue
        if s.startswith("[") and s != "[until]":
            in_until = False
            continue
        if in_until and "=" in s:
            k, v = s.split("=", 1)
            until[k.strip()] = int(v.strip())

lines = ['held = [' + ", ".join(f'"{h}"' for h in held) + ']']
for h in held:
    if h in until:
        lines.append(f"until_{h} = {until[h]}")
pathlib.Path("/var/lib/multipath/ops/holds.active").write_text("\n".join(lines) + "\n")
PY
EOF
chmod 755 "$app_root/ops/latch_m.sh"

# graft_k: seat the eligible AO path in the folded preferred group, above the
# generation floor, excluding held maps.
cat > "$app_root/ops/graft_k.sh" <<'EOF'
#!/bin/bash
set -euo pipefail
mkdir -p /var/lib/multipath

python3 - <<'PY'
import json
import pathlib
import re

ops = pathlib.Path("/var/lib/multipath/ops")
cand = pathlib.Path("/var/lib/multipath/candidates")

def parse_list(path, key):
    if not path.exists():
        return []
    m = re.search(rf"{key}\s*=\s*\[([^\]]*)\]", path.read_text())
    if not m:
        return []
    return [x.strip().strip('"').strip("'") for x in m.group(1).split(",") if x.strip()]

roster = parse_list(ops / "roster.toml", "members")
held = set(parse_list(ops / "holds.active", "held"))

floor = 0
for line in (ops / "authority.toml").read_text().splitlines():
    if line.startswith("min_generation"):
        floor = int(line.split("=", 1)[1].strip())

groups = {}
gm = ops / "group.map"
if gm.exists():
    for line in gm.read_text().splitlines():
        if line.strip():
            k, v = line.split()
            groups[k] = int(v)

by_alias = {}
for f in cand.glob("*.json"):
    d = json.loads(f.read_text())
    by_alias[d["alias"]] = d

rows = []
for alias in roster:
    if alias in held:
        continue
    d = by_alias.get(alias)
    if not d:
        continue
    pref = groups.get(alias)
    if pref is None:
        continue
    eligible = [
        p for p in d["paths"]
        if p["alua"] == "active/optimized"
        and p["generation"] >= floor
        and p["group"] == pref
    ]
    if not eligible:
        continue
    pick = sorted(eligible, key=lambda p: (-p["prio"], p["dev"]))[0]
    rows.append((d["wwid"], pick["dev"], pick["group"]))

rows.sort(key=lambda r: r[0])
pathlib.Path("/var/lib/multipath/bindings").write_text(
    "".join(f"{w} {dev} {g}\n" for w, dev, g in rows)
)
PY
EOF
chmod 755 "$app_root/ops/graft_k.sh"

# tally_t: resolve the seated path's priority and generation for each map.
cat > "$app_root/rim/tally_t.sh" <<'EOF'
#!/bin/bash
set -euo pipefail
mkdir -p /var/lib/multipath/ops

python3 - <<'PY'
import json
import pathlib

cand = pathlib.Path("/var/lib/multipath/candidates")
by_wwid = {}
for f in cand.glob("*.json"):
    d = json.loads(f.read_text())
    for p in d["paths"]:
        by_wwid[(d["wwid"], p["dev"])] = (p["prio"], p["generation"])

out = []
b = pathlib.Path("/var/lib/multipath/bindings")
if b.exists():
    for line in b.read_text().splitlines():
        if not line.strip():
            continue
        wwid, dev, _ = line.split()
        prio, gen = by_wwid.get((wwid, dev), (0, 0))
        out.append(f"{wwid} {prio} {gen}")
pathlib.Path("/var/lib/multipath/ops/prio.map").write_text(
    "".join(s + "\n" for s in out)
)
PY
EOF
chmod 755 "$app_root/rim/tally_t.sh"

# emit_z: assemble the report with durable schema_tag, seated devices, holds,
# and a path_ok recomputed independently from frozen truth.
cat > "$app_root/ops/emit_z.sh" <<'EOF'
#!/bin/bash
set -euo pipefail
mkdir -p /output /var/lib/multipath/ops

python3 - <<'PY'
import json
import pathlib
import re

ops = pathlib.Path("/var/lib/multipath/ops")
truth = pathlib.Path("/app/data/sysfs")

def parse_list(path, key):
    if not path.exists():
        return []
    m = re.search(rf"{key}\s*=\s*\[([^\]]*)\]", path.read_text())
    if not m:
        return []
    return [x.strip().strip('"').strip("'") for x in m.group(1).split(",") if x.strip()]

schema_tag = "alua.seat.v1"
for line in (ops / "authority.toml").read_text().splitlines():
    if line.startswith("schema_tag"):
        schema_tag = line.split("=", 1)[1].strip().strip('"')

floor = 0
for line in (ops / "authority.toml").read_text().splitlines():
    if line.startswith("min_generation"):
        floor = int(line.split("=", 1)[1].strip())

mode = (ops / "mode.active").read_text().strip()

roster = parse_list(ops / "roster.toml", "members")
held = parse_list(ops / "holds.active", "held")

# priority/generation for seated devices
prio = {}
pm = ops / "prio.map"
if pm.exists():
    for line in pm.read_text().splitlines():
        if line.strip():
            w, p, g = line.split()
            prio[w] = (int(p), int(g))

devices = []
bindings = pathlib.Path("/var/lib/multipath/bindings")
if bindings.exists():
    for line in bindings.read_text().splitlines():
        if not line.strip():
            continue
        wwid, dev, group = line.split()
        p, g = prio.get(wwid, (0, 0))
        devices.append(
            {
                "wwid": wwid,
                "active_path": dev,
                "group": int(group),
                "priority": p,
                "generation": g,
            }
        )
devices.sort(key=lambda r: r["wwid"])

# holds array with epochs, resolving wwid from frozen truth
truth_wwid = {}
for f in truth.glob("*.json"):
    d = json.loads(f.read_text())
    truth_wwid[d["alias"]] = d["wwid"]
holds_txt = (ops / "holds.active").read_text()
holds = []
for alias in held:
    m = re.search(rf"until_{alias}\s*=\s*(\d+)", holds_txt)
    until = int(m.group(1)) if m else 0
    holds.append({"wwid": truth_wwid.get(alias, alias), "until_epoch": until})
holds.sort(key=lambda r: r["wwid"])

# path_ok: recompute expected seating independently from frozen truth using a
# correct last-wins conf.d fold, then compare to the runtime bindings.
weights = {}
for f in sorted(pathlib.Path("/etc/multipath/conf.d").glob("*.conf")):
    for line in f.read_text().splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[0] == "weight":
            weights[parts[1]] = int(parts[2])

expected = {}
held_set = set(held)
for f in truth.glob("*.json"):
    d = json.loads(f.read_text())
    alias = d["alias"]
    if alias not in roster or alias in held_set:
        continue
    pref = weights.get(alias)
    if pref is None:
        continue
    elig = [
        p for p in d["paths"]
        if p["alua"] == "active/optimized"
        and p["generation"] >= floor
        and p["group"] == pref
    ]
    if not elig:
        continue
    pick = sorted(elig, key=lambda p: (-p["prio"], p["dev"]))[0]
    expected[d["wwid"]] = (pick["dev"], pick["group"])

live = {row["wwid"]: (row["active_path"], row["group"]) for row in devices}
non_held_roster = {a for a in roster if a not in held_set}
path_ok = (
    mode in ("durable", "authority")
    and live == expected
    and len(expected) == len(non_held_roster)
)

doc = {
    "schema_tag": schema_tag,
    "devices": devices,
    "holds": holds,
    "path_ok": bool(path_ok),
}
pathlib.Path("/output/alua-seat.json").write_text(json.dumps(doc, indent=2) + "\n")
PY
EOF
chmod 755 "$app_root/ops/emit_z.sh"

# Seat twice to confirm idempotence locally.
bash "$app_root/ops/run_alua_seat.sh"
bash "$app_root/ops/run_alua_seat.sh"
