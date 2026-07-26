"""Mixed-slice candidate pool composition."""

from __future__ import annotations


def weave_m(marks, lots, _retired: set[str]):
    from lib.common import fold_all

    if not marks:
        return []
    return [fold_all(lots, "c"), fold_all(lots, "d")]
