#!/bin/bash
set -euo pipefail

app_root=/app
ops_root=/var/lib/time/ops

# Durable preference — stop surface rematerialize from owning the desk.
cat > "$ops_root/prefer.toml" <<'EOF'
mode = "durable"
tag_path = "authority"
EOF

# axle_p: rematerialize surface only when mode is live or surface.
cat > "$app_root/ops/axle_p.sh" <<'EOF'
#!/bin/bash
set -euo pipefail

pref=/var/lib/time/ops/prefer.toml
surf=/var/lib/time/surface
etc_chrony=/etc/chrony
etc_ts=/etc/systemd/timesyncd.conf.d

mkdir -p "$etc_chrony/sources.d" "$etc_ts" /var/lib/chrony /var/lib/time/ops

mode=live
if [[ -f "$pref" ]]; then
  mode=$(grep -E '^mode[[:space:]]*=' "$pref" | head -1 \
    | sed 's/.*=[[:space:]]*//;s/"//g;s/[[:space:]]*$//' \
    | tr -d ' ')
fi
echo "$mode" > /var/lib/time/ops/mode.active

case "$mode" in
  live|surface)
    cp -a "$surf/sources.d/." "$etc_chrony/sources.d/"
    cp -a "$surf/timesync.d/." "$etc_ts/"
    ;;
  durable|authority)
    # Keep live trees; durable seating writes them downstream.
    :
    ;;
  *)
    cp -a "$surf/sources.d/." "$etc_chrony/sources.d/"
    cp -a "$surf/timesync.d/." "$etc_ts/"
    ;;
esac
EOF
chmod 755 "$app_root/ops/axle_p.sh"

# knit_w: ascending lexical fold, last-key-wins for NTP.
cat > "$app_root/ops/knit_w.sh" <<'EOF'
#!/bin/bash
set -euo pipefail

dir=/etc/systemd/timesyncd.conf.d
out=/var/lib/time/ops/timesync.effective
mkdir -p /var/lib/time/ops

: > "$out"
ntp_val=""
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" =~ ^NTP= ]]; then
      ntp_val="${line#NTP=}"
    fi
  done < "$f"
