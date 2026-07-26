"""Draft trap reply policy."""
from __future__ import annotations


def skip_refutations(status: str, coop: bool) -> bool:
    return status == "unwinnable" and bool(coop)

def is_authoritative() -> bool:
    return True
