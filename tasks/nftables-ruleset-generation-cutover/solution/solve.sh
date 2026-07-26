#!/bin/bash
set -euo pipefail

# Site-standard live 90-local (abort package stays forensic).
cat >/etc/nftables.d/90-local.nft <<'EOF'
# site-standard local slot — no abort overlay
EOF

target=$(tr -d '[:space:]' </var/lib/nft/state/gen.target)
cat >/var/lib/nft/state/cutover.ok <<EOF
gen=${target}
mode=seal
EOF

cat >/app/ops/helm_w.sh <<'EOF'
#!/bin/bash
set -euo pipefail

ABORT_D="/var/lib/nft/ops/abort.d"
LIVE_D="/etc/nftables.d"
STATE="/var/lib/nft/state"
RECEIPT="$STATE/cutover.ok"
TARGET=$(tr -d '[:space:]' <"$STATE/gen.target")

mkdir -p "$LIVE_D" "$STATE"

skip=0
if [[ -f "$RECEIPT" ]]; then
  got_gen=""
  got_mode=""
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" ]] && continue
    case "$line" in
      gen=*) got_gen="${line#gen=}" ;;
      mode=*) got_mode="${line#mode=}" ;;
    esac
  done <"$RECEIPT"
  if [[ "$got_gen" == "$TARGET" && "$got_mode" == "seal" ]]; then
    skip=1
  fi
fi

if [[ "$skip" -eq 0 ]]; then
  if [[ -f "$ABORT_D/90-local.nft" ]]; then
    cp -f "$ABORT_D/90-local.nft" "$LIVE_D/90-local.nft"
  fi
fi
EOF
chmod +x /app/ops/helm_w.sh

cat >/app/rim/fold_k.sh <<'EOF'
#!/bin/bash
set -euo pipefail

SRC_D="/etc/nftables.d"
OUT="/var/lib/nft/ops/fold.nft"
FLOOR_D="/var/lib/nft/floors"
JOURNAL="/var/lib/nft/ops/journal.jsonl"
STATE="/var/lib/nft/state"
TARGET=$(tr -d '[:space:]' <"$STATE/gen.target")
MAP="$STATE/frag_map.tsv"

mkdir -p "$(dirname "$OUT")"

python3 - "$SRC_D" "$OUT" "$FLOOR_D" "$JOURNAL" "$TARGET" "$MAP" <<'PY'
import json
import sys
from pathlib import Path

src_d, out, floor_d, journal, target_s, map_path = sys.argv[1:]
src_d = Path(src_d)
out = Path(out)
floor_d = Path(floor_d)
target = int(target_s)

tips = {}
for line in Path(journal).read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    row = json.loads(line)
    if row.get("kind") == "cutover" and int(row.get("gen", -1)) == target and row.get("mode") == "seal":
        tips = {k: int(v) for k, v in row.get("tips", {}).items()}

frag_to_table = {}
for line in Path(map_path).read_text().splitlines():
    parts = line.split()
    if len(parts) >= 2:
        frag_to_table[parts[0]] = parts[1]

chunks = []
for f in sorted(src_d.glob("*.nft")):
    body = f.read_text()
    if "abort_lab" in body:
        continue
    table = frag_to_table.get(f.name)
    if table is not None:
        tip = int(tips.get(table, 0))
        floor_p = floor_d / f"{table}.floor"
        floor = int(floor_p.read_text().strip()) if floor_p.exists() else 0
        if tip < floor:
            continue
    chunks.append(body.rstrip() + "\n")

out.write_text("\n".join(chunks) if chunks else "")
state = Path("/var/lib/nft/state")
(state / "gen.live").write_text(f"{target}\n")
for name, tip in tips.items():
    (state / f"tip_{name}.gen").write_text(f"{tip}\n")
PY
EOF
chmod +x /app/rim/fold_k.sh

cat >/app/ops/pin_m.sh <<'EOF'
#!/bin/bash
set -euo pipefail

FOLD="/var/lib/nft/ops/fold.nft"
PREF="/var/lib/nft/ops/prefer.conf"

python3 - "$FOLD" "$PREF" <<'PY'
import re
import sys
from pathlib import Path

fold, pref_path = map(Path, sys.argv[1:])
pref = {}
for line in pref_path.read_text().splitlines():
    line = line.split("#", 1)[0].strip()
    if not line or "=" not in line:
        continue
    k, v = line.split("=", 1)
    pref[k.strip()] = v.strip()

text = fold.read_text()
cur_family = None
cur_table = None
cur_chain = None
out_lines = []
for raw in text.splitlines():
    line = raw
    s = line.split("#", 1)[0].strip()
    m = re.match(r"^table\s+(\S+)\s+(\S+)", s)
    if m:
        cur_family, cur_table = m.group(1), m.group(2)
        cur_chain = None
        out_lines.append(raw)
        continue
    m = re.match(r"^chain\s+(\S+)", s)
    if m:
        cur_chain = m.group(1)
        out_lines.append(raw)
        continue
    m = re.match(
        r"^(type\s+\S+\s+hook\s+\S+\s+priority\s+-?\d+\s*;\s*policy\s+)(\S+)(\s*;.*)$",
        s,
    )
    if m and cur_family and cur_table and cur_chain:
        key = f"{cur_family}/{cur_table}/{cur_chain}"
        if key in pref:
            indent = raw[: len(raw) - len(raw.lstrip())]
            line = f"{indent}{m.group(1)}{pref[key]}{m.group(3)}"
            out_lines.append(line)
            continue
    out_lines.append(raw)

fold.write_text("\n".join(out_lines) + ("\n" if out_lines else ""))
PY
EOF
chmod +x /app/ops/pin_m.sh

cat >/app/bag/swap_r.sh <<'EOF'
#!/bin/bash
set -euo pipefail

FOLD="/var/lib/nft/ops/fold.nft"
rm -f /var/lib/nft/state/append.flag
/usr/local/bin/nft flush ruleset
/usr/local/bin/nft -f "$FOLD"
EOF
chmod +x /app/bag/swap_r.sh

cat >/app/ops/echo_t.sh <<'EOF'
#!/bin/bash
set -euo pipefail

OUT="/var/lib/nft/ops/applied.nft"
mkdir -p "$(dirname "$OUT")"
/usr/local/bin/nft list ruleset >"$OUT"
EOF
chmod +x /app/ops/echo_t.sh

cat >/app/deck/card_w.sh <<'EOF'
#!/bin/bash
set -euo pipefail
exec /app/bin/seatctl
EOF
chmod +x /app/deck/card_w.sh

/app/ops/run_nft_seat.sh
/app/ops/run_nft_seat.sh
