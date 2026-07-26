"""Opaque helper: classify each round by searching force/coop outcomes."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from board_hunt.engine import (
    coop_capture,
    force_capture,
    load_sheet,
    threat_tries,
)


def _judge_cmd() -> list[str]:
    app = os.environ.get("APP_ROOT", "/app")
    return ["java", "-jar", f"{app}/bin/judge.jar"]


def _tag_line(board_id: int, pairs: list[tuple[str, str]], dialect: str) -> list[str]:
    """Tag announces using the dialect recovered from match logs."""
    app = os.environ.get("APP_ROOT", "/app")
    board = f"{app}/puzzles/board_{board_id:02d}.txt"
    segs: list[str] = []
    for color, uci in pairs:
        if uci == "pass":
            segs.append(f"{color} pass|silent")
            continue
        candidates: list[str] = ["silent", "check", "mate"]
        if len(uci) >= 4:
            sq = uci[2:4]
            if dialect == "square":
                candidates.extend(
                    [f"taken:{sq}", f"taken:{sq}+check", f"taken:{sq}+mate"]
                )
            else:
                candidates.extend(["taken", "taken+check", "taken+mate"])
        ok = False
        for ann in candidates:
            trial = segs + [f"{color} {uci}|{ann}"]
            proc = subprocess.run(
                [*_judge_cmd(), "validate", "--board", board, "--moves", ";".join(trial)],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if proc.returncode != 0 or not proc.stdout:
                continue
            data = json.loads(proc.stdout)
            if data.get("all_legal"):
                segs = trial
                ok = True
                break
        if not ok:
            raise RuntimeError(f"tag fail {color} {uci} dialect={dialect} after {segs}")
    proc = subprocess.run(
        [*_judge_cmd(), "validate", "--board", board, "--moves", ";".join(segs)],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    data = json.loads(proc.stdout)
    if not (data.get("all_legal") and (data.get("target_captured") or data.get("target_empty"))):
        raise RuntimeError(f"win pv rejected for {board_id}: {data}")
    return segs


def op_b(a: int, b: str) -> dict:
    board_id = int(a)
    dialect = b if b in ("square", "bare") else "square"
    app = Path(os.environ.get("APP_ROOT", "/app"))
    sheet = app / "puzzles" / f"board_{board_id:02d}.txt"
    sq, side, mark, _target = load_sheet(sheet)

    forced = force_capture(sq, side, mark, max_black=5)
    coop = coop_capture(sq, side, mark, max_black=8)

    if forced is not None:
        black_stones = sum(1 for c, u in forced if c == "black" and u != "pass")
        white_plies = sum(1 for c, _u in forced if c == "white")
        white_stones = sum(1 for c, u in forced if c == "white" and u != "pass")
        if black_stones < 3 or white_plies < 2 or white_stones < 1:
            raise RuntimeError(
                f"board {board_id}: force line too short "
                f"(black={black_stones} white_plies={white_plies} white_stones={white_stones})"
            )
        return {
            "board_id": board_id,
            "status": "win",
            "coop_capturable": True,
            "sequence": _tag_line(board_id, forced, dialect),
        }

    if coop is None:
        return {
            "board_id": board_id,
            "status": "unwinnable",
            "coop_capturable": False,
        }

    # Trap: coop yes, force no — refutations filled by op_c from live threats.
    threats = threat_tries(sq, mark)
    return {
        "board_id": board_id,
        "status": "unwinnable",
        "coop_capturable": True,
        "refutations": None,
        "_threats": threats,
    }