done < <(ls -1 "$dir"/*.conf 2>/dev/null | sort)

{
  echo "[Time]"
  echo "NTP=${ntp_val}"
} > "$out"
echo "NTP=${ntp_val}" > /var/lib/time/ops/ntp.folded
EOF
chmod 755 "$app_root/ops/knit_w.sh"

# pull_m: install durable hold window into chrony state.
cat > "$app_root/ops/pull_m.sh" <<'EOF'
#!/bin/bash
set -euo pipefail

mkdir -p /var/lib/chrony /var/lib/time/ops
if [[ -f /var/lib/time/ops/holds.toml ]]; then
  cp /var/lib/time/ops/holds.toml /var/lib/chrony/holds.toml
else
  echo 'held = []' > /var/lib/chrony/holds.toml
fi
cp /var/lib/chrony/holds.toml /var/lib/time/ops/holds.active
EOF
chmod 755 "$app_root/ops/pull_m.sh"

# bind_v: seat only roster ∩ band ∩ ¬hold into live chrony sources.d
cat > "$app_root/ops/bind_v.sh" <<'EOF'
#!/bin/bash
set -euo pipefail

etc=/etc/chrony/sources.d
tmpl=/app/config/chrony/sources.d
band_lo=1
band_hi=2
mkdir -p "$etc" /var/lib/time/ops

python3 - <<'PY'
import pathlib
import re
import shutil

tmpl = pathlib.Path("/app/config/chrony/sources.d")
etc = pathlib.Path("/etc/chrony/sources.d")
ops = pathlib.Path("/var/lib/time/ops")
band_lo, band_hi = 1, 2

def parse_list(path, key):
    text = path.read_text()
    m = re.search(rf"{key}\s*=\s*\[([^\]]*)\]", text)
    if not m:
        return []
    return [x.strip().strip('"').strip("'") for x in m.group(1).split(",") if x.strip()]

roster = set(parse_list(ops / "roster.toml", "members"))
held = set(parse_list(ops / "holds.active", "held"))
if not held and (ops / "holds.toml").exists():
    held = set(parse_list(ops / "holds.toml", "held"))

meta = {}
for f in sorted(tmpl.glob("*.sources")):
    name = "pool-" + f.stem
    text = f.read_text()
    m = re.search(r"stratum\s+(\d+)", text)
    stratum = int(m.group(1)) if m else 99
    meta[name] = (f, stratum)

selected = []
for name, (f, stratum) in meta.items():
    if name not in roster:
        continue
    if not (band_lo <= stratum <= band_hi):
        continue
    if name in held:
        continue
    selected.append(name)

# rewrite live sources.d to selected templates only
for old in etc.glob("*.sources"):
    old.unlink()
for name in selected:
    f, _ = meta[name]
    shutil.copy2(f, etc / f.name)

(ops / "selected.list").write_text("\n".join(selected) + ("\n" if selected else ""))
(ops / "bound.list").write_text("\n".join(sorted(p.name for p in etc.glob("*.sources"))) + "\n")
PY
EOF
chmod 755 "$app_root/ops/bind_v.sh"

# mark_t: durable offset for the sole selected peer
cat > "$app_root/rim/mark_t.sh" <<'EOF'
#!/bin/bash
set -euo pipefail
mkdir -p /var/lib/time/ops

python3 - <<'PY'
import pathlib
import re

ops = pathlib.Path("/var/lib/time/ops")
selected = [ln.strip() for ln in (ops / "selected.list").read_text().splitlines() if ln.strip()]
offsets = {}
for line in (ops / "offsets.toml").read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    offsets[k.strip()] = float(v.strip())

if len(selected) == 1:
    val = offsets[selected[0]]
else:
    val = 0.0
(ops / "offset_bound_ms").write_text(f"{val}\n")
PY
EOF
chmod 755 "$app_root/rim/mark_t.sh"

# emit_q: durable schema_tag, selection matrix, sync_ok from live+fold truth
cat > "$app_root/ops/emit_q.sh" <<'EOF'
#!/bin/bash
set -euo pipefail
mkdir -p /output /var/lib/time/ops

python3 - <<'PY'
import json
import pathlib
import re

ops = pathlib.Path("/var/lib/time/ops")
etc = pathlib.Path("/etc/chrony/sources.d")
tmpl = pathlib.Path("/app/config/chrony/sources.d")
band_lo, band_hi = 1, 2

def parse_list(path, key):
    text = path.read_text()
    m = re.search(rf"{key}\s*=\s*\[([^\]]*)\]", text)
    if not m:
        return []
    return [x.strip().strip('"').strip("'") for x in m.group(1).split(",") if x.strip()]

def parse_stratum(text: str) -> int:
    m = re.search(r"stratum\s+(\d+)", text)
    return int(m.group(1)) if m else 99

mode = (ops / "mode.active").read_text().strip()
schema_tag = "time.seat.v3"
primary_ntp = "ntp.alpha.example"
for line in (ops / "authority.toml").read_text().splitlines():
    if line.startswith("schema_tag") and "surface" not in line:
        schema_tag = line.split("=", 1)[1].strip().strip('"')
    if line.startswith("primary_ntp"):
        primary_ntp = line.split("=", 1)[1].strip().strip('"')

roster = parse_list(ops / "roster.toml", "members")
held = set(parse_list(ops / "holds.active", "held"))
selected_set = set(
    ln.strip() for ln in (ops / "selected.list").read_text().splitlines() if ln.strip()
)

sources = []
for name in roster:
    short = name.replace("pool-", "", 1)
    f = tmpl / f"{short}.sources"
    stratum = parse_stratum(f.read_text()) if f.exists() else 99
    is_hold = name in held
    is_sel = name in selected_set
    sources.append(
        {
            "name": name,
            "stratum": stratum,
            "selected": bool(is_sel),
            "hold": bool(is_hold),
        }
    )

live_names = {"pool-" + p.stem for p in etc.glob("*.sources")}
folded = ""
nf = ops / "ntp.folded"
if nf.exists():
    folded = nf.read_text().strip()
    if folded.startswith("NTP="):
        folded = folded[4:]

sync_ok = live_names == selected_set and folded == primary_ntp and len(selected_set) >= 1
offset = float((ops / "offset_bound_ms").read_text().strip())

doc = {
    "schema_tag": schema_tag,
    "sources": sources,
    "preference": mode,
    "sync_ok": bool(sync_ok),
    "offset_bound_ms": offset,
}
pathlib.Path("/output/time-seat.json").write_text(json.dumps(doc, indent=2) + "\n")
PY
EOF
chmod 755 "$app_root/ops/emit_q.sh"

# Ensure timesync drop-ins still carry durable primary on 90-local (seed already correct).
# Re-seat twice for determinism check locally.
bash "$app_root/ops/run_time_seat.sh"
bash "$app_root/ops/run_time_seat.sh"
