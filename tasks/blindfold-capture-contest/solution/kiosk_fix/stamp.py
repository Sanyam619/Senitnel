"""Correct overnight status stamps."""
from __future__ import annotations


def stamp_from_whisper(whisper: str) -> str:
    if "looks_fillable_if_defender_passes" in (whisper or ""):
        return "unwinnable"
    return "unwinnable"

def is_authoritative() -> bool:
    return False
