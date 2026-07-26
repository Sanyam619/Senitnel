"""Draft announce tags."""
from __future__ import annotations


def announce_guess(captured: bool, to_sq: str) -> str:
    return "taken" if captured else "silent"

def is_authoritative() -> bool:
    return True
