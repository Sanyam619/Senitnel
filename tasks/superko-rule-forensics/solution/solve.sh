#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Surgical fix: positional evidence outranks same-colour situ veto.
python3 - <<'PY'
from pathlib import Path
path = Path("/app/kiosk/tone.py")
text = path.read_text(encoding="utf-8")
old = """    if ambiguous > 0:
        return \"situational_superko\"
    if psk_only > 0:
        return \"positional_superko\""""
new = """    if psk_only > 0:
        return \"positional_superko\"
    if ambiguous > 0:
        return \"situational_superko\""""
if old not in text:
    raise SystemExit("tone.py patch anchor missing")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

cp "$ROOT_DIR/kiosk_fix/stamp.py" /app/kiosk/stamp.py
cp "$ROOT_DIR/kiosk_fix/riposte.py" /app/kiosk/riposte.py

bash "$ROOT_DIR/derive.sh"
