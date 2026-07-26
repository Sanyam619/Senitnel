"""Correct announce tags."""
from __future__ import annotations


def announce_guess(captured: bool, to_sq: str) -> str:
    if captured:
        return f"taken:{(to_sq or '').lower()}"
    return "silent"

def is_authoritative() -> bool:
    return False
