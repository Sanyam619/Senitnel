#!/bin/bash
# Restore bevel seating from desk seeds unless evaluation selection and
# tip binding are publishable together. Two gate parsers stay structurally
# dissimilar so a single greppable mode line is not enough.
set -euo pipefail

APP="${BEVEL_APP:-/app}"
PREF="$APP/calib/trial_pref.toml"
BIND="$APP/calib/tip_bind.accept"
JOURNAL="$APP/data/feature_registry/tip_journal.jsonl"
RETIRED="$APP/data/feature_registry/retired_tips.jsonl"
SEAT="$APP/bevel"
SEEDS="$APP/bevel/seeds"

selection_ok() {
  python3 - "$PREF" <<'PY'
import sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8") if Path(sys.argv[1]).is_file() else ""
for raw in text.splitlines():
    line = raw.strip()
    if line.startswith("#") or not line:
        continue
    if "selection" in line:
        after = line.split("selection", 1)[1].lstrip()
        if after.startswith("="):
            val = after[1:].strip().strip('"')
            raise SystemExit(0 if val == "serving" else 1)
raise SystemExit(1)
PY
}

resolved_tip() {
  python3 - "$JOURNAL" "$RETIRED" <<'PY'
import sys
from pathlib import Path

def tip_field(line: str):
    key = '"tip"'
    i = line.find(key)
    if i < 0:
        return None
    rest = line[i + len(key):].lstrip().lstrip(":").lstrip()
    if not rest.startswith('"'):
        return None
    rest = rest[1:]
    end = rest.find('"')
    return rest[:end] if end >= 0 else None

def state_field(line: str):
    key = '"state"'
    i = line.find(key)
    if i < 0:
        return None
    rest = line[i + len(key):].lstrip().lstrip(":").lstrip()
    if not rest.startswith('"'):
        return None
    rest = rest[1:]
    end = rest.find('"')
    return rest[:end] if end >= 0 else None

def idx_field(line: str) -> int:
    key = '"idx"'
    i = line.find(key)
    if i < 0:
        return 0
    rest = line[i + len(key):].lstrip().lstrip(":").lstrip()
    num = ""
    for c in rest:
        if c.isdigit():
            num += c
        elif num:
            break
    return int(num) if num else 0

journal, retired = Path(sys.argv[1]), Path(sys.argv[2])
banned = set()
if retired.is_file():
    for line in retired.read_text(encoding="utf-8").splitlines():
        t = tip_field(line.strip())
        if t:
            banned.add(t)
best_idx, best_tip = 0, ""
if journal.is_file():
    for line in journal.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if state_field(line) != "durable":
            continue
        tip = tip_field(line)
        if not tip or tip in banned:
            continue
        idx = idx_field(line)
        if idx >= best_idx:
            best_idx, best_tip = idx, tip
print(best_tip)
PY
}

bind_ok() {
  local want="$1"
  local have
  have="$(tr -d ' \t\r\n' <"$BIND" 2>/dev/null || true)"
  [[ -n "$want" && "$have" == "$want" ]]
}

restore_pair() {
  local a_seed="$1" a_dest="$2" b_seed="$3" b_dest="$4"
  for pair in "$a_seed:$a_dest" "$b_seed:$b_dest"; do
    local src="${pair%%:*}"
    local dst="${pair##*:}"
    if [[ -f "$src" ]]; then
      cp -f "$src" "$dst"
    fi
  done
}

if ! selection_ok || ! bind_ok "$(resolved_tip)"; then
  restore_pair \
    "$SEEDS/knot.py.in" "$SEAT/knot.py" \
    "$SEEDS/facet.py.in" "$SEAT/facet.py"
fi

python3 - "$PREF" "$BIND" "$JOURNAL" "$RETIRED" "$SEEDS" "$SEAT" <<'PY'
import sys
from pathlib import Path

pref, bind, journal, retired, seeds, seat = map(Path, sys.argv[1:])

def selection(path: Path) -> str:
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pos = line.find("selection")
        if pos < 0:
            continue
        after = line[pos + len("selection"):].lstrip()
        if after.startswith("="):
            return after[1:].strip().strip('"')
    return ""

def receipt(path: Path) -> str:
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    return lines[0].strip() if lines else ""

def extract_quoted(line: str, key: str):
    needle = f'"{key}"'
    i = line.find(needle)
    if i < 0:
        return None
    rest = line[i + len(needle):].lstrip()
    if not rest.startswith(":"):
        return None
    rest = rest[1:].lstrip()
    if not rest.startswith('"'):
        return None
    rest = rest[1:]
    end = rest.find('"')
    return rest[:end] if end >= 0 else None

def extract_idx(line: str) -> int:
    q = extract_quoted(line, "idx")
    if q and q.isdigit():
        return int(q)
    key = '"idx"'
    i = line.find(key)
    if i < 0:
        return 0
    rest = line[i + len(key):].lstrip().lstrip(":").lstrip()
    num = ""
    for c in rest:
        if c.isdigit():
            num += c
        elif num:
            break
    return int(num) if num else 0

banned = set()
if retired.is_file():
    for line in retired.read_text(encoding="utf-8").splitlines():
        t = extract_quoted(line, "tip")
        if t:
            banned.add(t)
best = (0, "")
if journal.is_file():
    for line in journal.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if extract_quoted(line, "state") != "durable":
            continue
        tip = extract_quoted(line, "tip")
        if not tip or tip in banned:
            continue
        idx = extract_idx(line)
        if idx >= best[0]:
            best = (idx, tip)

serving = selection(pref) == "serving"
bound = bool(best[1]) and receipt(bind) == best[1]
if not (serving and bound):
    for name in ("lens.py", "weave.py"):
        src = seeds / f"{name}.in"
        dst = seat / name
        if src.is_file():
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
PY
