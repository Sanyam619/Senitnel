"""Ko family guess from match books."""

from __future__ import annotations

import re
from pathlib import Path

_PLY_REF = re.compile(r"ply_(\d+)")


def infer_rule(history_dir: str | Path) -> str:
    history = Path(history_dir)
    psk_only = 0
    ambiguous = 0
    for log in sorted(history.glob("game_*.log")):
        ply_colour: dict[str, str] = {}
        lines = log.read_text(encoding="utf-8").splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            ply, colour, _move, verdict = parts[0], parts[1], parts[2], parts[3]
            if verdict == "accepted":
                ply_colour[ply] = colour
                ply_colour[ply.lstrip("0") or "0"] = colour
        for line in lines:
            if "rejected" not in line or "superko:recreates_board_from_ply_" not in line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            rej = parts[1]
            m = _PLY_REF.search(line)
            if not m:
                continue
            ref = m.group(1)
            ref_colour = ply_colour.get(ref) or ply_colour.get(ref.lstrip("0") or "0")
            if not ref_colour:
                continue
            # Cross-colour recreations are positional-only; same-colour stay ambiguous.
            if rej != ref_colour:
                psk_only += 1
            else:
                ambiguous += 1
    if psk_only > 0:
        return "positional_superko"
    if ambiguous > 0:
        return "situational_superko"
    return "natural_situational_superko"
