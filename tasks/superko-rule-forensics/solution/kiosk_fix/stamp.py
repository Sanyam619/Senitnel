from __future__ import annotations

import json
import subprocess
from pathlib import Path


def sensei_line(board_id: int) -> str:
    proc = subprocess.run(
        ["/app/tools/sensei_hint.sh"],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    key = f"board_{board_id:02d}"
    for line in proc.stdout.splitlines():
        if line.startswith(key):
            return line
    return ""


def jar_fill_under_white_pass(board_id: int, moves: list[str]) -> bool:
    board = Path(f"/app/puzzles/board_{board_id:02d}.txt")
    cmd = [
        "java",
        "-jar",
        "/app/bin/judge.jar",
        "validate",
        "--board",
        str(board),
        "--moves",
        ";".join(moves),
    ]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, check=False, timeout=60,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return False
    data = json.loads(proc.stdout)
    return bool(data.get("all_legal") and data.get("target_empty"))


def classify_round(board_id: int, coop_fill_line: list[str] | None = None) -> dict:
    """Return status fields: status + coop_capturable (no sequences)."""
    whisper = sensei_line(board_id)
    looks_fillable = "looks_fillable_if_white_passes" in whisper
    coop = False
    if coop_fill_line:
        coop = jar_fill_under_white_pass(board_id, coop_fill_line)
    elif looks_fillable:
        coop = False

    if coop:
        return {"board_id": board_id, "status": "unwinnable", "coop_capturable": True}
    if looks_fillable:
        return {"board_id": board_id, "status": "unwinnable", "coop_capturable": True}
    return {"board_id": board_id, "status": "unwinnable", "coop_capturable": False}
