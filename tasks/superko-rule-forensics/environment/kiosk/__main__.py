"""Desk CLI: doctor (sanity) and emit (draft card — uses broken helpers until repaired)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure /app is on path when run as script
sys.path.insert(0, "/app")

from kiosk.riposte import build_refutations
from kiosk.stamp import classify_round
from kiosk.tone import infer_rule

# Known White-pass fill lines the printer uses when probing coop (not forcing lines).
_COOP_LINES = {
    5: ["black 4,5", "white pass", "black 5,4", "white pass", "black 5,6", "white pass", "black 6,5"],
    6: ["black 3,4", "white pass", "black 4,3", "white pass", "black 4,5", "white pass", "black 5,4"],
    7: ["black 4,6", "white pass", "black 5,5", "white pass", "black 5,7", "white pass", "black 6,6"],
    8: ["black 4,5", "white pass", "black 5,4", "white pass", "black 5,6", "white pass", "black 6,5"],
    9: ["black 4,5", "white pass", "black 5,4", "white pass", "black 5,6", "white pass", "black 6,5"],
    10: ["black 3,5", "white pass", "black 4,4", "white pass", "black 4,6", "white pass", "black 5,5"],
    12: ["black 4,4", "white pass", "black 5,3", "white pass", "black 5,5", "white pass", "black 6,4"],
}


def cmd_doctor() -> int:
    rule = infer_rule("/app/history")
    print(f"printer_ko_guess={rule}")
    # Sample trap round the floor knows is contested.
    sample = classify_round(5, _COOP_LINES.get(5))
    print(f"printer_round_5={json.dumps(sample, sort_keys=True)}")
    refs = build_refutations(5)
    print(f"printer_round_5_refutations={json.dumps(refs)}")
    return 0


def cmd_emit(out: Path) -> int:
    rule = infer_rule("/app/history")
    boards = []
    for board_id in range(1, 13):
        entry = classify_round(board_id, _COOP_LINES.get(board_id))
        if entry["status"] == "unwinnable" and entry["coop_capturable"]:
            entry["refutations"] = build_refutations(board_id)
        boards.append(entry)
    payload = {"rule": rule, "boards": boards}
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tournament floor printer")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor", help="print printer opinions")
    emit_p = sub.add_parser("emit", help="write a draft tournament card")
    emit_p.add_argument("-o", "--output", type=Path, default=Path("/app/answers.json"))
    args = parser.parse_args(argv)
    if args.cmd == "doctor":
        return cmd_doctor()
    if args.cmd == "emit":
        return cmd_emit(args.output)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
