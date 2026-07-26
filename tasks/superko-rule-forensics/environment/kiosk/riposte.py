from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _starting_libs(board_id: int) -> list[tuple[int, int]]:
    text = Path(f"/app/puzzles/board_{board_id:02d}.txt").read_text()
    target = None
    rows: list[str] = []
    mode = False
    for line in text.splitlines():
        if line.startswith("target:"):
            r_s, c_s = line.split(":", 1)[1].strip().split(",")
            target = (int(r_s), int(c_s))
        if mode and line.strip():
            rows.append(line.strip())
            if len(rows) == 9:
                break
        if line.strip() == "board:":
            mode = True
    assert target and len(rows) == 9
    tr, tc = target
    color = rows[tr - 1][tc - 1]
    seen = {(tr, tc)}
    stack = [(tr, tc)]
    libs: set[tuple[int, int]] = set()
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if not (1 <= nr <= 9 and 1 <= nc <= 9) or (nr, nc) in seen:
                continue
            ch = rows[nr - 1][nc - 1]
            if ch == color:
                seen.add((nr, nc))
                stack.append((nr, nc))
            elif ch == ".":
                libs.add((nr, nc))
    return sorted(libs)


def _jar_ok(board_id: int, moves: list[str]) -> tuple[bool, bool]:
    board = Path(f"/app/puzzles/board_{board_id:02d}.txt")
    proc = subprocess.run(
        [
            "java",
            "-jar",
            "/app/bin/judge.jar",
            "validate",
            "--board",
            str(board),
            "--moves",
            ";".join(moves),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return False, False
    data = json.loads(proc.stdout)
    return bool(data.get("all_legal")), bool(data.get("target_empty"))


def build_refutations(board_id: int) -> list[dict]:
    out: list[dict] = []
    for r, c in _starting_libs(board_id):
        after = f"{r},{c}"
        legal, empty = _jar_ok(board_id, [f"black {after}", "white pass"])
        if legal and not empty:
            out.append({"after_black": after, "white": "pass"})
            continue
        out.append({"after_black": after, "white": "pass"})
    return out
