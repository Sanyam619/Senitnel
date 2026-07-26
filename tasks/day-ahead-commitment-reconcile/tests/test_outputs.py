"""Verifier for day-ahead commitment answers — domain outcomes."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

CARD = Path("/data/out/answers.json")
JUDGE = Path("/opt/distro/lib/rowcheck.jar")
JUDGE_SHA = Path("/opt/distro/lib/rowcheck.jar.sha256")
PUZZLES = Path("/data/fixtures")
KIOSK = Path("/data/staging")
HISTORY = Path("/data/fixtures")
JUDGE_CMD = ["java", "-jar", str(JUDGE)]

FEASIBLE = {"R01", "R02", "R05", "R08", "R10", "R12"}
RESERVE_SHORT = {"R03", "R06", "R09"}
INFEASIBLE = {"R04", "R07", "R11"}
DEEP = {"R02", "R08", "R10", "R12"}


def _load_card():
    assert CARD.exists(), "missing answers card"
    return json.loads(CARD.read_text())


def _by_id(card):
    return {r["round_id"]: r for r in card["rounds"]}


def _board_by_rid():
    out = {}
    for path in sorted(PUZZLES.glob("board_*.txt")):
        for line in path.read_text().splitlines():
            if line.startswith("round_id:"):
                out[line.split(":", 1)[1].strip()] = path
                break
    return out


def _validate(board: Path, row: dict) -> dict:
    claim = {
        "status": row["status"],
        "cleared": row.get("cleared") or [],
        "smp": row.get("smp", 0),
        "reserve_binds": bool(row.get("reserve_binds", False)),
    }
    if row.get("refutation"):
        claim["refutation"] = row["refutation"]
    proc = subprocess.run(
        [*JUDGE_CMD, "validate", "--board", str(board), "--claim", json.dumps(claim)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(proc.stdout)


def _caps(board: Path) -> dict[str, int]:
    caps = {}
    for line in board.read_text().splitlines():
        if line.startswith("unit "):
            parts = line.split()
            caps[parts[1]] = int(parts[2])
    return caps


def test_k3_zircon():
    """Every round validates under the sealed row checker with a complete status lattice."""
    card = _load_card()
    assert card["version"] == 1
    assert len(card["rounds"]) == 12
    boards = _board_by_rid()
    by = _by_id(card)
    assert set(by) == FEASIBLE | RESERVE_SHORT | INFEASIBLE
    for rid, row in by.items():
        assert _validate(boards[rid], row)["ok"] is True
        if rid in FEASIBLE:
            assert row["status"] == "feasible_clear"
            assert row["cleared"]
            assert "refutation" not in row or row["refutation"] in (None, "")
        elif rid in RESERVE_SHORT:
            assert row["status"] == "reserve_short"
            assert row["reserve_binds"] is True
            assert row["refutation"] == "C_RES"
            assert row["cleared"], "reserve_short must report an energy line"
        else:
            assert row["status"] == "infeasible"
            assert row["reserve_binds"] is False
            assert row["cleared"] == []
            assert row["refutation"] == "C_CAP"


def test_m8_obsidian():
    """Row checker rejects staging trap claims and re-entry stays byte-identical when valid."""
    assert JUDGE.exists()
    digest = subprocess.run(
        ["sha256sum", str(JUDGE)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()[0]
    assert digest == JUDGE_SHA.read_text().strip()
    bad = {
        "status": "feasible_clear",
        "cleared": [
            {"unit_id": "A", "mw": 70, "offer_price": 10},
            {"unit_id": "B", "mw": 70, "offer_price": 20},
        ],
        "smp": 20,
        "reserve_binds": True,
    }
    trap = PUZZLES / "board_03.txt"
    proc = subprocess.run(
        [
            *JUDGE_CMD,
            "validate",
            "--board",
            str(trap),
            "--claim",
            json.dumps(bad),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0 or '"ok":false' in proc.stdout.replace(" ", "")
    before = CARD.read_bytes()
    card = json.loads(before)
    canonical = (json.dumps(card, sort_keys=True, separators=(",", ":")) + "\n").encode()
    assert before == canonical
    CARD.write_bytes(canonical)
    assert CARD.read_bytes() == before


def test_p2_garnet():
    """feasible_clear rounds are checker-legal and meet reserve with correct binds."""
    card = _by_id(_load_card())
    boards = _board_by_rid()
    for rid in FEASIBLE:
        row = card[rid]
        assert row["status"] == "feasible_clear"
        assert _validate(boards[rid], row)["ok"] is True
        caps = _caps(boards[rid])
        demand = None
        reserve = None
        for line in boards[rid].read_text().splitlines():
            if line.startswith("demand_mw:"):
                demand = int(line.split(":", 1)[1])
            if line.startswith("reserve_mw:"):
                reserve = int(line.split(":", 1)[1])
        cleared = {x["unit_id"]: x["mw"] for x in row["cleared"]}
        assert sum(cleared.values()) == demand
        room = sum(caps[u] - mw for u, mw in cleared.items())
        assert room >= reserve
        assert row["reserve_binds"] is (room == reserve)


def test_q7_topaz():
    """reserve_short: energy-legal cleared line, reserve fails, C_RES, binds true."""
    card = _by_id(_load_card())
    boards = _board_by_rid()
    for rid in RESERVE_SHORT:
        row = card[rid]
        assert row["status"] == "reserve_short"
        assert row["reserve_binds"] is True
        assert row["refutation"] == "C_RES"
        assert row["cleared"]
        caps = _caps(boards[rid])
        demand = reserve = None
        for line in boards[rid].read_text().splitlines():
            if line.startswith("demand_mw:"):
                demand = int(line.split(":", 1)[1])
            if line.startswith("reserve_mw:"):
                reserve = int(line.split(":", 1)[1])
        cleared = {x["unit_id"]: x["mw"] for x in row["cleared"]}
        assert sum(cleared.values()) == demand
        room = sum(caps[u] - mw for u, mw in cleared.items())
        assert room < reserve
        assert _validate(boards[rid], row)["ok"] is True


def test_r1_onyx():
    """infeasible rounds stay empty/unbound with C_CAP; energy claims fail the checker."""
    card = _by_id(_load_card())
    boards = _board_by_rid()
    for rid in INFEASIBLE:
        row = card[rid]
        assert row["status"] == "infeasible"
        assert row["reserve_binds"] is False
        assert row["cleared"] == []
        assert row["refutation"] == "C_CAP"
        assert _validate(boards[rid], row)["ok"] is True
        proc = subprocess.run(
            [
                *JUDGE_CMD,
                "validate",
                "--board",
                str(boards[rid]),
                "--claim",
                json.dumps(
                    {
                        "status": "reserve_short",
                        "cleared": [],
                        "smp": 0,
                        "reserve_binds": True,
                        "refutation": "C_RES",
                    }
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode != 0 or '"ok": true' not in proc.stdout.replace(" ", "")


def test_t6_amber():
    """Staging drafts stamp feasible_clear on trap boards the answers must not."""
    card = _by_id(_load_card())
    kiosk = "\n".join(path.read_text() for path in sorted(KIOSK.glob("draft_*.txt")))
    assert "feasible_clear" in kiosk
    boards = _board_by_rid()
    for rid in ("R03", "R04", "R06"):
        assert card[rid]["status"] != "feasible_clear"
        assert _validate(boards[rid], card[rid])["ok"] is True


def test_v4_jade():
    """Deep feasible SMPs match the house lowest-SMP / max-headroom line."""
    card = _by_id(_load_card())
    boards = _board_by_rid()
    notes = "\n".join(p.read_text() for p in sorted(HISTORY.glob("sample_*.txt")))
    for rid in DEEP:
        row = card[rid]
        assert row["status"] == "feasible_clear"
        m = None
        for line in notes.splitlines():
            if line.startswith(f"{rid} smp="):
                m = int(line.split("=", 1)[1].strip())
                break
        assert m is not None, f"missing history note for {rid}"
        assert row["smp"] == m
        offers = [item["offer_price"] for item in row["cleared"]]
        assert row["smp"] == max(offers)
        assert _validate(boards[rid], row)["ok"] is True


def test_w9_flint():
    """Deep feasible clears are not naive full-capacity dumps and need multi-unit mix."""
    card = _by_id(_load_card())
    boards = _board_by_rid()
    for rid in DEEP:
        row = card[rid]
        assert row["status"] == "feasible_clear"
        board = boards[rid]
        caps = _caps(board)
        cleared = {item["unit_id"]: item["mw"] for item in row["cleared"]}
        naive = set(cleared) == set(caps) and all(
            cleared[uid] == caps[uid] for uid in caps
        )
        assert not naive
        assert len(cleared) >= 3
        assert sum(cleared.values()) > 0
        assert _validate(board, row)["ok"] is True
