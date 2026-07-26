"""Correct trap reply policy."""
from __future__ import annotations


def skip_refutations(status: str, coop: bool) -> bool:
    return False

def is_authoritative() -> bool:
    return False
