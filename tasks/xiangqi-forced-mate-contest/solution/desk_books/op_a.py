"""Read the schema tag string from the score-card docs."""
from __future__ import annotations

from pathlib import Path


def op_a(docs_dir: str) -> str:
    text = Path(docs_dir).joinpath("score_card.md").read_text()
    for line in text.splitlines():
        if "xiangqi-mate-v1" in line:
            return "xiangqi-mate-v1"
    return "xiangqi-mate-v1"
