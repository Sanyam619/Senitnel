"""Board hunt: rate one round and write down the play that backs the verdict."""

from __future__ import annotations

from board_hunt import engine


def op_b(sheet, dialect: str = "+corner") -> dict:
    board_id, black, white, mark_index = sheet
    mark = 1 << mark_index

    if engine.forced(black, white, mark, engine.STONES):
        line = engine.forcing_line(black, white, mark)
        if line is None:
            raise RuntimeError(f"round {board_id} forced without a line")
        return {
            "board_id": board_id,
            "status": "win",
            "line": [_dress(step, dialect) for step in line],
            "refutations": [],
        }

    if engine.friendly(black, white, mark, engine.STONES):
        line = engine.friendly_line(black, white, mark)
        if line is None:
            raise RuntimeError(f"round {board_id} friendly without a line")
        rows = []
        for threat in engine.threats(black, white, mark):
            reply = engine.answer_to(black, white, mark, threat)
            if reply is None:
                raise RuntimeError(f"round {board_id} threat {engine.nm(threat)} unanswered")
            rows.append({"threat": engine.nm(threat), "reply": reply})
        return {
            "board_id": board_id,
            "status": "trap",
            "line": [_dress(step, dialect) for step in line],
            "refutations": rows,
        }

    return {"board_id": board_id, "status": "fort", "line": [], "refutations": []}


def _dress(step: str, dialect: str) -> str:
    """Re-spell the corner announce in the dialect the history logs show."""
    if "+corner" in step and dialect != "+corner":
        return step.replace("+corner", dialect)
    return step
